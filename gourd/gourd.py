import atexit
import logging
import re
from os import environ
from socket import gethostname

import paho.mqtt.client

from .mqtt_wildcard import mqtt_wildcard


class Gourd:
    def __init__(self, app_name, *, mqtt_host='localhost', mqtt_port=1883, mqtt_user='', mqtt_pass='', mqtt_qos=1, timeout=30, status_topic=None, status_online='ON', status_offline='OFF'):
        self.name = app_name
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_pass = mqtt_pass
        self.mqtt_qos = mqtt_qos
        self.mqtt_topics = {}
        self.timeout = timeout

        # Setup the status topic
        self.status_topic = status_topic
        self.status_online = status_online
        self.status_offline = status_offline

        if not self.status_topic:
            self.status_topic = f'{app_name}/{gethostname()}/status'

        # Setup logging
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

        # Setup MQTT
        self.mqtt = paho.mqtt.client.Client()
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_log = self.on_log
        self.mqtt.on_message = self.on_message
        self.mqtt.will_set(self.status_topic, payload=self.status_offline, qos=1, retain=True)
        self.publish = self.mqtt.publish
        atexit.register(self.on_exit)

    def connect(self):
        """Connect to the MQTT server.
        """
        self.mqtt.connect(self.mqtt_host, self.mqtt_port, self.timeout)

    def subscribe(self, topic):
        """Decorator that registers a function to be called whenever a message for a topic is sent.
        """
        def inner_function(handler):
            if topic not in self.mqtt_topics:
                self.mqtt_topics[topic] = []

            if handler not in self.mqtt_topics[topic]:
                self.mqtt_topics[topic].append(handler)

            return handler

        return inner_function

    def do_subscribe(self):
        """Subscribe to our topics.
        """
        for topic in self.mqtt_topics:
            self.mqtt.subscribe(topic)

    def on_connect(self, client, userdata, flags, rc):
        """Called when an MQTT server connection is established.
        """
        self.log.info("MQTT connected: " + paho.mqtt.client.connack_string(rc))
        if rc != 0:
            cli.log.error("Could not connect. Error: " + str(rc))
        else:
            self.mqtt.publish(self.status_topic, payload=self.status_online, qos=1, retain=True)
            self.do_subscribe()

    def on_disconnect(self, client, userdata, flags, rc):
        """Called when an MQTT server is disconnected.
        """
        self.log.error("MQTT disconnected: " + paho.mqtt.client.connack_string(rc))

    def on_exit(self):
        """Called when exiting to ensure we cleanup and disconnect cleanly.
        """
        self.mqtt.publish(self.status_topic, payload=self.status_offline, qos=1, retain=True)
        self.mqtt.disconnect()

    def on_log(self, mqtt, obj, level, string):
        """Called when paho has a log message to enable.
l       """
        if level < 16:
            self.log.error(string)
        else:
            self.log.debug(string)

    def on_message(self, client, userdata, msg):
        """Called when paho has a message from the queue to process.
        """
        self.log.info('Got a message for', msg.topic, 'content:', msg.payload)
        for topic, funcs in self.mqtt_topics.items():
            if mqtt_wildcard(msg.topic, topic):
                for func in funcs:
                    func(msg)

    def run_forever(self):
        """Run the program until forcibly quit.
        """
        try:
            self.connect()
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            pass
