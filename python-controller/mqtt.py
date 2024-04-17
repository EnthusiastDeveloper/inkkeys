#!/usr/bin/env python3

'''
Specialized class to handle MQTT communication.
This class is used by the main controller to communicate with an MQTT server.
'''

import json
# pylint: disable=import-error
import paho.mqtt.client as mqtt

class InkkeysMqtt:
    '''
    Class to handle MQTT communication.
    '''
    def __init__(self, server, debug=False):
        self.client = mqtt.Client("inkkeys")
        self.server = server
        self.debug = debug

        self.is_lights_on = False
        self.lights_mqtt_topic = "zigbee2mqtt_octopi/plug_office"

        self.co2 = 0
        self.co2_mqtt_topic = "co2/data/update"

        def on_message(client, userdata, message):
            if message.topic == self.lights_mqtt_topic:
                state = json.loads(str(message.payload.decode("utf-8")))
                self.is_lights_on = state["state"] != "OFF"
                if self.debug:
                    print("Light: " + str(self.is_lights_on))
            elif message.topic == self.co2_mqtt_topic:
                state = json.loads(str(message.payload.decode("utf-8")))
                self.co2 = state["co2"]
                if self.debug:
                    print("CO2: " + str(self.co2))

        self.client.on_message = on_message

    def connect(self):
        '''
        Connect to the MQTT server and subscribe to the topics.
        '''
        if self.server is None:
            return
        self.client.connect(self.server)
        self.client.loop_start()
        self.client.subscribe(self.lights_mqtt_topic)
        self.client.subscribe(self.co2_mqtt_topic)
        self.client.publish(self.lights_mqtt_topic + "/get",'{"state":""}')

    def disconnect(self):
        '''
        Disconnect from the MQTT server.
        This should be called before the program exits.
        '''
        if self.server is None:
            return
        self.client.loop_stop()
        self.client.disconnect()

    def set_lights(self, state):
        '''
        Set the state of the lights.
        '''
        if self.server is None:
            return
        self.client.publish(self.lights_mqtt_topic + "/set",'{"state":' + ('"ON"' if state else '"OFF"') + '}')

    def get_lights(self):
        '''
        Get the state of the lights.
        '''
        return self.is_lights_on if self.server is not None else None

    def get_co2(self):
        ''''
        Get the CO2 level.
        '''
        return self.co2 if self.server is not None else None
