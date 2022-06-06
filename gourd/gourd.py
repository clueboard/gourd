import atexit
import json
import logging
import re
from os import environ
from socket import gethostname

import paho.mqtt.client

from .gourd_message import GourdMessage
from .mqtt_log_handler import MQTTLogHandler
from .mqtt_wildcard import mqtt_wildcard


class Gourd:
    """An opinionated framework for writing MQTT applications.

    Args:
        app_name                    The name of your application (typically used as the base of your mqtt topic(s))
        mqtt_host='localhost'       The MQTT server to connect to
        mqtt_port=1883              The port number to connect to
        username=''                 The username to connect to the MQTT server with
        password=''                 The password to connect to the MQTT server with
        qos=1                       Default QOS Level for messages
        timeout=30                  The timeout for the MQTT connection
        log_mqtt=True               Set to false to disable mqtt logging
        log_topic=None              The MQTT topic to send debug logs to (When None it's f'{app_name}/{gethostname()}/debug')
        status_enabled=True         Set to false to disable the status topic
        status_topic=None           The topic to publish application status (ON/OFF) to (When None it's f'{app_name}/{gethostname()}/status')
        status_online='ON'          The payload to publish to status_topic when we are running
        status_offline='OFF'        The payload to publish to status_topic when we are not running
        max_inflight_messages=20    How many messages can be in-flight. See Paho MQTT documentation for more details.
        max_queued_messages=0       How many messages can be queued at a time. See Paho MQTT documentation for more details.
        message_retry_sec=5         How long to wait before retrying messages. See Paho MQTT documentation for more details.
    """
    def __init__(self, app_name, *, mqtt_host='localhost', mqtt_port=1883, username='', password='', qos=1, timeout=30, log_mqtt=True, log_topic=None, status_enabled=True, status_topic=None, status_online='ON', status_offline='OFF', max_inflight_messages=20, max_queued_messages=0, message_retry_sec=5):
        self.name = app_name
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.username = username
        self.qos = qos
        self.mqtt_topics = {}
        self.timeout = timeout

        # Setup the status topic
        self.status_enabled = status_enabled
        self.status_topic = status_topic
        self.status_online = status_online
        self.status_offline = status_offline

        if not self.status_topic:
            self.status_topic = f'{app_name}/{gethostname()}/status'

        # Setup logging
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

        if not log_topic:
            log_topic = f'{app_name}/{gethostname()}/debug'

        # Setup MQTT
        self.mqtt = paho.mqtt.client.Client()
        self.mqtt.enable_logger(self.log)
        self.mqtt.max_inflight_messages_set(max_inflight_messages)
        self.mqtt.max_queued_messages_set(max_queued_messages)
        self.mqtt.message_retry_set(message_retry_sec)
        self.mqtt.username_pw_set(username, password)

        # Register mqtt callbacks
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message

        if self.status_enabled:
            self.mqtt.will_set(self.status_topic, payload=self.status_offline, qos=1, retain=True)

        # Setup MQTT logging
        self.mqtt_log_handler = None
        if log_mqtt:
            self.mqtt_log_handler = MQTTLogHandler(mqtt_client=self.mqtt, topic=log_topic, qos=qos, retain=False)
            self.mqtt_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))
            self.log.addHandler(self.mqtt_log_handler)

        # Register handlers
        atexit.register(self.on_exit)

    def publish(self, topic, payload=None, *, qos=None, **kwargs):
        """Publish a message to the MQTT server.
        """
        if qos is None:
            qos = self.qos

        self.mqtt.publish(topic, payload, qos=qos, **kwargs)

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
        self.log.info("MQTT connected: %s", paho.mqtt.client.connack_string(rc))
        if rc != 0:
            cli.log.error("Could not connect. Error: " + str(rc))
        else:
            if self.status_enabled:
                self.mqtt.publish(self.status_topic, payload=self.status_online, qos=1, retain=True)
            self.do_subscribe()

    def on_disconnect(self, client, userdata, flags, rc=None):
        """Called when an MQTT server is disconnected.
        """
        self.log.error("MQTT disconnected: %s", paho.mqtt.client.connack_string(rc))

    def on_exit(self):
        """Called when exiting to ensure we cleanup and disconnect cleanly.
        """
        if self.status_enabled:
            self.mqtt.publish(self.status_topic, payload=self.status_offline, qos=1, retain=True)
        self.mqtt.disconnect()

    def on_message(self, client, userdata, msg):
        """Called when paho has a message from the queue to process.
        """
        self.log.info('Got a message for topic:%s payload:%s', msg.topic, msg.payload)

        for topic, funcs in self.mqtt_topics.items():
            if mqtt_wildcard(msg.topic, topic):
                for func in funcs:
                    func(GourdMessage(msg))

    def run_forever(self):
        """Run the program until forcibly quit.
        """
        try:
            self.connect()
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            self.log.error('User interrupted with ^C...')
