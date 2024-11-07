
import time
import math
import Adafruit_DHT
import pyrebase
from RPLCD.i2c import CharLCD
from w1thermsensor import W1ThermSensor, Unit
from mpu6050 import mpu6050
import RPi.GPIO as GPIO
import requests

# Firebase configuration
config = {
    "apiKey": "",  
    "authDomain": "",  
    "databaseURL": "",  
    "projectId": "",  
    "storageBucket": "", 
    "messagingSenderId": "",  
    "appId": "", 
    "measurementId": "" 
}

# Initialize Firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# ThingSpeak and Pushbullet credentials
THINGSPEAK_WRITE_API_KEY = '' #API token
PUSHBULLET_ACCESS_TOKEN = '' #API token

# Set up GPIO mode and sensor pins
GPIO.setmode(GPIO.BCM)
pulse_sensor_pin = 21  # GPIO 21
red_led_pin = 18       # GPIO 18 (Red LED)
green_led_pin = 17     # GPIO 17 (Green LED)
buzzer_pin = 23        # GPIO 23 (Buzzer)

# Set up sensor pins
GPIO.setup(pulse_sensor_pin, GPIO.IN)
GPIO.setup(red_led_pin, GPIO.OUT)
GPIO.setup(green_led_pin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT)

# Initialize sensors
dht_sensor = Adafruit_DHT.DHT11
dht_pin = 4  
lcd = CharLCD('PCF8574', 0x27)
mpu_sensor = mpu6050(0x68)

# Tilt threshold in degrees
TILT_THRESHOLD = 5

# Temperature thresholds
HIGH_BODY_TEMP_THRESHOLD = 100.4  # 100.4°F

# Pulse detection delay (2-3 minutes)
PULSE_TIMEOUT = 180  # 3 minutes in seconds

# Initialize variables to track pulse detection time
last_pulse_time = None
pulse_status = "Pulse Detected"

def calculate_tilt_angle(accel_data):
    accel_x = accel_data['x']
    accel_z = accel_data['z']
    tilt_angle = math.degrees(math.atan2(accel_x, accel_z))
    return abs(tilt_angle) 

def detect_tilt():
    accel_data = mpu_sensor.get_accel_data()
    tilt_angle = calculate_tilt_angle(accel_data)
    return tilt_angle > TILT_THRESHOLD

def read_temperature():
    sensor = W1ThermSensor()
    temperature_fahrenheit = sensor.get_temperature(Unit.DEGREES_F)
    return temperature_fahrenheit

# Function to send data to ThingSpeak
def send_to_thingspeak(dht_temperature, humidity, body_temp):
    url = f'https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_API_KEY}&field1={dht_temperature}&field2={humidity}&field3={body_temp}'
    try:
        response = requests.get(url, timeout=40)  # 10 seconds timeout ( majhe majhe connection er jonno besi timeout dite hobe max 30)
        if response.status_code == 200:
            print("Data sent to ThingSpeak successfully.")
        else:
            print("Error sending data to ThingSpeak.")
    except requests.RequestException as e:
        print(f"Error sending data to ThingSpeak: {e}")

# Function to send Pushbullet notification
def send_pushbullet_notification(message):
    pushbullet_url = 'https://api.pushbullet.com/v2/pushes'
    headers = {'Access-Token': PUSHBULLET_ACCESS_TOKEN}
    payload = {
        'type': 'note',
        'title': 'Patient Monitoring Alert',
        'body': message
    }
    try:
        response = requests.post(pushbullet_url, headers=headers, data=payload, timeout=10)  # 10 seconds timeout
        if response.status_code == 200:
            print("Pushbullet notification sent.")
        else:
            print("Error sending Pushbullet notification.")
    except requests.RequestException as e:
        print(f"Error sending Pushbullet notification: {e}")

previous_body_temp = None
previous_air_temp = None
previous_humidity = None

try:
    while True:
        # Read DHT11 sensor data
        humidity, dht_temperature = Adafruit_DHT.read_retry(dht_sensor, dht_pin)
        body_temp = read_temperature()

        # Display body temperature only if it has changed
        if previous_body_temp != body_temp:
            lcd.clear()
            lcd.write_string(f'Body Temp: {body_temp:.1f}F')
            previous_body_temp = body_temp

        print(f"Body Temperature in Fahrenheit: {body_temp}°F")

        if humidity is not None and dht_temperature is not None:
            print(f'Air Temperature: {dht_temperature}°C')
            print(f'Humidity: {humidity}%')

            # Update LCD only if air temp or humidity changed
            if previous_air_temp != dht_temperature or previous_humidity != humidity:
                time.sleep(1)
                lcd.clear()
                lcd.write_string(f'Air Temp: {dht_temperature}C')
                lcd.crlf()
                lcd.write_string(f'Humidity: {humidity}%')
                previous_air_temp = dht_temperature
                previous_humidity = humidity

            # Fall detection status
            fall_status = "fallen" if detect_tilt() else "not fallen"
            print(f"Fall Status: {fall_status}")

            # Pulse detection status
            if GPIO.input(pulse_sensor_pin) == GPIO.LOW:  # Pulse detected (assuming active low)
                pulse_status = "Pulse Detected"
                last_pulse_time = time.time()  # Update last pulse time when pulse is detected
                print(f"Pulse Status: {pulse_status}")
            else:
                # If pulse is not detected, check the time since the last pulse
                if last_pulse_time and (time.time() - last_pulse_time) > PULSE_TIMEOUT:
                    pulse_status = "No pulse"
                    print(f"Pulse Status: {pulse_status}")
                    GPIO.output(red_led_pin, GPIO.HIGH)  # Turn on red LED
                    GPIO.output(green_led_pin, GPIO.LOW)  # Turn off green LED
                    GPIO.output(buzzer_pin, GPIO.HIGH)  # Activate buzzer
                    send_pushbullet_notification("No pulse detected for 2-3 minutes!")

            # Check for high body temperature, fall, or no pulse
            if body_temp >= HIGH_BODY_TEMP_THRESHOLD:
                print("High Body Temperature Detected!")
                GPIO.output(red_led_pin, GPIO.HIGH)  # Turn on red LED
                GPIO.output(green_led_pin, GPIO.LOW)  # Turn off green LED
                GPIO.output(buzzer_pin, GPIO.HIGH)  # Activate buzzer
                send_pushbullet_notification("High body temperature detected!")
            elif fall_status == "fallen":
                print("Fall Detected!")
                GPIO.output(red_led_pin, GPIO.HIGH)  # Turn on red LED
                GPIO.output(green_led_pin, GPIO.LOW)  # Turn off green LED
                GPIO.output(buzzer_pin, GPIO.HIGH)  # Activate buzzer
                send_pushbullet_notification("Fall detected!")
            else:
                GPIO.output(red_led_pin, GPIO.LOW)  # Turn off red LED
                GPIO.output(green_led_pin, GPIO.HIGH)  # Turn on green LED
                GPIO.output(buzzer_pin, GPIO.LOW)  # Deactivate buzzer

            # Prepare and send data to Firebase
            data = {
                "sensorDHT": {
                    "temperature": dht_temperature,
                    "humidity": humidity
                },
                "Body Temperature": body_temp,
                "Fall Status": fall_status,
                "Pulse Status": pulse_status
            }
            try:
                db.update(data)
                print("Data sent to Firebase successfully.")
            except Exception as e:
                print("Error sending data to Firebase:", e)

            # Send data to ThingSpeak
            send_to_thingspeak(dht_temperature, humidity, body_temp)

        else:
            print('Failed to read from DHT sensor.')

        time.sleep(2)

except KeyboardInterrupt:
    print("Program terminated")

finally:
    # Cleanup GPIO to prevent conflicts when the script ends
    GPIO.cleanup()
    print("GPIO cleanup completed.")
