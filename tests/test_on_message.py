"""Unit tests for Gourd.on_message dispatch."""
from unittest.mock import MagicMock, patch
from gourd.gourd_message import GourdMessage


def make_gourd():
    with patch('gourd.gourd.paho.mqtt.client.Client'):
        with patch('gourd.gourd.atexit.register'):
            from gourd import Gourd
            return Gourd(app_name='test', log_mqtt=False, status_enabled=False)


def make_paho_msg(topic, payload=b''):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = payload
    return msg


def test_handler_called():
    app = make_gourd()
    handler = MagicMock()
    app.mqtt_topics['test/topic'] = [handler]

    app.on_message(None, None, make_paho_msg('test/topic'))

    handler.assert_called_once()
    assert isinstance(handler.call_args[0][0], GourdMessage)


def test_multiple_handlers_all_called():
    app = make_gourd()
    h1, h2 = MagicMock(), MagicMock()
    app.mqtt_topics['test/topic'] = [h1, h2]

    app.on_message(None, None, make_paho_msg('test/topic'))

    h1.assert_called_once()
    h2.assert_called_once()


def test_non_matching_topic_not_called():
    app = make_gourd()
    handler = MagicMock()
    app.mqtt_topics['other/topic'] = [handler]

    app.on_message(None, None, make_paho_msg('test/topic'))

    handler.assert_not_called()


def test_wildcard_dispatches():
    app = make_gourd()
    handler = MagicMock()
    app.mqtt_topics['test/#'] = [handler]

    app.on_message(None, None, make_paho_msg('test/foo/bar'))

    handler.assert_called_once()


def test_exception_in_one_handler_does_not_skip_others():
    app = make_gourd()

    def bad_handler(msg):
        raise RuntimeError('boom')

    good_handler = MagicMock()
    app.mqtt_topics['test/topic'] = [bad_handler, good_handler]

    app.on_message(None, None, make_paho_msg('test/topic'))

    good_handler.assert_called_once()
