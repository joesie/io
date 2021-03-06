
from datetime import datetime
from typing import ClassVar
import RPi.GPIO as GPIO
import socket
import json

hostname = socket.gethostname()
MQTT_RESPONSE_STATE = hostname + "/gpio/"

class Channel:
    inputChannels = []
    outputChannels = []
    _LOGGER = None
    client = None
    pin = None

    def __init__(self, _LOGGER, client, pin):
        self._LOGGER = _LOGGER
        self.client = client
        self.pin = pin

    #=============================
    ##
    # send MQTT response for given value
    ##
    def send_mqtt_pin_value(self, value):
        now = datetime.now()
        if(value):
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/state" , "1", retain = True)
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/stateText" , "ON", retain = True)
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/timestamp_ON", now.strftime('%Y-%m-%d %H:%M:%S'), retain = True)
            self._LOGGER.debug(now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_RESPONSE_STATE + str(self.pin) + ': ON'))
        else:
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/stateText", "OFF", retain = True)
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/state", "0", retain = True)
            self.client.publish(MQTT_RESPONSE_STATE + str(self.pin) + "/timestamp_OFF", now.strftime('%Y-%m-%d %H:%M:%S'), retain = True)
            self._LOGGER.debug( now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_RESPONSE_STATE + str(self.pin) + ': OFF'))

    #####
    # init all configured GPIOs
    #####
    @staticmethod
    def init(configfile, _LOGGER, client):
        _LOGGER.info("Configure GPIOs")
        try:
            GPIO.setmode(GPIO.BCM)
            with open(configfile) as json_pcfg_file:
                pcfg = json.load(json_pcfg_file)
                _LOGGER.debug("Plugin Config: " + str(pcfg))
                gpio = pcfg['gpio']

                # configure inputs
                inputs = gpio['inputs']
                for i in range(0, int(inputs['count'])):
                    key = "channel_{}".format(i)
                    channel = inputs[key]
                    Channel.inputChannels.append( InputChannel(channel, _LOGGER, client) )

                # configure outputs
                outputs = gpio['outputs']
                for i in range(0, int(outputs['count'])):
                    key = "channel_{}".format(i)
                    channel = outputs[key]
                    Channel.outputChannels.append( OutputChannel(channel, _LOGGER, client) )
                    
        except Exception as e:
            _LOGGER.exception(str(e))

    #####
    # send current pin state
    #####
    def sendState(self):
        value = GPIO.input(self.pin)
        self.send_mqtt_pin_value(value)

    #####
    # send state for all configured channels
    #####
    @staticmethod
    def sendChannelStates():
        for channel in Channel.inputChannels:
            channel.sendState()

        for channel in Channel.outputChannels:
            channel.sendState()    




class InputChannel(Channel):

    ##
    # Callback function for interrupt handling
    ##
    def callback_input(self, channel):
        now = datetime.now()

        if GPIO.input(channel): # if SENSOR_PIN of channel == 1 or high
            self.send_mqtt_pin_value(1)
        else: # if SENSOR_PIN of channel != 1 or low
            self.send_mqtt_pin_value(0)


    def __init__(self, channel, _LOGGER, client):
        Channel.__init__(self, _LOGGER, client, int(channel['pin']))


        wireing = GPIO.PUD_UP
        if channel['wiring'] == 'd':
            wireing = GPIO.PUD_DOWN

        GPIO.setup(int(channel['pin']), GPIO.IN, pull_up_down = wireing)
        GPIO.add_event_detect(int(channel['pin']) , GPIO.BOTH, callback= self.callback_input)
        _LOGGER.info("set Pin " + channel['pin'] + " as Input")    

class OutputChannel(Channel):

    def __init__(self, channel, _LOGGER, client):
        Channel.__init__(self, _LOGGER, client, int(channel['pin']))

        GPIO.setup(int(channel['pin']), GPIO.OUT)
        GPIO.output(int(channel['pin']), GPIO.LOW) #Default GPIO High is off
        _LOGGER.info("set Pin " + channel['pin'] + " as Output")

    ##
    #   handle output command
    ##

    @staticmethod
    def setOutput(channel, value):
        if value == "ON" or value == "1" or value == "on" :
            GPIO.output(int(channel.pin), GPIO.HIGH)
            channel.send_mqtt_pin_value(1)
        if value == "OFF" or value == "0" or value == "off":
            GPIO.output(int(channel.pin), GPIO.LOW)
            channel.send_mqtt_pin_value(0)


    @staticmethod   
    def handle_setOutput(pin, value):
        for channel in Channel.outputChannels:
            if(str(channel.pin) == str(pin)):
                OutputChannel.setOutput(channel, value)
                    