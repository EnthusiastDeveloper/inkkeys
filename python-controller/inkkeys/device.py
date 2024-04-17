#!/usr/bin/env python3

import time
import io
from threading import Lock

from PIL import Image, ImageDraw, ImageOps, ImageFont
# pylint: disable=import-error
from serial import Serial, SerialException  # Serial functions

from .protocol import *

CHUNK_SIZE = 100

class Device:
    def __init__(self):
        self.debug = True
        self.testmode = False

        self.ser = None
        self.inbuffer = ""
        self.awaiting_response_lock = Lock()
        self.num_of_leds = 0
        self.display_width = 0
        self.display_height = 0
        self.rotation_factor = 0
        self.rotation_circle_steps = 0
        self.banner_height = 20  # Defines the height of top and bottom banner
        self.image_buffer = []
        self.callbacks = {}     # Stores callback functions that react directly to a keypress reported via serial
        self.led_state = None
        self.led_set_time = None
        self.status = False

    def connect(self, dev):
        '''
        Connect to the device on the given port.
        '''
        print(f'Connecting to {dev}.')
        self.ser = Serial(dev, 115200, timeout=1, write_timeout=5)
        if not self.request_info(3):
            self.disconnect()
            return False
        if self.testmode:
            print(f'Connection to {self.ser.name} was successfull, but the device is running the hardware test firmware, which cannot be used for anything but testing. Please flash the proper inkkeys firmware to use it.')
            return False
        print(f'Connected to {self.ser.name}.')
        return True

    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def send_to_device(self, command: str):
        if self.debug:
            print(f'Sending: {command}')
        self.ser.write((command + "\n").encode())

    def send_binary_to_device(self, data):
        if self.debug:
            print(f'Sending {len(data)} bytes of binary data.')
        try:
            # Send binary data in chunks to prevent killing the serial connection
            endIx = CHUNK_SIZE
            startIx = 0
            while startIx < len(data):
                self.ser.write(data[startIx:endIx])
                #if self.debug:
                #    print(data[startIx:endIx].hex())
                startIx = startIx + CHUNK_SIZE
                endIx = endIx + CHUNK_SIZE
            if self.debug:
                print('Data sent.')
        except SerialException as e:
            print("Serial error: ", e)

    def read_from_device(self):
        if self.ser.in_waiting > 0:
            self.inbuffer += self.ser.read(self.ser.in_waiting).decode('ISO-8859-16').replace('\r', '')
        chunks = self.inbuffer.split("\n", 1)
        if len(chunks) > 1:
            cmd = chunks[0]
            self.inbuffer = chunks[1]
            if self.debug:
                print(f'Received: {cmd}')
            return cmd
        return None

    def poll(self):
        with self.awaiting_response_lock:
            input = self.read_from_device()
        if input is not None:
            if input[0] == KeyCode.JOG.value and (input[1:].isdecimal() or (input[1] == '-' and input[2:].isdecimal())):
                if KeyCode.JOG.value in self.callbacks:
                    self.callbacks[KeyCode.JOG.value](int(input[1:]))
            elif input in self.callbacks:
                self.callbacks[input]()

    def register_callback(self, cb, key):
        self.callbacks[key.value] = cb

    def clear_callback(self, key):
        if key.value in self.callbacks:
            del self.callbacks[key.value]

    def clear_callbacks(self):
        self.callbacks = {}

    def assign_key(self, key, sequence):
        self.send_to_device(CommandCode.ASSIGN.value + " " + key.value + (" " + " ".join(sequence) if len(sequence) > 0 else ""))

    def send_led(self, colors):
        self.send_to_device(CommandCode.LED.value + " " + " ".join(colors))

    def send_led_animation(self, animation, steps, delay=0, brightness=0, r=0, g=0, b=0, iteration=1):
        self.send_to_device(f"{CommandCode.ANIMATE.value} {animation} {steps} {delay} {brightness} {r} {g} {b} {iteration}")

    def request_info(self, timeout):
        with self.awaiting_response_lock:
            print('Requesting device info...')
            start = time.time()
            self.send_to_device(CommandCode.INFO.value)
            line = self.read_from_device()
            while line != "Inkkeys":
                if time.time() - start > timeout:
                    return False
                if line is None:
                    time.sleep(0.1)
                    line = self.read_from_device()
                    continue
                print(f'Skipping: {line}')
                line = self.read_from_device()
            print('Header found. Waiting for infos...')
            line = self.read_from_device()
            while line != 'Done':
                if time.time() - start > timeout:
                    return False
                if line is None:
                    time.sleep(0.1)
                    line = self.read_from_device()
                    continue
                if line.startswith('TEST '):
                    self.testmode = line[5] != '0'
                elif line.startswith('N_LED '):
                    self.num_of_leds = int(line[6:])
                elif line.startswith('DISP_W '):
                    self.display_width = int(line[7:])
                elif line.startswith('DISP_H '):
                    self.display_height = int(line[7:])
                elif line.startswith('ROT_CIRCLE_STEPS '):
                    self.rotation_circle_steps = int(line[17:])
                else:
                    print(f'Skipping: {line}')
                line = self.read_from_device()
            print('End of info received.')
            print(f'Testmode: {self.testmode}')
            print(f'Number of LEDs: {self.num_of_leds}')
            print(f'Display width: {self.display_width}')
            print(f'Display height: {self.display_height}')
            print(f'Rotation circle steps: {self.rotation_circle_steps}')
            return True

    def send_image(self, x, y, image):
        '''
        Send an image to the controller to be displayed on the screen.
        '''
        if self.debug:
            print(f"send_image({x}, {y})")
        self.image_buffer.append({"x": x, "y": y, "image": image.copy()})
        w, h = image.size
        data = image.convert("1").rotate(180).tobytes()
        self.send_to_device(CommandCode.DISPLAY.value + " " + str(x) + " " + str(y) + " " + str(w) + " " + str(h))
        self.send_binary_to_device(data)
        return True

    def resend_image_data(self):
        '''
        Resend all of the image data from the buffer to buffer in the display.
        '''
        if self.debug:
            print('resend_image_data()')
        for part in self.image_buffer:
            image = part['image']
            x = part['x']
            y = part['y']
            w, h = image.size
            data = image.convert('1').rotate(180).tobytes()
            self.send_to_device(CommandCode.DISPLAY.value + " " + str(x) + " " + str(y) + " " + str(w) + " " + str(h))
            self.send_binary_to_device(data)
        self.image_buffer = []

    def reset_display(self):
        '''
        Reset the display to a blank state.
        '''
        self.send_to_device(CommandCode.REFRESH.value + " " + RefreshTypeCode.RESET.value)

    def update_display(self, full_refresh=True, timeout=5, buffer_data=False):
        '''
        Update the display with the current image buffer.
        '''
        with self.awaiting_response_lock:
            if self.debug:
                print(f'update_display(full_refresh={full_refresh}, timeout={timeout})')
            # Send the refresh command and wait for "ok" response until the timeout is up.
            start = time.time()
            self.send_to_device(CommandCode.REFRESH.value + " " + (RefreshTypeCode.FULL.value if full_refresh else RefreshTypeCode.PARTIAL.value))
            line = self.read_from_device()
            while line != "ok":
                if time.time() - start > timeout:
                    if self.debug:
                        print('Timed out...')
                    return False
                if line == None:
                    time.sleep(0.1)
                    line = self.read_from_device()
                    continue
                line = self.read_from_device()
            # Resend all of the image data from the buffer to buffer in the display
            if buffer_data:
                self.resend_image_data()
                self.send_to_device(CommandCode.REFRESH.value + " " + RefreshTypeCode.OFF.value)
                start = time.time()
                line = self.read_from_device()
                while line != "ok":
                    if time.time() - start > timeout:
                        if self.debug:
                            print('Timed out...')
                        return False
                    if line == None:
                        time.sleep(0.1)
                        line = self.read_from_device()
                        continue
                    line = self.read_from_device()

    def get_area_for(self, function):
        '''
        Get the area of the screen that the image should be displayed in.
        '''
        banner_space = self.banner_height//2  # Each side gives space for half the banner height
        tile_height = self.display_height//4               # Tile height is the screen height divided by 4
        tile_width = (self.display_width//2)-banner_space # Tile width is half the screen minus half the banner height

        if function == "title":
            # TODO: The controler hangs and fails to upddate the display when the title is less than 40 in height
            area = (tile_width, 0, 40, self.display_height)
        elif function == 1:
            # TODO: Decide what to do with button 1 text, if anything.
            area = (0, tile_width, self.display_height, self.display_width//2+self.banner_height)
        elif function <= 5:
            area = (tile_width+(self.banner_height), (5-function)*tile_height, tile_width+2, tile_height)
        else:
            area = (0, (9-function)*tile_height, tile_width+2, tile_height)

        if self.debug:
            x, y, w, h = area
            print(f'Area is {x}/{y} {w}x{h}')
        return area

    # Resize the image if needed and send it to the controller.
    def send_image_for(self, function, image):
        x, y, w, h = self.get_area_for(function)
        if (w, h) != image.size:
            if self.debug:
                print(f'Rescaling image from {image.size} to {w}, {h}.')
            image = image.resize((w, h))
        self.send_image(x, y, image)

    def send_text_for(self, function, text, subtext="", inverted=False):
        if self.debug:
            print(f'send_text_for({function}, {text}, subtext={subtext}, inverted={inverted})')
        _, _, width, height = self.get_area_for(function)
        image = Image.new("1", (width, height), color=(0 if inverted else 1))
        drawing = ImageDraw.Draw(image)
        main_text_font = ImageFont.truetype("font/Munro.ttf", 10)
        left, top, right, bottom = main_text_font.getbbox(text)
        main_text_width = right - left
        main_text_height = bottom - top

        subtext_font = ImageFont.truetype("font/MunroSmall.ttf", 10)
        left, top, right, bottom  = subtext_font.getbbox(subtext)
        subtext_width = right - left
        if function in (1, 'title'):
            # Center jog wheel and title label (the title gets small -0.5 nudge for rounding to prefer a top alignment)
            position1 = ((width-main_text_width)/2, (height-main_text_height-(0.5 if function == "title" else 0))/2)
            position2 = None
        elif function < 6:
            drawing.line([(0, height/2), (main_text_width, height/2)], fill=(1 if inverted else 0))
            position1 = (0, height/2-main_text_height-2) # Align left
            position2 = (0, height/2-1)
            align = 'left'
        else:
            drawing.line([(width, height/2), (width-main_text_width, height/2)], fill=(1 if inverted else 0))
            position1 = (width-main_text_width, height/2-main_text_height-2) # Align right
            position2 = (width-subtext_width, height/2-1)
            align = 'right'
        drawing.text(position1, text, font=main_text_font, fill=(1 if inverted else 0))
        if position2 is not None and subtext is not None:
            drawing.multiline_text(position2, subtext, font=subtext_font, align=align, spacing=-2, fill=(1 if inverted else 0))
        self.send_image_for(function, image)

    def send_icon_for(self, function, icon, inverted=False, centered=True, marked=False, crossed=False):
        if self.debug:
            print(f'send_icon_for({icon}, inverted={inverted}, centered={centered}, marked={marked}, crossed={crossed})')
        x, y, w, h = self.get_area_for(function)
        img = Image.new("1", (w, h), color=(0 if inverted else 1))
        imgIcon = Image.open(icon).convert("RGB")
        if inverted:
            imgIcon = ImageOps.invert(imgIcon)
        wi, hi = imgIcon.size
        if function < 6:
            pos = ((w-wi)//2 if centered else 0, (h - hi)//2)
        else:
            pos = ((w-wi)//2 if centered else (w - wi), (h - hi)//2)
        img.paste(imgIcon, pos)

        if marked:
            imgMarker = Image.open("icons/chevron-compact-right.png" if function < 6 else "icons/chevron-compact-left.png")
            wm, hm = imgMarker.size
            img.paste(imgMarker, (-16,(h - hm)//2) if function < 6 else (w-wm+16,(h - hm)//2), mask=ImageOps.invert(imgMarker.convert("RGB")).convert("1"))

        if crossed:
            d = ImageDraw.Draw(img)
            d.line([pos[0]+5, pos[1]+5, pos[0]+wi-5, pos[1]+hi-5], width=3)
            d.line([pos[0]+5, pos[1]+hi-5, pos[0]+wi-5, pos[1]+5], width=3)

        self.send_image(x, y, img)

    def set_leds(self, leds):
        '''
        Set the LEDs to a specific color.
        '''
        ledStr = [f'{i:06x}' for i in leds]
        self.led_set_time = time.time()
        self.led_state = leds
        self.send_led(ledStr)

    def fade_leds(self):
        if self.led_state == None:
            return
        p = (3.5 - (time.time() - self.led_set_time))/0.5 # Stay on for 3 seconds and then fade out over 0.5 seconds
        if p >= 1:
            return
        if p <= 0:
            self.led_state = None
            self.send_led(["000000" for i in range(self.num_of_leds)])
            return
        dimmed_leds = [(int((i & 0xff0000) * p) & 0xff0000) | (int((i & 0xff00) * p) & 0xff00) | (int((i & 0xff) * p) & 0xff) for i in self.led_state]
        led_str = ['{:06x}'.format(i) for i in dimmed_leds]
        self.send_led(led_str)

    def set_status(self, status):
        self.status = status
        if self.debug:
            print(f'Setting device status to {status}')
