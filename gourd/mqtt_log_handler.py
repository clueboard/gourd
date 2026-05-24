import logging

import paho.mqtt.client

class MQTTLogHandler(logging.Handler):
    def __init__(self, mqtt_client: paho.mqtt.client.Client, topic: str, qos: int = 0, retain: bool = False) -> None:
        super().__init__()

        self.mqtt = mqtt_client
        self.topic = topic
        self.qos = qos
        self.retain = retain

    def emit(self, record: logging.LogRecord) -> None:
        if not self.mqtt.is_connected():  # Only emit logs when MQTT is connected
            return

        try:
            msg = self.format(record)
            self.mqtt.publish(topic=self.topic, payload=msg, qos=self.qos, retain=self.retain)
        except Exception:
            self.handleError(record)
