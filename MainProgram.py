import time
import serial
from Models import *

arduinoConnection = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=1.0)

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


def main():
    while True:
        data = arduinoConnection.readline()
        store_in_array(data)


def store_in_array(data):
    weather_parameters = data.split(',')
    for parameter in weather_parameters:
        splitted_parameter = parameter.split(':')
        if splitted_parameter[0] == 'T':
            temperatureList.append(splitted_parameter[1])
            maxTemperature.update_max_edge(splitted_parameter[1])
            minTemperature.update_min_edge(splitted_parameter[1])
        elif splitted_parameter[0] == 'H':
            humidityList.append(splitted_parameter[1])
            maxHumidity.update_max_edge(splitted_parameter[1])
            minHumidity.update_min_edge(splitted_parameter[1])
        elif splitted_parameter[0] == 'W':
            windSpeedList.append(splitted_parameter[1])
            maxWind.update_max_edge(splitted_parameter[1])
        elif splitted_parameter[0] == 'D':
            windDirectionList.append(splitted_parameter[1])
        elif splitted_parameter[0] == 'P':
            pressureList.append(splitted_parameter[1])
        elif splitted_parameter[0] == 'R':
            pressureList.append(splitted_parameter[1])


    print(data)


if __name__ == '__main__':
    main()
