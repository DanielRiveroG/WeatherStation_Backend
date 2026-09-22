import logging
import os
import random
import sched
import sys
import threading
import time
from datetime import datetime
import serial
from serial.tools import list_ports
import numpy

from DatabaseOperations import *
from Models import *

# Set WEATHERSTATION_SIMULATE=1 to run without an Arduino attached: synthetic readings are generated
# instead of reading a real serial port, so the rest of the pipeline (parsing, buffering, DB writes, API)
# can be exercised end-to-end for local/frontend testing.
SIMULATE = os.getenv('WEATHERSTATION_SIMULATE', '').lower() in ('1', 'true', 'yes')
SIMULATED_READING_INTERVAL_SECONDS = 5

# Overrides auto-detection with a specific device path (e.g. /dev/ttyACM0, COM3) - useful for
# troubleshooting when the auto-detected port isn't the right one.
SERIAL_PORT_OVERRIDE = os.getenv('WEATHERSTATION_SERIAL_PORT')

LOG_LEVEL = os.getenv('WEATHERSTATION_LOG_LEVEL', 'INFO').upper()

# Vendor IDs seen on real Arduino boards and the common USB-serial chips their clones use.
ARDUINO_VENDOR_IDS = {0x2341, 0x1A86, 0x0403}

logger = logging.getLogger(__name__)

WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

rainList = []
windSpeedList = []
windDirectionList = []
humidityList = []
temperatureList = []
pressureList = []

maxTemperature = EdgeValue(None, None)
minTemperature = EdgeValue(None, None)
maxHumidity = EdgeValue(None, None)
minHumidity = EdgeValue(None, None)
maxPressure = EdgeValue(None, None)
minPressure = EdgeValue(None, None)
maxWindGust = GustEdgeValue(None, None, None)

timer = sched.scheduler(time.time, time.sleep)

# Guards the six buffers above and the EdgeValue trackers below: store_reading() (main thread, reading
# the Arduino/simulator) and time_event() (background thread, driven by the scheduler) both touch them.
readings_lock = threading.Lock()


def _drain(buffer):
    items = list(buffer)
    buffer.clear()
    return items


def find_arduino_port():
    for port in list_ports.comports():
        description = (port.description or "").lower()
        if port.vid in ARDUINO_VENDOR_IDS or 'arduino' in description:
            return port.device
    return None


def connect_to_arduino():
    port = SERIAL_PORT_OVERRIDE or find_arduino_port()
    if port is None:
        raise RuntimeError(
            "No Arduino serial port found. Connect the weather station, or set "
            "WEATHERSTATION_SIMULATE=1 to run with synthetic data instead.")
    return serial.Serial(port, baudrate=9600, timeout=1.0)


def generate_simulated_reading():
    return (
        f"T:{round(random.uniform(15, 28), 1)},"
        f"H:{round(random.uniform(40, 80))},"
        f"R:{round(random.uniform(0, 2), 1)},"
        f"W:{round(random.uniform(0, 20), 1)},"
        f"D:{random.choice(WIND_DIRECTIONS)},"
        f"P:{round(random.uniform(995, 1025), 1)}"
    )


def main():
    logging.basicConfig(level=LOG_LEVEL, stream=sys.stdout,
                         format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    initialize_database()
    timer.enter(60, 1, time_event)
    threading.Thread(target=timer.run, daemon=True).start()

    if SIMULATE:
        logger.info("Running in simulation mode: generating synthetic readings, no Arduino connected")
        while True:
            slice_data(generate_simulated_reading())
            time.sleep(SIMULATED_READING_INTERVAL_SECONDS)
    else:
        arduino_connection = connect_to_arduino()
        while True:
            data = arduino_connection.readline().decode('utf-8').strip()
            if data:
                slice_data(data)


def slice_data(data):
    weather_parameters = data.split(',')
    parsed_values = {}
    for parameter in weather_parameters:
        key, value = parameter.split(':')
        parsed_values[key] = value
    store_reading(parsed_values)


def store_reading(parsed_values):
    with readings_lock:
        if 'T' in parsed_values:
            temperature = float(parsed_values['T'])
            temperatureList.append(temperature)
            maxTemperature.update_max_edge(temperature)
            minTemperature.update_min_edge(temperature)
        if 'H' in parsed_values:
            humidity = float(parsed_values['H'])
            humidityList.append(humidity)
            maxHumidity.update_max_edge(humidity)
            minHumidity.update_min_edge(humidity)
        if 'P' in parsed_values:
            pressure = float(parsed_values['P'])
            pressureList.append(pressure)
            maxPressure.update_max_edge(pressure)
            minPressure.update_min_edge(pressure)
        if 'R' in parsed_values:
            rainList.append(float(parsed_values['R']))
        if 'D' in parsed_values:
            windDirectionList.append(parsed_values['D'])
        if 'W' in parsed_values:
            wind_speed = float(parsed_values['W'])
            windSpeedList.append(wind_speed)
            maxWindGust.update_max_edge(wind_speed, parsed_values.get('D'))


def time_event():
    timer.enter(60, 1, time_event)
    current_time = datetime.now()
    logger.debug("Every minute")
    if current_time.minute % 5 == 0:
        logger.info("Every five minutes")
        with readings_lock:
            temperature_snapshot = _drain(temperatureList)
            humidity_snapshot = _drain(humidityList)
            pressure_snapshot = _drain(pressureList)
            wind_speed_snapshot = _drain(windSpeedList)
            rain_snapshot = _drain(rainList)
            direction_snapshot = _drain(windDirectionList)
        if temperature_snapshot:
            mean_temp = numpy.sum(temperature_snapshot) / len(temperature_snapshot)
            mean_humidity = numpy.sum(humidity_snapshot) / len(humidity_snapshot)
            mean_pressure = numpy.sum(pressure_snapshot) / len(pressure_snapshot)
            mean_wind_speed = numpy.sum(wind_speed_snapshot) / len(wind_speed_snapshot)
            accumulated_rain = numpy.sum(rain_snapshot)
            predominant_wind = most_common(direction_snapshot)
            store_weather_parameters_in_database(mean_wind_speed, predominant_wind, mean_temp, mean_humidity,
                                                 mean_pressure, accumulated_rain, current_time)
    if current_time.hour == 0 and current_time.minute == 0:
        logger.info("Every midnight")
        with readings_lock:
            store_edge_values_in_database(maxTemperature, minTemperature, maxHumidity, minHumidity,
                                           maxPressure, minPressure, maxWindGust)
            maxTemperature.reset_value()
            minTemperature.reset_value()
            maxHumidity.reset_value()
            minHumidity.reset_value()
            maxPressure.reset_value()
            minPressure.reset_value()
            maxWindGust.reset_value()


def most_common(direction_list):
    dictionary = {
        "N": direction_list.count("N"),
        "S": direction_list.count("S"),
        "E": direction_list.count("E"),
        "W": direction_list.count("W"),
        "NE": direction_list.count("NE"),
        "NW": direction_list.count("NW"),
        "SE": direction_list.count("SE"),
        "SW": direction_list.count("SW"),
    }
    return max(dictionary, key=dictionary.get)


if __name__ == '__main__':
    main()
