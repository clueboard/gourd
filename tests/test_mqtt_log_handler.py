"""Unit tests for gourd.mqtt_log_handler.MQTTLogHandler."""
import logging
from threading import Lock
from unittest.mock import MagicMock, call
from gourd.mqtt_log_handler import MQTTLogHandler


def make_handler(connected=True, lock=None):
    mqtt = MagicMock()
    mqtt.is_connected.return_value = connected
    handler = MQTTLogHandler(mqtt_client=mqtt, topic='app/log', qos=1, retain=False, lock=lock)
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



def test_acquires_lock_when_provided():
    lock = MagicMock()
    lock.__enter__ = MagicMock(return_value=None)
    lock.__exit__ = MagicMock(return_value=False)
    handler, mqtt = make_handler(connected=True, lock=lock)

    handler.emit(make_record('hello'))

    lock.__enter__.assert_called_once()
    mqtt.publish.assert_called_once()


def test_no_lock_still_publishes():
    handler, mqtt = make_handler(connected=True, lock=None)
    handler.emit(make_record('hello'))
    mqtt.publish.assert_called_once()
