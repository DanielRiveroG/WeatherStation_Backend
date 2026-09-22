import sqlite3
from datetime import datetime, timedelta


def store_weather_parameters_in_database(wind_speed, wind_direction, temperature, humidity, pressure, rain, timestamp):
    day = timestamp.strftime("%d%m%y")
    hour = timestamp.strftime("%H:%M:%S")
    query_string = "INSERT INTO DailyRegister(Wind_Speed, Wind_Direction, Temperature, Humidity, Pressure, Rain, " \
                   "Day, Hour) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
    execute_query(query_string, (wind_speed, wind_direction, temperature, humidity, pressure, rain, day, hour))


def store_edge_values_in_database(max_temp, min_temp, max_hum, min_hum, max_wind):
    yesterday = datetime.now() - timedelta(days=1)
    day = yesterday.strftime("%d%m%y")
    query_string = "INSERT INTO EdgeRegister(Max_Wind, Max_Wind_Time, Max_Temp, Max_Temp_Time, Min_Temp, " \
                   "Min_Temp_Time, Max_Hum, Max_Hum_Time, Min_Hum, Min_Hum_Time, Day) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    execute_query(query_string, (max_wind.value, max_wind.timestamp, max_temp.value, max_temp.timestamp,
                                  min_temp.value, min_temp.timestamp, max_hum.value, max_hum.timestamp,
                                  min_hum.value, min_hum.timestamp, day))


def execute_query(query_string, parameters=()):
    try:
        sqlite_connection = sqlite3.connect('Weather_Data.db')
        cursor = sqlite_connection.cursor()
        cursor.execute(query_string, parameters)
        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.commit()
            sqlite_connection.close()
