'''
This file contains the different modes that can be selected to be used on the controller.
Each mode is a class that inherits from ModeBase.
    It can overrides the functions activate, deactivate, poll and animate.

To avoid multiple screen refresh - the modules should not clean-up the display upon deactivation
Instead, each module is supposed to set at least the area corresponding to each button.
If a button is not used, it should be set to a blank icon and no key assignment should be made.
'''

import time
from threading import Timer
from math import ceil, floor
from colorsys import hsv_to_rgb

# pylint: disable=import-error
import pulsectl                 # Get volume level in Linux, pip3 install pulsectl

from PIL import Image, ImageDraw, ImageFont
from inkkeys import *
from mqtt import InkkeysMqtt

class ModeBase:
    '''
    A template class
    '''
    # pylint: disable=unused-argument
    def activate(self, device: Device):
        '''
        Called when the mode becomes active.
        Usually used to set up static key assignment and icons
        '''
        pass

    def deactivate(self, device: Device):
        '''
        Called when the mode becomes inactive.
        Usually used to clean up and remove callbacks.
        '''
        # Remove callbacks before switching to a different mode
        device.clear_callbacks()

    # pylint: disable=unused-argument
    def poll(self, device: Device):
        '''
        Called periodically and typically used to poll a state which you need to monitor.
        The return value is the time in seconds until the next poll, or False if no polling is required.
        '''
        return False

    def animate(self, device: Device):
        '''
        Called up to 30 times per second, used for LED animation
        '''
        # If no LED animation is used by the mode, "fade_leds" will clear the LEDs from the previous mode
        device.fade_leds()


class ModeBlender (ModeBase):
    '''
    Simple example. For Blender we just set up a few key assignments with corresponding images.
    '''
    def activate(self, device: Device):
        device.send_text_for("title", "Blender", inverted=True) #Title

        #Button1 (Jog dial press)
        device.send_text_for(1, "<   Play/Pause   >")
        device.assign_key(KeyCode.SW1_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_SPACE, ActionCode.PRESS)]) #Play/pause
        device.assign_key(KeyCode.SW1_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_SPACE, ActionCode.RELEASE)])

        #Jog dial rotation
        device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_RIGHT)]) #CW = Clock-wise, one frame forward
        device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT)]) #CCW = Counter clock-wise, one frame back

        #Button2 (top left)
        device.send_icon_for(2, "icons/camera-reels.png")
        device.assign_key(KeyCode.SW2_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_0, ActionCode.PRESS)]) #Set view to camera
        device.assign_key(KeyCode.SW2_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_0, ActionCode.RELEASE)])

        #Button3 (left, second from top)
        device.send_icon_for(3, "icons/person-bounding-box.png")
        device.assign_key(KeyCode.SW3_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_DIVIDE, ActionCode.PRESS)]) #Isolation view
        device.assign_key(KeyCode.SW3_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_DIVIDE, ActionCode.RELEASE)])

        #Button4 (left, third from top)
        device.send_icon_for(4, "icons/dot.png")
        device.assign_key(KeyCode.SW4_PRESS, []) #Not used, set to nothing.
        device.assign_key(KeyCode.SW4_RELEASE, [])

        #Button5 (bottom left)
        device.send_icon_for(5, "icons/dot.png")
        device.assign_key(KeyCode.SW5_PRESS, []) #Not used, set to nothing.
        device.assign_key(KeyCode.SW5_RELEASE, [])

        #Button6 (top right)
        device.send_icon_for(6, "icons/aspect-ratio.png")
        device.assign_key(KeyCode.SW6_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_DOT, ActionCode.PRESS)]) #Center on selection
        device.assign_key(KeyCode.SW6_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEYPAD_DOT, ActionCode.RELEASE)])

        #Button7 (right, second from top)
        #Button4 (left, third from top)
        device.send_icon_for(7, "icons/collection.png")
        device.assign_key(KeyCode.SW7_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_F12), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.RELEASE)]) #Render sequence
        device.assign_key(KeyCode.SW7_RELEASE, [])

        #Button8 (right, third from top)
        device.send_icon_for(8, "icons/dot.png")
        device.assign_key(KeyCode.SW8_PRESS, []) #Not used, set to nothing.
        device.assign_key(KeyCode.SW8_RELEASE, [])

        #Button9 (bottom right)
        device.send_icon_for(9, "icons/dot.png")
        device.assign_key(KeyCode.SW9_PRESS, []) #Not used, set to nothing.
        device.assign_key(KeyCode.SW9_RELEASE, [])

        device.update_display()


class ModeZoom (ModeBase):
    jog_function = ""    # Keeps track of the currently selected function of the jog dial

    def activate(self, device: Device):
        device.send_text_for("title", "Zoom", inverted=True)  # Title

        # Button2 (top left) END MEETING
        device.send_icon_for(2, "icons/arrow-up-left-circle.png")
        device.assign_key(KeyCode.SW2_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_Q, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW2_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_Q, ActionCode.RELEASE)])

        # Button3 (left, second from top)
        device.send_icon_for(3, "icons/camera-video.png")
        device.assign_key(KeyCode.SW3_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_V, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW3_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_V, ActionCode.RELEASE)])

        # Button4 (left, third from top)
        device.send_icon_for(4, "icons/white.png")
        device.assign_key(KeyCode.SW4_PRESS, [])
        device.assign_key(KeyCode.SW4_RELEASE, [])

        # Button5 (bottom left)
        device.send_icon_for(5, "icons/white.png")
        device.assign_key(KeyCode.SW5_PRESS, [])
        device.assign_key(KeyCode.SW5_RELEASE, [])

        # Button6 (top right) MUTE
        device.send_icon_for(6, "icons/mic.png")
        device.assign_key(KeyCode.SW6_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_A, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW6_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_A, ActionCode.RELEASE)])

        # Button7 (right, second from top) SHARE
        device.send_icon_for(7, "icons/aspect-ratio.png")
        device.assign_key(KeyCode.SW7_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_S, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW7_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_S, ActionCode.RELEASE)])

        # Button8 (right, third from top) CHAT
        device.send_icon_for(8, "icons/chat-dots.png")
        device.assign_key(KeyCode.SW8_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_H, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW8_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_H, ActionCode.RELEASE)])

        # Button9 (bottom right) PAUSE SHARE
        device.send_icon_for(9, "icons/aspect-ratio-fill.png")
        device.assign_key(KeyCode.SW9_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_T, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW9_RELEASE, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_T, ActionCode.RELEASE)])

        device.update_display()


class ModeGimp (ModeBase):
    '''
    The Gimp example is similar to Blender, but we add a callback to pressing the jog dial to switch functions
    '''

    # Keeps track of the currently selected function of the jog dial
    jog_function = ""

    def activate(self, device: Device):
        device.send_text_for("title", "Gimp", inverted=True)  #Title

        # Button2 (top left)
        device.send_icon_for(2, "icons/fullscreen.png")
        # Cut to selection (this shortcut appears to be language dependent, so you will probably need to change it)
        device.assign_key(KeyCode.SW2_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_B), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_Z)])
        device.assign_key(KeyCode.SW2_RELEASE, [])

        # Button3 (left, second from top)
        device.send_icon_for(3, "icons/upc-scan.png")
        # Cut to content (this shortcut appears to be language dependent, so you will probably need to change it)
        device.assign_key(KeyCode.SW3_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_B), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_I)])
        device.assign_key(KeyCode.SW3_RELEASE, [])

        # Button4 (left, third from top)
        device.send_icon_for(4, "icons/crop.png")
        # Canvas size (this shortcut appears to be language dependent, so you will probably need to change it)
        device.assign_key(KeyCode.SW4_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_B), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_L)])
        device.assign_key(KeyCode.SW4_RELEASE, [])

        # Button5 (bottom left)
        device.send_icon_for(5, "icons/arrows-angle-expand.png")
        # Resize (this shortcut appears to be language dependent, so you will probably need to change it)
        device.assign_key(KeyCode.SW5_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_B), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_ALT, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_S)])
        device.assign_key(KeyCode.SW5_RELEASE, [])

        # Button6 (top right)
        device.send_icon_for(6, "icons/clipboard-plus.png")
        # Paste as new image
        device.assign_key(KeyCode.SW6_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_V), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.RELEASE)])
        device.assign_key(KeyCode.SW6_RELEASE, [])

        # Button7 (right, second from top)
        device.send_icon_for(7, "icons/layers-half.png")
        # New layer
        device.assign_key(KeyCode.SW7_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_N), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.RELEASE)])
        device.assign_key(KeyCode.SW7_RELEASE, [])

        # Button8 (right, third from top)
        device.send_icon_for(8, "icons/arrows-fullscreen.png")
        # Zoom to fill screen
        device.assign_key(KeyCode.SW8_PRESS, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_J), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_CTRL, ActionCode.RELEASE), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.RELEASE)])
        device.assign_key(KeyCode.SW8_RELEASE, [])

        # Button9 (bottom right)
        device.send_icon_for(9, "icons/dot.png")
        device.assign_key(KeyCode.SW9_PRESS, []) # Not used, set to nothing.
        device.assign_key(KeyCode.SW9_RELEASE, [])


        self.jog_function = ""

        # This toggles the jog function and sets up key assignments and the label for the jog dial. It calls "updateDiplay()" if update is not explicitly set to False (for example if you need to update more parts of the display before updating it.)
        def toggle_jog_function(update=True):
            if self.jog_function == "size":  # Tool opacity in GIMP
                device.clear_callback(KeyCode.JOG)
                device.send_text_for(1, "Tool opacity")
                device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_COMMA), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.RELEASE)])
                device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.PRESS), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_PERIOD), event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_SHIFT, ActionCode.RELEASE)])
                self.jog_function = "opacity"
            else:                            # Tool size in GIMP
                device.clear_callback(KeyCode.JOG)
                device.send_text_for(1, "Tool size")
                device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT_BRACE)])
                device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_RIGHT_BRACE)])
                self.jog_function = "size"

            if update:
                device.update_display()


        # Button 1 / jog dial press
        device.register_callback(toggle_jog_function, KeyCode.JOG_PRESS) # set up the callback for the jog dial press
        device.assign_key(KeyCode.SW1_PRESS, [])                         # clear the key assignment for the button
        device.assign_key(KeyCode.SW1_RELEASE, [])
        toggle_jog_function(False)      # call toggle_jog_function to set the initilal label and assignment
        device.update_display()          # refresh the display


class ModeFallback (ModeBase):
    '''
    This mode is used as a fallback and a much more complex example than Gimp.
    It also uses a switchable Jog dial but most of its functions give a feedback via LED.
    Also, we use MQTT (via a separately defined class) to get data from a CO2 sensor and control a light (both including feedback)
    '''

    def __init__(self, mqtt: InkkeysMqtt = None):
        self.mqtt = mqtt
        self.jog_function = ""      # current function of the jog dial
        self.light_state = None      # current state of the light in my office
        self.is_demo_active = False     # demo mode active or not

    def activate(self, device: Device):
        device.send_text_for("title", "Default", inverted=True) # Title

        ### Buttons 2, 3, 6 and 7 are media controls ###
        device.send_icon_for(2, "icons/play.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW2_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_PLAY_PAUSE, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW2_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_PLAY_PAUSE, ActionCode.RELEASE)])
        device.send_icon_for(3, "icons/skip-start.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW3_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_PREV, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW3_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_PREV, ActionCode.RELEASE)])

        device.send_icon_for(6, "icons/stop.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW6_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_STOP, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW6_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_STOP, ActionCode.RELEASE)])
        device.send_icon_for(7, "icons/skip-end.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW7_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_NEXT, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW7_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_NEXT, ActionCode.RELEASE)])

        ### Buttons 5 and 9 are shortcuts to applications ###
        device.send_icon_for(5, "icons/envelope.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW5_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.CONSUMER_EMAIL_READER, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW5_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.CONSUMER_EMAIL_READER, ActionCode.RELEASE)])
        device.send_icon_for(9, "icons/calculator.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW9_PRESS, [event(DeviceCode.CONSUMER, ConsumerKeycode.CONSUMER_CALCULATOR, ActionCode.PRESS)])
        device.assign_key(KeyCode.SW9_RELEASE, [event(DeviceCode.CONSUMER, ConsumerKeycode.CONSUMER_CALCULATOR, ActionCode.RELEASE)])

        ### Button 4 controls the light in my office and displays its state ###
        def toggle_light():
            target = not self.light_state
            self.mqtt.set_lights(target)
            self.light_state = target
            self.show_light_state(device)

        self.light_state = self.mqtt.get_lights
        self.show_light_state(device, False)

        device.assign_key(KeyCode.SW4_PRESS, [])
        device.assign_key(KeyCode.SW4_RELEASE, [])
        device.register_callback(toggle_light, KeyCode.SW4_PRESS)

        ### Button 8 set display and LEDs to a demo state (only used for videos and pictures of the thing)
        def toggle_demo():
            if self.is_demo_active:
                self.is_demo_active = False
                img = Image.new("1", (device.display_width, device.display_height), color=1)
                device.send_image(0, 0, img)
                self.activate(device) #Recreate the screen content after the demo
            else:
                self.is_demo_active = True
                self.activate(device) #Recreate the screen because with demo active, the buttons will align differently to give room for "there.oughta.be"
                text = "there.oughta.be/a/macro-keyboard"
                font = ImageFont.truetype("arial.ttf", 17)
                w, h = font.getsize(text)
                x = (device.display_width-h)//2
                x8 = floor(x / 8) * 8 #needs to be a multiple of 8
                h8 = ceil((h + x - x8) / 8) * 8 #needs to be a multiple of 8
                img = Image.new("1", (w, h8), color=1)
                d = ImageDraw.Draw(img)
                d.text((0, x-x8), text, font=font, fill=0)
                device.send_image(x8, (device.display_height-w)//2, img.transpose(Image.ROTATE_90))
                device.update_display(True)

        device.register_callback(toggle_demo, KeyCode.SW8_PRESS)
        device.send_icon_for(8, "icons/emoji-sunglasses.png", centered=not self.is_demo_active)
        device.assign_key(KeyCode.SW8_PRESS, [])
        device.assign_key(KeyCode.SW8_RELEASE, [])

        ### The jog wheel can be pressed to switch between three functions: Volume control, mouse wheel, arrow keys left/right ###
        def show_volume(n):
            with pulsectl.Pulse('inkkeys') as pulse:
                sinkList = pulse.sink_list()
                name = pulse.server_info().default_sink_name
                for sink in sinkList:
                    if sink.name == name:
                        vol = sink.volume.value_flat
                off = 0x00ff00
                on = 0xff0000
                leds = [on if vol > i/(device.num_of_leds-1) else off for i in range(device.num_of_leds)]
                device.set_leds(leds)

        self.jog_function = ""

        def toggle_jog_function(update=True):
            if self.jog_function == "wheel":
                device.clear_callback(KeyCode.JOG)
                device.send_text_for(1, "Arrow Keys")
                device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_RIGHT)])
                device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.KEYBOARD, KeyboardKeycode.KEY_LEFT)])
                self.jog_function = "arrow"
            elif self.jog_function == "arrow":
                device.send_text_for(1, "Volume")
                device.register_callback(show_volume, KeyCode.JOG)
                device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_VOL_UP)])
                device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.CONSUMER, ConsumerKeycode.MEDIA_VOL_DOWN)])
                self.jog_function = "volume"
            else:
                device.clear_callback(KeyCode.JOG)
                device.send_text_for(1, "Mouse Wheel")
                device.assign_key(KeyCode.JOG_CW, [event(DeviceCode.MOUSE, MouseAxisCode.MOUSE_WHEEL, 1)])
                device.assign_key(KeyCode.JOG_CCW, [event(DeviceCode.MOUSE, MouseAxisCode.MOUSE_WHEEL, -1)])
                self.jog_function = "wheel"

            if update:
                device.update_display()

        device.register_callback(toggle_jog_function, KeyCode.JOG_PRESS)
        device.assign_key(KeyCode.SW1_PRESS, [])
        device.assign_key(KeyCode.SW1_RELEASE, [])
        toggle_jog_function(False)

        ### All set, let's update the display ###
        device.update_display()

    def poll(self, device: Device):
        if not self.is_demo_active:
            co2 = self.mqtt.get_co2()
            if co2 is not None and co2 > 1000:
                leds = [0x0000ff for i in range(device.num_of_leds)]
                device.set_leds(leds)
            light = self.mqtt.get_lights()
            if light != self.light_state:
                self.light_state = light
                self.show_light_state(device)
        # Return the time in seconds until the next poll
        # This is not a real poll but a reaction to the MQTT messages
        return 10

    # Called to update the icon of button 4, showing the state of the office light
    def show_light_state(self, device: Device, update=True):
        if self.light_state:
            device.send_icon_for(4, "icons/lightbulb.png", centered=not self.is_demo_active)
        else:
            device.send_icon_for(4, "icons/lightbulb-off.png", centered=not self.is_demo_active)
        if update:
            device.update_display()

    def animate(self, device: Device):
        if self.is_demo_active: # Set LEDs animation in demo mode
            def rgbTupleToInt(rgb):
                return (int(rgb[0]*255) << 16) | (int(rgb[1]*255) << 8) | int(rgb[2]*255)

            t = time.time()
            leds = [rgbTupleToInt(hsv_to_rgb(t + i/device.num_of_leds, 1, 1)) for i in range(device.num_of_leds)]
            device.set_leds(leds)
        else:               # Otherwise call "fade_leds" to create a fade animation for any color set anywhere in this mode
            device.fade_leds()


class ModeOBS (ModeBase):
    '''
    One of the most complex examples. This controls OBS scenes and gives feedback about the current state.
    For this we use the websocket plugin and address scenes and sources by their names.
    So, you need to adapt these to your setup.
    We subscribe to OBS events and show the status on the key and LEDs.
    '''
    ws = None           # Websocket instance
    currentScene = None # Keep track of current scene

    # Scenes assigned to buttons with respective icons.
    scenes = [\
                {"name": "Moderation", "icon": "icons/card-image.png", "button": 2}, \
                {"name": "Closeup", "icon": "icons/person-square.png", "button": 3}, \
                {"name": "Slides", "icon": "icons/easel.png", "button": 4}, \
                {"name": "Video-Mute", "icon": "icons/camera-video-off.png", "button": 5}, \
             ]

    # State of sources within scenes. "items" is an array of scene/item combinations to keep track of items that need to be switched on multiple scenes simultaneously, so you can mute all mics in all scenes and switch scenes without an unpleasant surprise. The current state is tracked in this object ("current")
    states = [\
                {"items": [("Moderation", "Phone"), ("Closeup", "Phone"), ("Slides", "Phone")], "icon": "icons/phone.png", "button": 7, "current": True}, \
                {"items": [("Slides", "Cam: Closeup")], "icon": "icons/pip.png", "button": 8, "current": True}, \
                {"items": [("Moderation", "Mic: Moderation"), ("Closeup", "Mic: Closeup"), ("Slides", "Mic: Closeup")], "icon": "icons/mic.png", "button": 9, "current": True}, \
             ]

    # Switch to scene with name "name"
    def setScene(self, name):
        self.ws.call(requests.SetCurrentScene(name))

    # Toggle source visibility as defined in a state (see states above)
    def toggleState(self, state):
        visible = not state["current"]
        for item in state["items"]:
            self.ws.call(requests.SetSceneItemProperties(item[1], scene_name=item[0], visible=visible))

    # Generates a callback function which in turn calls "setScene" with the fixed scene "name" without requiring a parameter
    def getSetSceneCallback(self, name):
        return lambda: self.setScene(name)

    # Generates a callback function which in turn calls "toggleState" with a fixed "state" object without requiting a parameter
    def getToggleStateCallback(self, state):
        return lambda: self.toggleState(state)

    # Updates the buttons associated with scenes. Unless "init" is set to true, it only updates changed parts of the display and returns True if anything has changed so that the calling function should call updateDisplay()
    def updateSceneButtons(self, device, newScene, init=False):
        if self.currentScene == newScene:
            return False
        for scene in self.scenes:
            if (init and newScene != scene["name"]) or self.currentScene == scene["name"]:
                device.sendIconFor(scene["button"], scene["icon"], centered=True)
            elif newScene == scene["name"]:
                device.sendIconFor(scene["button"], scene["icon"], centered=True, marked=True)
        self.currentScene = newScene
        return True

    # Updates the buttons associated with states. Unless "init" is set to true, it only updates changed parts of the display and returns True if anything has changed so that the calling function should call updateDisplay()
    def updateStateButtons(self, device, scene, item, visible, init=False):
        anyUpdate = False
        for state in self.states:
            if init or ((scene, item) in state["items"] and visible != state["current"]):
                device.sendIconFor(state["button"], state["icon"], centered=True, crossed=not (state["current"] if init else visible))
                anyUpdate = True
                if not init:
                    state["current"] = visible
        return anyUpdate

    def updateLED(self, device):
        '''
        Changes the LED color depending on the current scene and the state of the microphones
        '''
        if self.currentScene == "Video-Mute" or self.states[2]["current"] == False:
            leds = [0xff0000 for i in range(device.nLeds)] # Either this is the empty "Video-Mute" scene or the mics are muted -> red
        else:
            leds = [0x00ff00 for i in range(device.nLeds)] # In any other case the mics are live -> green
        device.setLeds(leds)

    def activate(self, device):
        self.ws = obsws("localhost", 4444) # Connect to websockets plugin in OBS

        # Callback if OBS is shutting down
        def on_exit(message):
            self.ws.disconnect()

        # Callback if the scene changes
        def on_scene(message):
            if self.updateSceneButtons(device, message.getSceneName()):
                device.update_display() #Only update if parts of the display actually changed
            self.updateLED(device)

        # Callback if the visibility of a source changes
        def on_visibility_changed(message):
            if self.updateStateButtons(device, message.getSceneName(), message.getItemName(), message.getItemVisible()):
                device.update_display() #Only update if parts of the display actually changed
            self.updateLED(device)

        # Register callbacks to OBS
        self.ws.register(on_exit, events.Exiting)
        self.ws.register(on_scene, events.SwitchScenes)
        self.ws.register(on_visibility_changed, events.SceneItemVisibilityChanged)

        self.ws.connect()
        device.send_text_for("title", "OBS", inverted=True) #Title

        ### Buttons 2 to 5 set different scenes (Moderation, Closeup, Slides and Video Mute) ###
        for scene in self.scenes:
            device.assign_key(KeyCode["SW"+str(scene["button"])+"_PRESS"], [])
            device.assign_key(KeyCode["SW"+str(scene["button"])+"_RELEASE"], [])
            device.register_callback(self.getSetSceneCallback(scene["name"]), KeyCode["SW"+str(scene["button"])+"_PRESS"])



        ### Button 6: Order!
        def stopOrder():
            self.ws.call(requests.SetSceneItemProperties("Order", visible=False))

        def playOrder():
            self.ws.call(requests.SetSceneItemProperties("Order", visible=True))
            Timer(3, stopOrder).start()


        device.assign_key(KeyCode["SW6_PRESS"], [])
        device.assign_key(KeyCode["SW6_RELEASE"], [])
        device.register_callback(playOrder, KeyCode["SW6_PRESS"])
        device.send_icon_for(6, "icons/megaphone.png", centered=True)


        ### Buttons 7 to 9 toogle the visibility of items, some of which are present in multiple scenes (Mics, Picture-In-Picture cam, Video stream from phone) ###
        for state in self.states:
            device.assign_key(KeyCode["SW"+str(state["button"])+"_PRESS"], [])
            device.assign_key(KeyCode["SW"+str(state["button"])+"_RELEASE"], [])
            device.register_callback(self.getToggleStateCallback(state), KeyCode["SW"+str(state["button"])+"_PRESS"])

        ### Get current state and initialize buttons accordingly ###
        current = self.ws.call(requests.GetSceneList())
        for scene in current.getScenes():
            for item in scene["sources"]:
                for state in self.states:
                    if (scene["name"], item["name"]) in state["items"]:
                        state["current"] = item["render"]

        #Call updateSceneButtons and updateStateButtons to initialize their images
        self.currentScene = None
        self.updateSceneButtons(device, current.getCurrentScene(), init=True)
        self.updateStateButtons(device, None, None, True, init=True)
        device.update_display()
        self.updateLED(device)

    def animate(self, device):
        pass    #In this mode we want permanent LED illumination. Do not fade or animate otherwise.
