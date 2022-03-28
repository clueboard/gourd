import logging

from paho.mqtt.client import mqtt_cs_connected, mqtt_cs_connect_async

MQTT_CONNECTED = (mqtt_cs_connected, mqtt_cs_connect_async)


class MQTTLogHandler(logging.Handler):
    def __init__(self, mqtt_client, topic, qos=0, retain=False):
        super().__init__()

        self.mqtt = mqtt_client
        self.topic = topic
        self.qos = qos
        self.retain = retain

    def emit(self, record):
        if self.mqtt._state in MQTT_CONNECTED:  # Only emit logs when MQTT is connected
            try:
                msg = self.format(record)
                if self.topic not in msg and 'Received PUBACK' not in msg:
                    # Avoid loops by skipping log messages possibly triggered by us
                    self.mqtt.publish(topic=self.topic, payload=msg, qos=self.qos, retain=self.retain)
            except Exception:
                self.handleError(record)
