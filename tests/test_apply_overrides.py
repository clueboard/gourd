"""Unit tests for _apply_overrides and its helpers in gourd.script."""
from unittest.mock import MagicMock, patch

import pytest


def make_gourd(status_enabled=False, log_mqtt=False, **kwargs):
    with patch('gourd.gourd.paho.mqtt.client.Client'):
        with patch('gourd.gourd.atexit.register'):
            from gourd import Gourd
            return Gourd(app_name='test', log_mqtt=log_mqtt, status_enabled=status_enabled, **kwargs)


def make_config(**overrides):
    """Create a mock config object with None defaults for all fields."""
    defaults = {
        'mqtt_host': None,
        'mqtt_port': None,
        'mqtt_username': None,
        'mqtt_password': None,
        'qos': None,
        'timeout': None,
        'log_mqtt': None,
        'log_mqtt_topic': None,
        'status_enabled': None,
        'max_inflight_messages': None,
        'max_queued_messages': None,
        'tls_enabled': None,
        'tls_verify': None,
        'tls_ca_certs': None,
        'tls_certfile': None,
        'tls_keyfile': None,
    }
    defaults.update(overrides)

    config = MagicMock()
    for key, value in defaults.items():
        setattr(config, key, value)

    return config


def make_cli(config):
    """Create a mock cli object with the given config."""
    mock_cli = MagicMock()
    mock_cli.config.general = config
    return mock_cli


# --- _apply_overrides: simple field overrides ---


def test_override_mqtt_host():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(mqtt_host='broker.example')
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.mqtt_host == 'broker.example'


def test_override_mqtt_port():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(mqtt_port=8883)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.mqtt_port == 8883


def test_override_timeout():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(timeout=60)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.timeout == 60


def test_override_qos():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(qos=2)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.qos == 2


def test_override_qos_syncs_log_handler():
    from gourd.script import _apply_overrides

    app = make_gourd(log_mqtt=True)
    assert app.mqtt_log_handler is not None
    config = make_config(qos=0)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.qos == 0
    assert app.mqtt_log_handler.qos == 0


def test_none_values_do_not_override():
    from gourd.script import _apply_overrides

    app = make_gourd()
    original_host = app.mqtt_host
    original_port = app.mqtt_port
    config = make_config()  # all None
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.mqtt_host == original_host
    assert app.mqtt_port == original_port


# --- _apply_credential_overrides ---


def test_credential_override_both_provided():
    from gourd.script import _apply_credential_overrides

    app = make_gourd()
    config = make_config(mqtt_username='user', mqtt_password='pass')
    cli = MagicMock()

    _apply_credential_overrides(cli, config, app)
    app.mqtt.username_pw_set.assert_called_with('user', 'pass')
    assert app.username == 'user'


def test_credential_override_username_only_exits():
    from gourd.script import _apply_credential_overrides

    app = make_gourd()
    config = make_config(mqtt_username='user')
    cli = MagicMock()

    with pytest.raises(SystemExit) as exc_info:
        _apply_credential_overrides(cli, config, app)
    assert exc_info.value.code == 2


def test_credential_override_password_only_exits():
    from gourd.script import _apply_credential_overrides

    app = make_gourd()
    config = make_config(mqtt_password='pass')
    cli = MagicMock()

    with pytest.raises(SystemExit) as exc_info:
        _apply_credential_overrides(cli, config, app)
    assert exc_info.value.code == 2


def test_credential_override_neither_does_nothing():
    from gourd.script import _apply_credential_overrides

    app = make_gourd()
    config = make_config()
    cli = MagicMock()

    call_count_before = app.mqtt.username_pw_set.call_count
    _apply_credential_overrides(cli, config, app)
    assert app.mqtt.username_pw_set.call_count == call_count_before


# --- status overrides ---


def test_status_enable_sets_will():
    from gourd.script import _apply_overrides

    app = make_gourd(status_enabled=False)
    config = make_config(status_enabled=True)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.status_enabled is True
    app.mqtt.will_set.assert_called_once_with(app.status_topic, payload=app.status_offline, qos=1, retain=True)


def test_status_disable_clears_will():
    from gourd.script import _apply_overrides

    app = make_gourd(status_enabled=True)
    config = make_config(status_enabled=False)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.status_enabled is False
    app.mqtt.will_clear.assert_called_once()


# --- log_mqtt overrides ---


def test_log_mqtt_enable_creates_handler():
    from gourd.script import _apply_log_mqtt_overrides

    app = make_gourd(log_mqtt=False, mqtt_topic='custom/base')
    assert app.mqtt_log_handler is None
    config = make_config(log_mqtt=True)

    _apply_log_mqtt_overrides(config, app)
    assert app.mqtt_log_handler is not None
    assert app.mqtt_log_handler.topic == 'custom/base/debug'


def test_log_mqtt_disable_removes_handler():
    from gourd.script import _apply_log_mqtt_overrides

    app = make_gourd(log_mqtt=True)
    handler = app.mqtt_log_handler
    assert handler is not None
    config = make_config(log_mqtt=False)

    with patch.object(handler, 'close') as mock_close:
        _apply_log_mqtt_overrides(config, app)
        assert app.mqtt_log_handler is None
        mock_close.assert_called_once()


def test_log_mqtt_topic_override():
    from gourd.script import _apply_log_mqtt_overrides

    app = make_gourd(log_mqtt=True)
    assert app.mqtt_log_handler is not None
    config = make_config(log_mqtt_topic='custom/topic')

    _apply_log_mqtt_overrides(config, app)
    assert app.mqtt_log_handler.topic == 'custom/topic'


def test_log_mqtt_enable_with_custom_topic():
    from gourd.script import _apply_log_mqtt_overrides

    app = make_gourd(log_mqtt=False)
    config = make_config(log_mqtt=True, log_mqtt_topic='custom/debug')

    _apply_log_mqtt_overrides(config, app)
    assert app.mqtt_log_handler is not None
    assert app.mqtt_log_handler.topic == 'custom/debug'


# --- max inflight / queued ---


def test_override_max_inflight_messages():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(max_inflight_messages=10)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    app.mqtt.max_inflight_messages_set.assert_called_with(10)


def test_override_max_queued_messages():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(max_queued_messages=100)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    app.mqtt.max_queued_messages_set.assert_called_with(100)


# --- TLS overrides ---


def test_override_tls_enabled_configures_client():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(tls_enabled=True)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.tls_enabled is True
    app.mqtt.tls_set.assert_called_once()
    app.mqtt.tls_insecure_set.assert_called_once_with(False)


def test_override_tls_verify_false_configures_insecure_mode():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(tls_enabled=True, tls_verify=False)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.tls_enabled is True
    assert app.tls_verify is False
    app.mqtt.tls_insecure_set.assert_called_once_with(True)


def test_override_tls_verify_false_without_tls_enabled_does_not_enable_tls():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(tls_verify=False)
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.tls_enabled is False
    assert app.tls_verify is False
    app.mqtt.tls_set.assert_not_called()
    app.mqtt.tls_insecure_set.assert_not_called()


def test_override_tls_cert_paths_enable_and_configure_tls():
    from gourd.script import _apply_overrides

    app = make_gourd()
    config = make_config(
        tls_ca_certs='/tmp/ca-chain.pem',
        tls_certfile='/tmp/client-chain.pem',
        tls_keyfile='/tmp/client.key',
    )
    cli = make_cli(config)

    _apply_overrides(cli, app)
    assert app.tls_enabled is True
    kwargs = app.mqtt.tls_set.call_args.kwargs
    assert kwargs['ca_certs'] == '/tmp/ca-chain.pem'
    assert kwargs['certfile'] == '/tmp/client-chain.pem'
    assert kwargs['keyfile'] == '/tmp/client.key'
