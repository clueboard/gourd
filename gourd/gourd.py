from __future__ import annotations

import atexit
import logging
import ssl
import threading
from collections.abc import Callable
from socket import gethostname
from typing import Any

import paho.mqtt.client
from paho.mqtt.client import CallbackAPIVersion, MQTTMessage, PayloadType

from .gourd_message import GourdMessage
from .mqtt_log_handler import MQTTLogHandler
from .mqtt_wildcard import mqtt_wildcard

MessageHandler = Callable[[GourdMessage], object]
ThreadFunc = Callable[..., object]


class Gourd:
    """An opinionated framework for writing MQTT applications.

    Args:
        app_name                    The name of your application
        mqtt_topic=None             Base MQTT topic for derived topics (When None it's f'{app_name}/{gethostname()}')
        mqtt_host='localhost'       The MQTT server to connect to
        mqtt_port=1883              The port number to connect to
        username=None               The username to connect to the MQTT server with
        password=None               The password to connect to the MQTT server with
        qos=1                       Default QOS Level for messages
        timeout=30                  The timeout for the MQTT connection
        log_mqtt=True               Set to false to disable mqtt logging
        mqtt_log_topic=None         The MQTT topic to send debug logs to (When None it's f'{mqtt_topic}/debug')
        log_topic=None              Deprecated alias for mqtt_log_topic
        status_enabled=True         Set to false to disable the status topic
        status_topic=None           The topic to publish application status (ON/OFF) to (When None it's f'{mqtt_topic}/status')
        status_online='ON'          The payload to publish to status_topic when we are running
        status_offline='OFF'        The payload to publish to status_topic when we are not running
        max_inflight_messages=20    How many messages can be in-flight. See Paho MQTT documentation for more details.
        max_queued_messages=0       How many messages can be queued at a time. See Paho MQTT documentation for more details.
        tls_enabled=False           Enable TLS for broker connection
        tls_verify=True             Verify broker TLS certificate and hostname
        tls_ca_certs=None           Path to PEM bundle containing trusted root/intermediate certificates
        tls_certfile=None           Path to PEM file containing client certificate (optionally with chain)
        tls_keyfile=None            Path to PEM file containing client private key
    """

    def __init__(
        self,
        app_name: str,
        *,
        mqtt_topic: str | None = None,
        mqtt_host: str = 'localhost',
        mqtt_port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        qos: int = 1,
        timeout: int = 30,
        log_mqtt: bool = True,
        mqtt_log_topic: str | None = None,
        log_topic: str | None = None,
        status_enabled: bool = True,
        status_topic: str | None = None,
        status_online: str = 'ON',
        status_offline: str = 'OFF',
        max_inflight_messages: int = 20,
        max_queued_messages: int = 0,
        tls_enabled: bool = False,
        tls_verify: bool = True,
        tls_ca_certs: str | None = None,
        tls_certfile: str | None = None,
        tls_keyfile: str | None = None,
    ) -> None:
        self.name = app_name
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.username = username
        self.qos = qos
        self.mqtt_topics: dict[str, list[MessageHandler]] = {}
        self.timeout = timeout
        self.thread_funcs: list[tuple[ThreadFunc, tuple[object, ...], dict[str, object]]] = []
        self.mqtt_topic = mqtt_topic or f'{app_name}/{gethostname()}'
        self.tls_verify = tls_verify
        self.tls_ca_certs = tls_ca_certs
        self.tls_certfile = tls_certfile
        self.tls_keyfile = tls_keyfile
        self.tls_enabled = tls_enabled or self._should_auto_enable_tls()

        # Setup the status topic
        self.status_enabled = status_enabled
        self.status_topic: str = status_topic or f'{self.mqtt_topic}/status'
        self.status_online = status_online
        self.status_offline = status_offline

        # Setup logging
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())  # Preparation for mqtt debug logging, console logs are handled by the `gourd` CLI. or the client program if they are not using gourd's CLI

        if mqtt_log_topic is None:
            mqtt_log_topic = log_topic
        if mqtt_log_topic is None:
            mqtt_log_topic = f'{self.mqtt_topic}/debug'

        # Setup MQTT
        self.mqtt = paho.mqtt.client.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        paho_log = logging.getLogger(__name__ + '.paho')
        paho_log.propagate = False
        self.mqtt.enable_logger(paho_log)
        self.mqtt.max_inflight_messages_set(max_inflight_messages)
        self.mqtt.max_queued_messages_set(max_queued_messages)
        self.mqtt.username_pw_set(self.username, password)

        # Register mqtt callbacks
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message

        if self.status_enabled:
            self.mqtt.will_set(self.status_topic, payload=self.status_offline, qos=1, retain=True)

        # Setup MQTT logging
        self.mqtt_log_handler: MQTTLogHandler | None = None
        if log_mqtt:
            self.mqtt_log_handler = MQTTLogHandler(mqtt_client=self.mqtt, topic=mqtt_log_topic, qos=qos, retain=False)
            self.mqtt_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))
            self.log.addHandler(self.mqtt_log_handler)

        # Register handlers
        atexit.register(self.on_exit)

    def _configure_tls(self) -> None:
        """Configure MQTT TLS settings when enabled."""
        if not self.tls_enabled:
            return

        # cert_reqs controls certificate validation; tls_insecure_set controls hostname checks.
        cert_reqs = ssl.CERT_REQUIRED if self.tls_verify else ssl.CERT_NONE

        self.mqtt.tls_set(ca_certs=self.tls_ca_certs, certfile=self.tls_certfile, keyfile=self.tls_keyfile, cert_reqs=cert_reqs)
        self.mqtt.tls_insecure_set(not self.tls_verify)

    def _should_auto_enable_tls(self) -> bool:
        return any((self.tls_ca_certs, self.tls_certfile, self.tls_keyfile))

    def publish(self, topic: str, payload: PayloadType = None, *, qos: int | None = None, **kwargs: Any) -> None:
        """Publish a message to the MQTT server."""
        if qos is None:
            qos = self.qos

        self.mqtt.publish(topic, payload, qos=qos, **kwargs)

    def connect(self) -> None:
        """Connect to the MQTT server."""
        if self.tls_enabled:
            self._configure_tls()
        self.mqtt.connect(self.mqtt_host, self.mqtt_port, self.timeout)

    def subscribe(self, topic: str) -> Callable[[MessageHandler], MessageHandler]:
        """Decorator that registers a function to be called whenever a message for a topic is sent."""

        def inner_function(handler: MessageHandler) -> MessageHandler:
            if topic not in self.mqtt_topics:
                self.mqtt_topics[topic] = []

            if handler not in self.mqtt_topics[topic]:
                self.mqtt_topics[topic].append(handler)

            return handler

        return inner_function

    def thread(self, *args: object, **kwargs: object) -> Callable[[ThreadFunc], ThreadFunc]:
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

        def decorator(func: ThreadFunc) -> ThreadFunc:
            if func not in (entry[0] for entry in self.thread_funcs):
                self.thread_funcs.append((func, args, kwargs))
            return func

        return decorator

    def _start_threads(self) -> None:
        """Start all registered thread functions."""
        for func, args, kwargs in self.thread_funcs:
            t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            t.start()

    def do_subscribe(self) -> None:
        """Subscribe to our topics."""
        if not self.mqtt_topics:
            return

        self.mqtt.subscribe([(topic, self.qos) for topic in self.mqtt_topics])

    def on_connect(self, client: Any, userdata: Any, connect_flags: Any, reason_code: Any, properties: Any) -> None:
        """Called when an MQTT server connection is established."""
        self.log.info('MQTT connected: %s', reason_code)

        if reason_code.is_failure:
            self.log.error('Could not connect. Error: %s', reason_code)

            return

        if self.status_enabled:
            self.mqtt.publish(self.status_topic, payload=self.status_online, qos=1, retain=True)

        self.do_subscribe()

    def on_disconnect(self, client: Any, userdata: Any, disconnect_flags: Any, reason_code: Any, properties: Any) -> None:
        """Called when an MQTT server is disconnected."""
        if not reason_code.is_failure:
            self.log.info('MQTT disconnected cleanly')

            return

        self.log.error('MQTT disconnected unexpectedly (rc=%s)', reason_code)

    def on_exit(self) -> None:
        """Called when exiting to ensure we cleanup and disconnect cleanly."""
        if self.status_enabled:
            self.mqtt.publish(self.status_topic, payload=self.status_offline, qos=1, retain=True)
            self.mqtt.loop(timeout=0.5)  # Give the publish a chance to transmit before disconnecting
        self.mqtt.disconnect()

    def on_message(self, client: Any, userdata: Any, msg: MQTTMessage) -> None:
        """Called when paho has a message from the queue to process."""
        self.log.debug('Got a message for topic:%s payload:%s', msg.topic, msg.payload)

        for topic, funcs in self.mqtt_topics.items():
            if mqtt_wildcard(msg.topic, topic):
                for func in funcs:
                    try:
                        func(GourdMessage(msg))
                    except Exception as e:
                        self.log.error('Uncaught exception in %s.on_message: %s', self.__class__.__name__, e)
                        self.log.exception(e)

    def loop_start(self) -> Any:
        """Run the program in a separate thread."""
        if not self.mqtt.is_connected():
            self.connect()
        self._start_threads()
        return self.mqtt.loop_start()

    def loop_stop(self) -> Any:
        """Stop the mqtt loop."""
        return self.mqtt.loop_stop()

    def run_forever(self) -> None:
        """Run the program until forcibly quit."""
        try:
            self.connect()
            self._start_threads()
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            self.log.info('User interrupted with ^C...')
