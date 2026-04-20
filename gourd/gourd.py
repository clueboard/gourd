import atexit
import json
import logging
import re
import threading
from os import environ
from socket import gethostname

import paho.mqtt.client
from paho.mqtt.client import CallbackAPIVersion

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
        message_retry_sec=None      Deprecated. Ignored in paho-mqtt v2.
        env_prefix=''               Prefix for environment variables. '' (default) means no prefix (e.g. MQTT_HOST).
                                    Set to a string like 'MY_APP' for prefixed vars (e.g. MY_APP_MQTT_HOST).
                                    Set to None or False to disable env var support.
    """
    _env_settings = {
        'MQTT_HOST': ('mqtt_host', str),
        'MQTT_PORT': ('mqtt_port', int),
        'USERNAME': ('username', str),
        'PASSWORD': ('password', str),
        'QOS': ('qos', int),
        'TIMEOUT': ('timeout', int),
    }

    def __init__(self, app_name, *, mqtt_host='localhost', mqtt_port=1883, username='', password='', qos=1, timeout=30, log_mqtt=True, log_topic=None, status_enabled=True, status_topic=None, status_online='ON', status_offline='OFF', max_inflight_messages=20, max_queued_messages=0, message_retry_sec=None, env_prefix=''):
        if message_retry_sec is not None:
            import warnings
            warnings.warn(
                "message_retry_sec is ignored in paho-mqtt v2 and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.name = app_name

        # Determine the environment variable prefix.
        # '' (default): no prefix, env vars are MQTT_HOST, USERNAME, etc.
        # A non-empty string: prefix env vars, e.g. 'MY_APP' -> MY_APP_MQTT_HOST
        # None/False: disable env var support entirely
        if env_prefix is None or env_prefix is False:
            self.env_prefix = None
        else:
            self.env_prefix = str(env_prefix)

        # Apply environment variable overrides.
        if self.env_prefix is not None:
            env_overrides = self._env_overrides()
            mqtt_host = env_overrides.get('mqtt_host', mqtt_host)
            mqtt_port = env_overrides.get('mqtt_port', mqtt_port)
            username = env_overrides.get('username', username)
            password = env_overrides.get('password', password)
            qos = env_overrides.get('qos', qos)
            timeout = env_overrides.get('timeout', timeout)

        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.username = username
        self.qos = qos
        self.mqtt_topics = {}
        self.timeout = timeout
        self.thread_funcs = []

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
        self.mqtt = paho.mqtt.client.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        paho_log = logging.getLogger(__name__ + '.paho')
        paho_log.propagate = False
        self.mqtt.enable_logger(paho_log)
        self.mqtt.max_inflight_messages_set(max_inflight_messages)
        self.mqtt.max_queued_messages_set(max_queued_messages)
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

    def thread(self, *args, **kwargs):
        """Decorator factory that registers a function to be run in a background thread.

        Any arguments are passed to the function when the thread starts. Threads run as daemons.

        Usage::

            @app.thread()
            def poll_sensor():
                while True:
                    app.publish('sensors/temp', str(read_sensor()))
                    time.sleep(10)

            @app.thread(some_arg, key='value')
            def worker(arg, key=None):
                ...
        """
        def decorator(func):
            if func not in (entry[0] for entry in self.thread_funcs):
                self.thread_funcs.append((func, args, kwargs))
            return func
        return decorator

    def _start_threads(self):
        """Start all registered thread functions."""
        for func, args, kwargs in self.thread_funcs:
            t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            t.start()

    def do_subscribe(self):
        """Subscribe to our topics.
        """
        self.mqtt.subscribe([(topic, self.qos) for topic in self.mqtt_topics])

    def on_connect(self, client, userdata, connect_flags, reason_code, properties):
        """Called when an MQTT server connection is established.
        """
        self.log.info("MQTT connected: %s", reason_code)
        if reason_code.is_failure:
            self.log.error("Could not connect. Error: %s", reason_code)
        else:
            if self.status_enabled:
                self.mqtt.publish(self.status_topic, payload=self.status_online, qos=1, retain=True)
            self.do_subscribe()

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Called when an MQTT server is disconnected.
        """
        if not reason_code.is_failure:
            self.log.info("MQTT disconnected cleanly")
        else:
            self.log.error("MQTT disconnected unexpectedly (rc=%s)", reason_code)

    def on_exit(self):
        """Called when exiting to ensure we cleanup and disconnect cleanly.
        """
        if self.status_enabled:
            self.mqtt.publish(self.status_topic, payload=self.status_offline, qos=1, retain=True)
            self.mqtt.loop(timeout=0.5)  # Give the publish a chance to transmit before disconnecting
        self.mqtt.disconnect()

    def _env_overrides(self):
        """Read environment variables and return a dict of overrides.

        When env_prefix is empty, env vars are MQTT_HOST, USERNAME, etc.
        When env_prefix is set (e.g. 'MY_APP'), env vars are MY_APP_MQTT_HOST, etc.
        """
        prefix = self.env_prefix + '_' if self.env_prefix else ''
        overrides = {}

        for env_suffix, (attr_name, type_fn) in self._env_settings.items():
            env_key = prefix + env_suffix
            env_value = environ.get(env_key)
            if env_value is not None:
                try:
                    overrides[attr_name] = type_fn(env_value)
                except (ValueError, TypeError):
                    self.log.warning('Ignoring invalid value for %s: %r', env_key, env_value)

        return overrides

    def on_message(self, client, userdata, msg):
        """Called when paho has a message from the queue to process.
        """
        self.log.debug('Got a message for topic:%s payload:%s', msg.topic, msg.payload)

        for topic, funcs in self.mqtt_topics.items():
            if mqtt_wildcard(msg.topic, topic):
                for func in funcs:
                    try:
                        func(GourdMessage(msg))
                    except Exception as e:
                        self.log.error("Uncaught exception in %s.on_message: %s", self.__class__.__name__, e)
                        self.log.exception(e)

    def loop_start(self):
        """Run the program in a separate thread.
        """
        if not self.mqtt.is_connected():
            self.connect()
        self._start_threads()
        return self.mqtt.loop_start()

    def loop_stop(self):
        """Stop the mqtt loop.
        """
        return self.mqtt.loop_stop()

    def run_forever(self):
        """Run the program until forcibly quit.
        """
        try:
            self.connect()
            self._start_threads()
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            self.log.info('User interrupted with ^C...')
