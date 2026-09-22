from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

from flask import Blueprint, Flask, jsonify, request

import DatabaseOperations as db

PARAMETERS = {'temperature', 'humidity', 'pressure', 'windSpeed', 'rainfall'}
TIMESPANS = {'today', 'last7Days', 'lastYear'}

app = Flask(__name__)
weather = Blueprint('weather', __name__, url_prefix='/weather')


def _epoch_to_iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def _local_midnight(moment):
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


@weather.route('/live')
def live():
    latest = db.fetch_latest_raw_reading()
    if latest is None:
        return jsonify({})

    wind_speed, wind_direction, temperature, humidity, pressure, date_epoch = latest
    today_start_epoch = int(_local_midnight(datetime.now()).timestamp())
    rainfall_today = db.fetch_rain_accumulated_since(today_start_epoch)

    return jsonify({
        "temperatureC": temperature,
        "humidityPct": humidity,
        "pressureHpa": pressure,
        "rainfallTodayMm": rainfall_today,
        "windSpeedKmh": wind_speed,
        "windDirection": wind_direction,
        "recordedAt": _epoch_to_iso(date_epoch),
    })


@weather.route('/history/<parameter>')
def history(parameter):
    if parameter not in PARAMETERS:
        return jsonify({"error": f"Unknown parameter '{parameter}'"}), 400

    timespan = request.args.get('timespan')
    start = request.args.get('start')
    end = request.args.get('end')

    if timespan:
        if timespan not in TIMESPANS:
            return jsonify({"error": f"Unknown timespan '{timespan}'"}), 400
        return jsonify(_points_for_timespan(parameter, timespan))

    if start and end:
        try:
            return jsonify(_points_for_range(parameter, start, end))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    return jsonify({"error": "Provide either 'timespan' or both 'start' and 'end'"}), 400


def _points_for_timespan(parameter, timespan):
    today_start = _local_midnight(datetime.now())

    if timespan == 'today':
        rows = db.fetch_raw_readings(int(today_start.timestamp()), int((today_start + timedelta(days=1)).timestamp()))
        return _hourly_points(parameter, rows)

    if timespan == 'last7Days':
        range_start = today_start - timedelta(days=7)
        rows = db.fetch_daily_summaries(int(range_start.timestamp()), int(today_start.timestamp()))
        return _daily_points(parameter, rows)

    range_start = today_start - timedelta(days=366)
    rows = db.fetch_daily_summaries(int(range_start.timestamp()), int(today_start.timestamp()))
    return _monthly_points(parameter, rows)


def _points_for_range(parameter, start, end):
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        raise ValueError("'start'/'end' must be dates in YYYY-MM-DD format")
    if end_date < start_date:
        raise ValueError("'end' must not be before 'start'")

    day_count = (end_date - start_date).days + 1
    if day_count > 366:
        raise ValueError("range must not exceed 366 days")

    range_end_exclusive = end_date + timedelta(days=1)

    if day_count == 1:
        rows = db.fetch_raw_readings(int(start_date.timestamp()), int(range_end_exclusive.timestamp()))
        return {"granularity": "hourly", "points": _hourly_points(parameter, rows)}

    if day_count <= 30:
        rows = db.fetch_daily_summaries(int(start_date.timestamp()), int(range_end_exclusive.timestamp()))
        return {"granularity": "daily", "points": _daily_points(parameter, rows)}

    rows = db.fetch_daily_summaries(int(start_date.timestamp()), int(range_end_exclusive.timestamp()))
    return {"granularity": "monthly", "points": _monthly_points(parameter, rows)}


# --- RawReadings rows: (Wind_Speed, Wind_Direction, Temperature, Humidity, Pressure, Rain, Date) ---

def _hourly_points(parameter, rows):
    buckets = defaultdict(list)
    for row in rows:
        hour_start = datetime.fromtimestamp(row[6]).replace(minute=0, second=0, microsecond=0)
        buckets[hour_start].append(row)

    return [_point_from_raw_bucket(parameter, _epoch_to_iso(int(hour_start.timestamp())), buckets[hour_start])
            for hour_start in sorted(buckets)]


def _point_from_raw_bucket(parameter, timestamp, rows):
    if parameter == 'rainfall':
        return {"timestamp": timestamp, "accumulatedRainMm": sum(row[5] for row in rows)}

    if parameter == 'windSpeed':
        directions = Counter(row[1] for row in rows if row[1])
        dominant_direction = directions.most_common(1)[0][0] if directions else None
        return {
            "timestamp": timestamp,
            "meanSpeedKmh": mean(row[0] for row in rows),
            "dominantDirection": dominant_direction,
        }

    column_index = {'temperature': 2, 'humidity': 3, 'pressure': 4}[parameter]
    return {"timestamp": timestamp, "mean": mean(row[column_index] for row in rows)}


# --- DailySummary rows: (Day, Max_Wind_Gust, Max_Wind_Gust_Direction, Max_Temp, Min_Temp, Max_Humidity,
#     Min_Humidity, Max_Pressure, Min_Pressure, Mean_Temp, Mean_Humidity, Mean_Pressure, Mean_Wind_Speed,
#     Dominant_Wind_Direction, Accumulated_Rain) ---

_DAILY_SUMMARY_COLUMNS = {
    'temperature': (9, 3, 4),
    'humidity': (10, 5, 6),
    'pressure': (11, 7, 8),
}


def _daily_points(parameter, rows):
    return [_point_from_daily_summary_row(parameter, row) for row in rows]


def _point_from_daily_summary_row(parameter, row):
    timestamp = _epoch_to_iso(row[0])

    if parameter == 'rainfall':
        return {"timestamp": timestamp, "accumulatedRainMm": row[14]}

    if parameter == 'windSpeed':
        point = {"timestamp": timestamp, "meanSpeedKmh": row[12], "dominantDirection": row[13]}
        if row[1] is not None:
            point["maxGustKmh"] = row[1]
            point["maxGustDirection"] = row[2]
        return point

    mean_index, max_index, min_index = _DAILY_SUMMARY_COLUMNS[parameter]
    point = {"timestamp": timestamp, "mean": row[mean_index]}
    if row[max_index] is not None:
        point["max"] = row[max_index]
    if row[min_index] is not None:
        point["min"] = row[min_index]
    return point


def _monthly_points(parameter, rows):
    buckets = defaultdict(list)
    for row in rows:
        month_start = datetime.fromtimestamp(row[0]).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        buckets[month_start].append(row)

    return [_rollup_month(parameter, _epoch_to_iso(int(month_start.timestamp())), buckets[month_start])
            for month_start in sorted(buckets)]


def _rollup_month(parameter, timestamp, rows):
    if parameter == 'rainfall':
        return {"timestamp": timestamp, "accumulatedRainMm": sum(row[14] for row in rows)}

    if parameter == 'windSpeed':
        directions = Counter(row[13] for row in rows if row[13])
        dominant_direction = directions.most_common(1)[0][0] if directions else None
        point = {
            "timestamp": timestamp,
            "meanSpeedKmh": mean(row[12] for row in rows),
            "dominantDirection": dominant_direction,
        }
        gust_rows = [row for row in rows if row[1] is not None]
        if gust_rows:
            best_gust_row = max(gust_rows, key=lambda row: row[1])
            point["maxGustKmh"] = best_gust_row[1]
            point["maxGustDirection"] = best_gust_row[2]
        return point

    mean_index, max_index, min_index = _DAILY_SUMMARY_COLUMNS[parameter]
    means = [row[mean_index] for row in rows if row[mean_index] is not None]
    maxes = [row[max_index] for row in rows if row[max_index] is not None]
    mins = [row[min_index] for row in rows if row[min_index] is not None]

    point = {"timestamp": timestamp}
    if means:
        point["mean"] = mean(means)
    if maxes:
        point["max"] = max(maxes)
    if mins:
        point["min"] = min(mins)
    return point


app.register_blueprint(weather)


if __name__ == '__main__':
    db.initialize_database()
    app.run(host='0.0.0.0', port=5000)
