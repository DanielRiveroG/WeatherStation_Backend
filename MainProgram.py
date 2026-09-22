import sched
import time
from datetime import datetime
import serial
import numpy

from DatabaseOperations import *
from Models import *

# arduinoConnection = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=1.0)

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


def main():
    initialize_database()
    timer.enter(60, 1, time_event)
    timer.run()
    while True:
        # data = arduinoConnection.readline()
        data = "W:1,R:5,H2"
        slice_data(data)


def slice_data(data):
    weather_parameters = data.split(',')
    parsed_values = {}
    for parameter in weather_parameters:
        key, value = parameter.split(':')
        parsed_values[key] = value
    store_reading(parsed_values)


def store_reading(parsed_values):
    if 'T' in parsed_values:
        temperature = parsed_values['T']
        temperatureList.append(temperature)
        maxTemperature.update_max_edge(temperature)
        minTemperature.update_min_edge(temperature)
    if 'H' in parsed_values:
        humidity = parsed_values['H']
        humidityList.append(humidity)
        maxHumidity.update_max_edge(humidity)
        minHumidity.update_min_edge(humidity)
    if 'P' in parsed_values:
        pressure = parsed_values['P']
        pressureList.append(pressure)
        maxPressure.update_max_edge(pressure)
        minPressure.update_min_edge(pressure)
    if 'R' in parsed_values:
        rainList.append(parsed_values['R'])
    if 'D' in parsed_values:
        windDirectionList.append(parsed_values['D'])
    if 'W' in parsed_values:
        wind_speed = parsed_values['W']
        windSpeedList.append(wind_speed)
        maxWindGust.update_max_edge(wind_speed, parsed_values.get('D'))


def time_event():
    timer.enter(60, 1, time_event)
    current_time = datetime.now()
    print("Every minute")
    if current_time.minute % 5 == 0:
        print("Every five minutes")
        mean_temp = numpy.sum(temperatureList) / len(temperatureList)
        mean_humidity = numpy.sum(humidityList) / len(humidityList)
        mean_pressure = numpy.sum(pressureList) / len(pressureList)
        mean_wind_speed = numpy.sum(windSpeedList) / len(windSpeedList)
        accumulated_rain = numpy.sum(rainList)
        predominant_wind = most_common(windDirectionList)
        store_weather_parameters_in_database(mean_wind_speed, predominant_wind, mean_temp, mean_humidity, mean_pressure,
                                             accumulated_rain, current_time)
    if current_time.hour == 0 and current_time.minute == 0:
        print("Every midnight")
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
