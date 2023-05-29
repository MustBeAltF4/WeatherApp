import psycopg2
import requests
from flask import Flask, jsonify, request, render_template
from datetime import date

app = Flask(__name__)

params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'weather',
    'user': 'postgres',
    'password': 'Vi243b7zz'
}


def get_weather_data(city):
    url = f'http://api.weatherapi.com/v1/current.json?key=ТВОЙ_КЛЮЧ&q={city}&aqi=no'
    response = requests.get(url)
    data = response.json()
    return data


def save_to_database(data):
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute('INSERT INTO weather_data (city, temperature_celsius, humidity, wind_speed, date) VALUES (%s, %s, '
                    '%s, %s, %s)',
                    (data['location']['name'], data['current']['temp_c'], data['current']['humidity'], data['current']['wind_kph'], date.today()))
        conn.commit()
        cur.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def get_weather_data_from_database(city):
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(f"SELECT temperature_celsius, humidity, wind_speed, date FROM weather_data WHERE city = '{city.capitalize()}' ORDER BY date DESC LIMIT 1")
        data = cur.fetchone()
        cur.close()
        conn.close()
        if data is not None:
            return {
                'city': city.capitalize(),
                'temperature_celsius': data[0],
                'humidity': data[1],
                'wind_speed': data[2],
                'date': data[3].strftime('%Y-%m-%d')
            }
        else:
            return None
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def get_weather_forecast(city):
    url = f'http://api.weatherapi.com/v1/forecast.json?key=ТВОЙ_КЛЮЧ&q={city}&days=3'     #
    response = requests.get(url)
    data = response.json()
    forecast = []
    date.today()
    for day in data['forecast']['forecastday']:
        forecast_date = day['date']
        for hour in day['hour']:
            if hour['time'].startswith('12'):
                forecast.append({
                    'date': forecast_date,
                    'temperature_celsius': hour['temp_c']
                })
                break
    return forecast


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', '')
    data = get_weather_data(city)
    save_to_database(data)
    return jsonify(data)


@app.route('/weather_db', methods=['GET'])
def get_weather_from_database():
    city = request.args.get('city', '')
    data = get_weather_data_from_database(city)
    if data is not None:
        return jsonify(data)
    else:
        data = get_weather_data(city)
        save_to_database(data)
        return jsonify(data)


@app.route('/forecast', methods=['GET'])
def get_forecast():
    city = request.args.get('city', '')
    forecast = get_weather_forecast(city)
    return jsonify(forecast)


if __name__ == '__main__':
    app.run(debug=True)
