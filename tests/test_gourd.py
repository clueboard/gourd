"""Unit tests for Gourd class methods."""
from unittest.mock import MagicMock, call, patch


def make_reason_code(failure=False):
    rc = MagicMock()
    rc.is_failure = failure
    return rc


def make_gourd(status_enabled=False):
    with patch('gourd.gourd.paho.mqtt.client.Client'):
        with patch('gourd.gourd.atexit.register'):
            from gourd import Gourd
            return Gourd(app_name='test', log_mqtt=False, status_enabled=status_enabled)


# --- subscribe ---

def test_subscribe_registers_handler():
    app = make_gourd()
    handler = MagicMock()
    app.subscribe('test/topic')(handler)
    assert handler in app.mqtt_topics['test/topic']


def test_subscribe_deduplicates():
    app = make_gourd()
    handler = MagicMock()
    app.subscribe('test/topic')(handler)
    app.subscribe('test/topic')(handler)
    assert app.mqtt_topics['test/topic'].count(handler) == 1


def test_subscribe_returns_handler():
    app = make_gourd()
    handler = MagicMock()
    result = app.subscribe('test/topic')(handler)
    assert result is handler


# --- do_subscribe ---

def test_do_subscribe_sends_tuples():
    app = make_gourd()
    app.mqtt_topics['test/topic'] = []
    app.mqtt_topics['other/topic'] = []
    app.do_subscribe()
    args = app.mqtt.subscribe.call_args[0][0]
    assert all(isinstance(item, tuple) and len(item) == 2 for item in args)
    assert set(t for t, _ in args) == {'test/topic', 'other/topic'}
    assert all(q == app.qos for _, q in args)


# --- publish ---

def test_publish_default_qos():
    app = make_gourd()
    app.publish('test/topic', 'hello')
    app.mqtt.publish.assert_called_once_with('test/topic', 'hello', qos=app.qos)


def test_publish_explicit_qos():
    app = make_gourd()
    app.publish('test/topic', 'hello', qos=0)
    app.mqtt.publish.assert_called_once_with('test/topic', 'hello', qos=0)


def test_publish_passes_kwargs():
    app = make_gourd()
    app.publish('test/topic', 'hello', retain=True)
    app.mqtt.publish.assert_called_once_with('test/topic', 'hello', qos=app.qos, retain=True)


# --- on_connect ---

def test_on_connect_success_publishes_status():
    app = make_gourd(status_enabled=True)
    app.on_connect(None, None, None, make_reason_code(failure=False), None)
    app.mqtt.publish.assert_any_call(app.status_topic, payload=app.status_online, qos=1, retain=True)


def test_on_connect_success_subscribes():
    app = make_gourd()
    app.mqtt_topics['test/topic'] = []
    app.on_connect(None, None, None, make_reason_code(failure=False), None)
    app.mqtt.subscribe.assert_called_once()


def test_on_connect_failure_skips_status_and_subscribe():
    app = make_gourd(status_enabled=True)
    app.on_connect(None, None, None, make_reason_code(failure=True), None)
    app.mqtt.publish.assert_not_called()
    app.mqtt.subscribe.assert_not_called()


def test_on_connect_status_disabled():
    app = make_gourd(status_enabled=False)
    app.mqtt_topics['test/topic'] = []
    app.on_connect(None, None, None, make_reason_code(failure=False), None)
    app.mqtt.publish.assert_not_called()
    app.mqtt.subscribe.assert_called_once()


# --- on_disconnect ---

def test_on_disconnect_clean():
    app = make_gourd()
    app.on_disconnect(None, None, None, make_reason_code(failure=False), None)  # should not raise


def test_on_disconnect_unexpected():
    app = make_gourd()
    app.on_disconnect(None, None, None, make_reason_code(failure=True), None)  # should not raise


# --- on_exit ---

def test_on_exit_with_status():
    app = make_gourd(status_enabled=True)
    app.on_exit()
    app.mqtt.publish.assert_called_once_with(app.status_topic, payload=app.status_offline, qos=1, retain=True)
    app.mqtt.loop.assert_called_once()
    app.mqtt.disconnect.assert_called_once()


def test_on_exit_without_status():
    app = make_gourd(status_enabled=False)
    app.on_exit()
    app.mqtt.publish.assert_not_called()
    app.mqtt.disconnect.assert_called_once()
