import sqlite3
import time
from datetime import timedelta


def store_weather_parameters_in_database(wind_speed, wind_direction, temperature, humidity, pressure, rain, timestamp):
    day = timestamp.strftime("%d%m%y")
    hour = timestamp.strftime("%H:%M:%S")
    query_string = f"INSERT INTO DailyRegister(Wind_Speed, Wind_Direction, Temperature, Humidity, Pressure, Rain, " \
                   f"Day, Hour) VALUES({wind_speed}, {wind_direction}, {temperature}, {humidity}, {pressure}, " \
                   f"{rain}, {day}, {hour}) "
    execute_query(query_string)


def store_edge_values_in_database(max_temp, min_temp, max_hum, min_hum, max_wind):
    yesterday = time.today() - timedelta(days=1)
    day = yesterday.strftime("%d%m%y")
    query_string = f"INSERT INTO EdgeRegister(Max_Wind, Max_Wind_Time, Max_Temp, Max_Temp_Time, Min_Temp, " \
                   f"Min_Temp_Time, Max_Hum, Max_Hum_Time, Min_Hum, Min_Hum_Time, Day) VALUES({max_wind.value}, " \
                   f"{max_wind.timestamp}, {max_temp.value}, {max_temp.timestamp}, {min_temp.value}, " \
                   f"{min_temp.timestamp}, {max_hum.value}, {max_hum.timestamp}, {min_hum.value}, {min_hum.timestamp}, {day})"
    execute_query(query_string)


def execute_query(query_string):
    try:
        sqlite_connection = sqlite3.connect('Weather_Data.db')
        cursor = sqlite_connection.cursor()
        cursor.execute(query_string)
        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.commit()
            sqlite_connection.close()
