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
        payload = self.payload
        parsed_payload = {}

        if self._json is not None:
            return self._json

        if payload.startswith('{') and payload.endswith('}'):
            try:
                parsed_payload = json.loads(payload)
            except Exception as e:
                log.warning('Could not decode payload as JSON: %s (%s)', payload, e)

        self._json = parsed_payload

        return self._json

    def __getattr__(self, attr):
        return getattr(self.mqtt_message, attr)
