"""Unit tests for gourd.mqtt_log_handler.MQTTLogHandler."""

import logging
from unittest.mock import MagicMock
from gourd.mqtt_log_handler import MQTTLogHandler


def make_handler(connected=True):
    mqtt = MagicMock()
    mqtt.is_connected.return_value = connected
    handler = MQTTLogHandler(mqtt_client=mqtt, topic='app/log', qos=1, retain=False)
    handler.setFormatter(logging.Formatter('%(message)s'))
    return handler, mqtt


def make_record(msg):
    return logging.LogRecord(name='test', level=logging.DEBUG, pathname='', lineno=0, msg=msg, args=(), exc_info=None)


def test_does_not_emit_when_disconnected():
    handler, mqtt = make_handler(connected=False)
    handler.emit(make_record('hello'))
    mqtt.publish.assert_not_called()


def test_emits_when_connected():
    handler, mqtt = make_handler(connected=True)
    handler.emit(make_record('hello'))
    mqtt.publish.assert_called_once()
