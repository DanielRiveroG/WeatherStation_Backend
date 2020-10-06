import sched
import time
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
maxWind = EdgeValue(None, None)

timer = sched.scheduler(time.time, time.sleep)


def main():
    timer.enter(60, 1, time_event)
    timer.run()
    while True:
        # data = arduinoConnection.readline()
        data = "W:1,R:5,H2"
        slice_data(data)


def slice_data(data):
    weather_parameters = data.split(',')
    for parameter in weather_parameters:
        splitted_parameter = parameter.split(':')
        store_in_array(splitted_parameter[0], splitted_parameter[1])


def store_in_array(parameter, value):
    if parameter == 'T':
        temperatureList.append(value)
        maxTemperature.update_max_edge(value)
        minTemperature.update_min_edge(value)
    elif parameter == 'H':
        humidityList.append(value)
        maxHumidity.update_max_edge(value)
        minHumidity.update_min_edge(value)
    elif parameter == 'W':
        windSpeedList.append(value)
        maxWind.update_max_edge(value)
    elif parameter == 'D':
        windDirectionList.append(value)
    elif parameter == 'P':
        pressureList.append(value)
    elif parameter == 'R':
        pressureList.append(value)


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
        store_edge_values_in_database(maxTemperature, minTemperature, maxHumidity, minHumidity, maxWind)
        maxTemperature.reset_value()
        minTemperature.reset_value()
        maxHumidity.reset_value()
        minHumidity.reset_value()
        maxWind.reset_value()


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
    max(dictionary.iteritems(), key=numpy.operator.itemgetter(1))[0]


if __name__ == '__main__':
    main()
