import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = 'Weather_Data.db'


def initialize_database():
    execute_query("""
        CREATE TABLE IF NOT EXISTS RawReadings (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Wind_Speed REAL,
            Wind_Direction TEXT,
            Temperature REAL,
            Humidity REAL,
            Pressure REAL,
            Rain REAL,
            Date INTEGER
        )
    """)
    execute_query("""
        CREATE TABLE IF NOT EXISTS DailySummary (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Day INTEGER,
            Max_Wind_Gust REAL,
            Max_Wind_Gust_Direction TEXT,
            Max_Wind_Gust_Time INTEGER,
            Max_Temp REAL,
            Max_Temp_Time INTEGER,
            Min_Temp REAL,
            Min_Temp_Time INTEGER,
            Max_Humidity REAL,
            Max_Humidity_Time INTEGER,
            Min_Humidity REAL,
            Min_Humidity_Time INTEGER,
            Max_Pressure REAL,
            Max_Pressure_Time INTEGER,
            Min_Pressure REAL,
            Min_Pressure_Time INTEGER,
            Mean_Temp REAL,
            Mean_Humidity REAL,
            Mean_Pressure REAL,
            Mean_Wind_Speed REAL,
            Dominant_Wind_Direction TEXT,
            Accumulated_Rain REAL
        )
    """)


def store_weather_parameters_in_database(wind_speed, wind_direction, temperature, humidity, pressure, rain, timestamp):
    query_string = "INSERT INTO RawReadings(Wind_Speed, Wind_Direction, Temperature, Humidity, Pressure, Rain, Date) " \
                   "VALUES(?, ?, ?, ?, ?, ?, ?)"
    execute_query(query_string, (wind_speed, wind_direction, temperature, humidity, pressure, rain,
                                  int(timestamp.timestamp())))


def store_edge_values_in_database(max_temp, min_temp, max_hum, min_hum, max_wind_gust):
    # Pressure min/max and the gust's own wind direction aren't tracked yet (see decisions 0003/0008/0009's
    # noted gap) - stored as NULL until that tracking exists.
    yesterday = datetime.now() - timedelta(days=1)
    day_start = datetime(yesterday.year, yesterday.month, yesterday.day)
    day_start_epoch = int(day_start.timestamp())
    day_end_epoch = int((day_start + timedelta(days=1)).timestamp())

    mean_temp, mean_humidity, mean_pressure, mean_wind_speed, accumulated_rain = _fetch_daily_means(
        day_start_epoch, day_end_epoch)
    dominant_wind_direction = _fetch_dominant_direction(day_start_epoch, day_end_epoch)

    query_string = """
        INSERT INTO DailySummary(
            Day, Max_Wind_Gust, Max_Wind_Gust_Direction, Max_Wind_Gust_Time,
            Max_Temp, Max_Temp_Time, Min_Temp, Min_Temp_Time,
            Max_Humidity, Max_Humidity_Time, Min_Humidity, Min_Humidity_Time,
            Max_Pressure, Max_Pressure_Time, Min_Pressure, Min_Pressure_Time,
            Mean_Temp, Mean_Humidity, Mean_Pressure, Mean_Wind_Speed,
            Dominant_Wind_Direction, Accumulated_Rain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query_string, (
        day_start_epoch,
        max_wind_gust.value, None, max_wind_gust.timestamp,
        max_temp.value, max_temp.timestamp, min_temp.value, min_temp.timestamp,
        max_hum.value, max_hum.timestamp, min_hum.value, min_hum.timestamp,
        None, None, None, None,
        mean_temp, mean_humidity, mean_pressure, mean_wind_speed,
        dominant_wind_direction, accumulated_rain,
    ))


def _fetch_daily_means(day_start_epoch, day_end_epoch):
    row = _fetch_one(
        "SELECT AVG(Temperature), AVG(Humidity), AVG(Pressure), AVG(Wind_Speed), SUM(Rain) "
        "FROM RawReadings WHERE Date >= ? AND Date < ?",
        (day_start_epoch, day_end_epoch))
    return row if row else (None, None, None, None, None)


def _fetch_dominant_direction(day_start_epoch, day_end_epoch):
    row = _fetch_one(
        "SELECT Wind_Direction FROM RawReadings WHERE Date >= ? AND Date < ? "
        "GROUP BY Wind_Direction ORDER BY COUNT(*) DESC LIMIT 1",
        (day_start_epoch, day_end_epoch))
    return row[0] if row else None


def _fetch_one(query_string, parameters=()):
    sqlite_connection = None
    try:
        sqlite_connection = sqlite3.connect(DATABASE_PATH)
        cursor = sqlite_connection.cursor()
        cursor.execute(query_string, parameters)
        return cursor.fetchone()
    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
        return None
    finally:
        if sqlite_connection:
            sqlite_connection.close()


def execute_query(query_string, parameters=()):
    try:
        sqlite_connection = sqlite3.connect(DATABASE_PATH)
        cursor = sqlite_connection.cursor()
        cursor.execute(query_string, parameters)
        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.commit()
            sqlite_connection.close()
