"""Unit tests for Gourd class methods."""
from socket import gethostname
from unittest.mock import MagicMock, patch


def make_reason_code(failure=False):
    rc = MagicMock()
    rc.is_failure = failure
    return rc


def make_gourd(status_enabled=False, log_mqtt=False, **kwargs):
    with patch('gourd.gourd.paho.mqtt.client.Client'):
        with patch('gourd.gourd.atexit.register'):
            from gourd import Gourd
            return Gourd(app_name='test', log_mqtt=log_mqtt, status_enabled=status_enabled, **kwargs)


def test_default_topic_derivation():
    app = make_gourd(status_enabled=True, log_mqtt=True)
    assert app.mqtt_topic == f'test/{gethostname()}'
    assert app.status_topic == f'{app.mqtt_topic}/status'
    assert app.mqtt_log_handler.topic == f'{app.mqtt_topic}/debug'


def test_custom_mqtt_topic_derivation():
    app = make_gourd(status_enabled=True, log_mqtt=True, mqtt_topic='custom/base')
    assert app.mqtt_topic == 'custom/base'
    assert app.status_topic == 'custom/base/status'
    assert app.mqtt_log_handler.topic == 'custom/base/debug'


def test_topic_derivation_with_features_disabled():
    app = make_gourd(status_enabled=False, log_mqtt=False, mqtt_topic='custom/base')
    assert app.mqtt_topic == 'custom/base'
    assert app.status_topic == 'custom/base/status'
    assert app.mqtt_log_handler is None


def test_mqtt_log_topic_overrides_default():
    app = make_gourd(log_mqtt=True, mqtt_topic='custom/base', mqtt_log_topic='custom/debug')
    assert app.mqtt_log_handler.topic == 'custom/debug'


def test_log_topic_alias_sets_mqtt_log_topic():
    app = make_gourd(log_mqtt=True, mqtt_topic='custom/base', log_topic='legacy/debug')
    assert app.mqtt_log_handler.topic == 'legacy/debug'


def test_mqtt_log_topic_takes_precedence_over_log_topic():
    app = make_gourd(
        log_mqtt=True,
        mqtt_topic='custom/base',
        mqtt_log_topic='custom/debug',
        log_topic='legacy/debug',
    )
    assert app.mqtt_log_handler.topic == 'custom/debug'
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


# --- thread ---


def test_thread_registers_handler():
    app = make_gourd()
    func = MagicMock()
    app.thread()(func)
    assert func in (entry[0] for entry in app.thread_funcs)


def test_thread_deduplicates():
    app = make_gourd()
    func = MagicMock()
    app.thread()(func)
    app.thread()(func)
    assert sum(1 for entry in app.thread_funcs if entry[0] is func) == 1


def test_thread_returns_handler():
    app = make_gourd()
    func = MagicMock()
    result = app.thread()(func)
    assert result is func


def test_thread_stores_args_and_kwargs():
    app = make_gourd()
    func = MagicMock()
    app.thread('a', key='val')(func)
    entry = next(e for e in app.thread_funcs if e[0] is func)
    assert entry[1] == ('a',)
    assert entry[2] == {'key': 'val'}


def test_run_forever_starts_threads():
    app = make_gourd()
    func = MagicMock()
    app.thread()(func)
    with patch('gourd.gourd.threading.Thread') as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        app.run_forever()
    mock_thread_cls.assert_called_once_with(target=func, args=(), kwargs={}, daemon=True)
    mock_thread.start.assert_called_once()


def test_loop_start_starts_threads():
    app = make_gourd()
    func = MagicMock()
    app.thread()(func)
    app.mqtt.is_connected.return_value = True
    with patch('gourd.gourd.threading.Thread') as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        app.loop_start()
    mock_thread_cls.assert_called_once_with(target=func, args=(), kwargs={}, daemon=True)
    mock_thread.start.assert_called_once()


def test_thread_passes_args_to_function():
    app = make_gourd()
    func = MagicMock()
    app.thread('x', key='y')(func)
    with patch('gourd.gourd.threading.Thread') as mock_thread_cls:
        mock_thread_cls.return_value = MagicMock()
        app.run_forever()
    mock_thread_cls.assert_called_once_with(target=func, args=('x',), kwargs={'key': 'y'}, daemon=True)


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
