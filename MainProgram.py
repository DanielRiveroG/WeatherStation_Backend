import sched
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

timer = sched.scheduler(time.time, time.sleep)


def main():
    timer.enter(60, 1, time_event)
    timer.run()
    while True:
        data = arduinoConnection.readline()
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
    if current_time.minute % 5 == 0:
        print("Every five minutes")


if __name__ == '__main__':
    main()
