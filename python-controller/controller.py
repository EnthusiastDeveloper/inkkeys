#!/usr/bin/env python3

"""
This is the main file, which reassigns keys, sets the content of the display and updates the LEDs.
The logic of this is built around "modes", which are defined in "modes.py".
Each mode can change key assignments, images, LED animations and their entire logic.
"""

import time
import re
import sys
import traceback                # Print tracebacks if an error is thrown and caught

# pylint: disable=import-error
from serial import SerialException
import serial.tools.list_ports  # Function to iterate over serial ports

from inkkeys import Device
from processchecks import get_active_processes, get_active_window
import modes
from mqtt import InkkeysMqtt


# None = Auto-detect, otherwise "/dev/ttyACM0" (Linux) or "COM1" (Windows)
SERIALPORT = None
# USB Vendor ID and Product ID
VID = 0x1b4f
PID = 0x9206

# More output on the command line
DEBUG = True

GET_ACTIVE_WINDOW_INTERVAL = 0.5
GET_RUNNING_PROCESSES_INTERVAL = 5.0


print("https://there.oughta.be/a/macro-keyboard")
print('I will try to stay connected. Press Ctrl+C to quit.')

# Set address to "None" if you do not want to use mqtt
mqtt = InkkeysMqtt(None, DEBUG)

# List of modes to be checked for in the main loop.
# Each mode must be either a running process or an active window (compiled regex pattern)
# The first mode that matches will be activated.
modes = [
            # {"mode": modes.ModeOBS(), "process": "obs"},
            {"mode": modes.ModeZoom(), "activeWindow": re.compile(".*Zoom")},
            # {"mode": modes.ModeBlender(), "activeWindow": re.compile("^Blender")},
            {"mode": modes.ModeGimp(), "activeWindow": re.compile("^gimp.*")},
            {"mode": modes.ModeFallback()}
        ]

##################################################################################################
# Usually there should not be anything to be customized below this point
##################################################################################################

def work():
    '''
    Main loop of the program. This is where the magic happens.
    '''
    current_mode = None             # The current working mode
    poll_interval = 0       # Polling interval as requested by the module
    last_poll = 0           # Last time the poll function of the current mode was called
    last_process_list = 0   # Last time the list of running processes was updated
    last_mode_check = 0     # Last time a decision about the mode was made
    active_window = None
    mqtt.connect()        # Connect to the MQTT server (if used)

    def if_matching_mode(mode):
        return ("process" in mode and mode["process"] in processes) \
            or ("activeWindow" in mode and mode["activeWindow"].match(active_window)) \
            or not ("process" in mode or "activeWindow" in mode)

    try:
        while True:
            now = time.time() # Start time of this iteration

            if now - last_process_list > GET_RUNNING_PROCESSES_INTERVAL:
                processes = get_active_processes()
                last_process_list = now

            if now - last_mode_check > GET_ACTIVE_WINDOW_INTERVAL:
                window = get_active_window()
                if window is not None:       # Ignore failures to get the active window fails.
                    if DEBUG and active_window != window:
                        print(f'Active window: {window}')
                    active_window = window
                # Get the first mode that matches the current active window or running process
                first_matching_mode = list(filter(if_matching_mode, modes))[0]
                # Only take action if the mode is different from the current one
                if first_matching_mode["mode"] != current_mode:
                    if DEBUG:
                        print(f'Switching from mode "{current_mode}" to: {first_matching_mode["mode"].__class__.__name__}')
                    if current_mode is not None:
                        current_mode.deactivate(device)
                        device.send_led_animation(2, 50, 20, b=255, iteration=2)
                        device.reset_display()
                    current_mode = first_matching_mode["mode"]
                    current_mode.activate(device)
                    poll_interval = 0
                last_mode_check = now

            # Regularly call the poll function of the mode if it requires regular polling
            if poll_interval is not False and now - last_poll > poll_interval >= 0:
                poll_interval = current_mode.poll(device)
                last_poll = now

            # Animate the LEDs and update the display
            current_mode.animate(device)
            # Check for key presses and call the corresponding callback functions
            device.poll()

            # Sleep until 1/30 sec have passed as there is no need to exceed 30 FPS
            time_to_30_fps = time.time() - now + 0.0333
            if time_to_30_fps > 0:
                time.sleep(time_to_30_fps)

    except KeyboardInterrupt:
        mqtt.disconnect()
        print('Disconnected from device. Hit Ctrl+c again to quit before reconnect.')

def is_port_matches(tested_port):
    '''
    Check if the given port matches the VID and PID of the device.
    '''
    return tested_port.vid == VID and tested_port.pid == PID

def try_using_port(port):
    '''
    Try to connect to the device on the given port. If successful, enter the main loop.
    Return False if the connection fails or the device is not the correct one.
    '''
    try:
        if device.connect(port):
            work()  # Success, enter main loop
            device.disconnect()
            return True
    except SerialException as serial_error:
        print("Serial error: ", serial_error)
    except Exception:
        # Something entirely unexpected happened.
        if DEBUG:
            print(traceback.format_exc())
        print("Error: ", sys.exc_info()[0])
    return False

# Instantiate the device
device = Device()
device.debug = DEBUG

work()

def main():
    '''
    Main function that tries to connect to the device and restarts the connection if it fails.
    '''
    try:
        while True:
            if SERIALPORT is not None:
                try_using_port(SERIALPORT)
            else:
                matching_ports = list(filter(is_port_matches, serial.tools.list_ports.comports()))
                # Iterate over all matching serial ports
                for port in matching_ports:
                    # Try connecting to this device
                    if try_using_port(port.device):
                        ## When the program reaches this point it means a successful connection
                        ##   and inkkeys was found.
                        ## If inkkeys got disconnected or some other kind of error occurred,
                        ##   skip the rest of the port list and start over.
                        break
            print("I will retry in three seconds...")
            time.sleep(3)
    except KeyboardInterrupt:   # Ctrl+C was pressed
        print('Ok, bye.')

if __name__ == "__main__":
    main()
