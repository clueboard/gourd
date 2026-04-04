import logging


class MQTTLogHandler(logging.Handler):
    def __init__(self, mqtt_client, topic, qos=0, retain=False):
        super().__init__()

        self.mqtt = mqtt_client
        self.topic = topic
        self.qos = qos
        self.retain = retain

    def emit(self, record):
        if self.mqtt.is_connected():  # Only emit logs when MQTT is connected
            try:
                msg = self.format(record)
                self.mqtt.publish(topic=self.topic, payload=msg, qos=self.qos, retain=self.retain)
            except Exception:
                self.handleError(record)
