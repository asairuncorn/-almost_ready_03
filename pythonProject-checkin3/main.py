from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import RPi.GPIO as GPIO
from switch import Switch
from led import LED
from pump import Pump
from timer import Timer
from sensor import PressureSensor
import threading
import os
from PiControler import*
import eventlet
from data_file_render import *

# Set GPIO pins for switch, LED, and pump relay
SWITCH_PIN = 17  # GPIO pin for the start switch
LED_PIN = 27     # GPIO pin for the LED
RELAY_PIN = 22   # GPIO pin for the pump relay



eventlet.monkey_patch()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Use environment variable or default key
socketio = SocketIO(app, cors_allowed_origins="*")


GPIO.setmode(GPIO.BCM)  # Set GPIO mode

def monitor_switch():
    while True:
        if switch.is_pressed():
            socketio.emit('switch_status', {'status': 'active'})
        else:
            socketio.emit('switch_status', {'status': 'install_cartridge'})

        socketio.sleep(1)  # Poll the switch status every second
# #
data_loger = DataLogger("data_log.csv", "csv" )

def handle_sensor_data(data1, data2):



    formatted_data1 = f"{data1:.2f}"
    print(f"Emitted sensor data: {formatted_data1}")
    socketio.emit('pressure_sensor_reading_1', {'message': formatted_data1})
    socketio.sleep(1)  # Sleep for 1 second bef

    formatted_data2 = f"{data2:.2f}"
    print(f"Emitted sensor data: {formatted_data2}")
    socketio.emit('pressure_sensor_reading_2', {'message': formatted_data2})
    socketio.sleep(1)  # Sleep for 1 second bef

    data_loger.log_data(sensor1 = formatted_data1, sensor2 = formatted_data2)

def update_progress_dial( progres):
    emit('update_state', {'bay_id': 1, 'status': 'Running', 'progress': progres}, broadcast=True)



#
#

# Serve the HTML page
# @app.route('/')
# def index():
#     return render_template('index_c.html')
#

switch = Switch(SWITCH_PIN)
led = LED(LED_PIN)

# @socketio.on('connect')
# def handle_connect():
#     emit('initialize_state', progress_state)
#
#
# @socketio.on('switch_status_replay')
# def switch_status():
#     print("switch_status")
#
# @socketio.on('testing_state')
# def testing_state(state):
#     print(f"testing - state{state} ")
#
#
# @socketio.on('start_pump')
# def handle_pump(data):
#
#     print('proces_time', data.get('proces_time'))
#     time_process = data.get('proces_time')
#     print("Pump started:", data)  # Log incoming data for debugging
#     button_id = data.get("blockId")
#     print("Button press event received:", button_id)
#
#     pump = Pump(RELAY_PIN)
#     pressure_sensor = PressureSensor()
#     timer = Timer(time_process, pressure_sensor, handle_sensor_data)
#
#     pump_controller = PiPumpController(switch, led, pump, timer)
#     pump_controller.check_and_run()
#
thread = threading.Thread(target=monitor_switch, daemon=True)
thread.start()

@app.route('/')
def index():
    return render_template('index_c.html')







# Store the state for each bay
progress_state = {
    1: {'status': 'Idle', 'progress': 0, 'pressure': 0},
    2: {'status': 'Idle', 'progress': 0, 'pressure': 0},
    3: {'status': 'Idle', 'progress': 0, 'pressure': 0},
    4: {'status': 'Idle', 'progress': 0, 'pressure': 0},
}

# Send initial state to new client
@socketio.on('connect')
def handle_connect():
    emit('initialize_state', progress_state)

# Handle button press events
@socketio.on('start_progress')
def handle_start_progress(data):
    bay_id = data['bay_id']
    progress_state[bay_id]['status'] = 'Running'
    progress_state[bay_id]['progress'] = 0

    emit('update_state', {'bay_id': bay_id, 'status': 'Running', 'progress': 0}, broadcast=True)
    print(bay_id, progress_state[bay_id]['progress'])

    pump = Pump(RELAY_PIN)
    pressure_sensor = PressureSensor()
    timer = Timer(60, pressure_sensor, handle_sensor_data)
    timer.start(update_progress_dial)
    # timer.start(update_progress_dial, bay_id, progres)
    # progres = timer.send_time()
    # emit('update_state', {'bay_id': bay_id, 'status': 'Running', 'progress': progres}, broadcast=True)
    # #
    # # pump_controller = PiPumpController(switch, led, pump, timer)
    # # pump_controller.check_and_run()

@socketio.on('stop_progress')
def handle_stop_progress(data):
    bay_id = data['bay_id']
    progress_state[bay_id]['status'] = 'Stopped'
    emit('update_state', {'bay_id': bay_id, 'status': 'Stopped', 'progress': progress_state[bay_id]['progress']}, broadcast=True)

@socketio.on('update_pressure')
def handle_update_pressure(data):
    bay_id = data['bay_id']
    pressure = data['pressure']
    progress_state[bay_id]['pressure'] = pressure
    emit('update_pressure', {'bay_id': bay_id, 'pressure': pressure}, broadcast=True)

# Handle setting time or any other configuration
@socketio.on('set_time')
def handle_set_time(data):
    bay_id = data['bay_id']
    time = data['time']
    # Update time for the bay
    # If needed, store time to progress_state and notify other clients
    emit('update_time', {'bay_id': bay_id, 'time': time}, broadcast=True)





# Run the server using socketio.run for WebSocket support
if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='127.0.0.1', port=5005, debug=True, allow_unsafe_werkzeug=True)




