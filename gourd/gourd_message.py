from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)


class GourdMessage:
    def __init__(self, mqtt_message: Any) -> None:
        self.mqtt_message = mqtt_message
        self._json: Any | None = None
        self.payload = mqtt_message.payload

    @property
    def text(self) -> str:
        payload = self.payload

        if isinstance(payload, bytes):
            return payload.decode('utf-8').strip()

        if isinstance(payload, str):
            return payload

        return str(payload)

    @property
    def json(self) -> Any | None:
        if self._json is not None:
            return self._json

        try:
            payload = self.text
        except UnicodeDecodeError:
            self._json = None

            return self._json

        if not payload.startswith('{') or not payload.endswith('}'):
            self._json = None

            return self._json

        try:
            parsed_payload = json.loads(payload)
        except Exception as e:
            log.warning('Could not decode payload as JSON: %s (%s)', payload, e)
            parsed_payload = None

        self._json = parsed_payload

        return self._json

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.mqtt_message, attr)
