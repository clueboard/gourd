import json

class GourdMessage:
    def __init__(self, mqtt_message):
        self.mqtt_message = mqtt_message
        self._json = None

        try:
            self.payload = mqtt_message.payload.decode('utf-8')
        except AttributeError:
            self.payload = mqtt_message.payload

    @property
    def json(self):
        if self._json is None:
            self._json = {}

            if self.payload[0] == '{' and self.payload[-1] == '}':
                try:
                    self._json = json.loads(self.payload)
                except Exception as e:
                    self.log.debug('Could not decode payload as json dictionary: %s', self.payload)

        return self._json

    def __getattr__(self, attr):
        return getattr(self.mqtt_message, attr)
