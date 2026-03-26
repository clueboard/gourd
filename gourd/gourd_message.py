import json
import logging

log = logging.getLogger(__name__)


class GourdMessage:
    def __init__(self, mqtt_message):
        self.mqtt_message = mqtt_message
        self._json = None

        try:
            self.payload = mqtt_message.payload.decode('utf-8').strip()
        except AttributeError:
            self.payload = mqtt_message.payload

    @property
    def json(self):
        if self._json is None:
            self._json = {}

            if self.payload.startswith('{') and self.payload.endswith('}'):
                try:
                    self._json = json.loads(self.payload)
                except Exception as e:
                    log.warning('Could not decode payload as JSON: %s (%s)', self.payload, e)

        return self._json

    def __getattr__(self, attr):
        return getattr(self.mqtt_message, attr)
