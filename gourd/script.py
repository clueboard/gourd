"""CLI for starting gourd apps"""

import logging
import sys
from importlib import import_module
from typing import Any

from milc import cli, MILCInterface

from gourd.mqtt_log_handler import MQTTLogHandler

__VERSION__ = '1.0.2'

cli.milc_options(name='Gourd', version=__VERSION__, author='Clueboard', env_prefix='')


@cli.argument('--mqtt-host', default=None, help='The MQTT broker hostname or IP.')
@cli.argument('--mqtt-port', default=None, type=int, help='The MQTT broker port.')
@cli.argument('--mqtt-username', default=None, help='Username for MQTT broker authentication.')
@cli.argument('--mqtt-password', default=None, help='Password for MQTT broker authentication.')
@cli.argument('--qos', default=None, type=int, choices=[0, 1, 2], help='Default QoS level (0, 1, or 2).')
@cli.argument('--timeout', default=None, type=int, help='MQTT connection keepalive timeout in seconds.')
@cli.argument('--log-mqtt', action='store_boolean', default=None, help='Enable or disable MQTT logging.')
@cli.argument('--log-mqtt-topic', default=None, help='The MQTT topic to publish log messages to.')
@cli.argument('--status-enabled', action='store_boolean', default=None, help='Enable or disable the status topic.')
@cli.argument('--max-inflight-messages', default=None, type=int, help='Maximum number of in-flight QoS > 0 messages.')
@cli.argument('--max-queued-messages', default=None, type=int, help='Maximum number of queued messages (0 = unlimited).')
@cli.argument('--tls-enabled', action='store_boolean', default=None, help='Enable or disable TLS for broker connection.')
@cli.argument('--tls-verify', action='store_boolean', default=None, help='Enable or disable TLS certificate/hostname verification.')
@cli.argument('--tls-ca-certs', default=None, help='Path to PEM bundle with trusted root/intermediate certificates.')
@cli.argument('--tls-certfile', default=None, help='Path to PEM file with client certificate (optionally including chain).')
@cli.argument('--tls-keyfile', default=None, help='Path to PEM file with client private key.')
@cli.argument('--sys-path', action='append', default=[], help='Append this path to sys.path (Can be passed multiple times.)')
@cli.argument('--relative-path', action='store_boolean', default=True, help='relative path for the entrypoint. (Default: Enabled)')
@cli.argument('gourd_app', arg_only=True, help='The entrypoint for your application in `<module>:<object>` format. EG: gourd_example:app')
@cli.entrypoint('CLI for starting Gourd apps.')
def main(cli: MILCInterface) -> None:
    gourd_app = cli.args.gourd_app

    if ':' not in gourd_app:
        cli.log.error('Invalid entrypoint: %s', gourd_app)
        sys.exit(2)

    for path in cli.args.sys_path:
        sys.path.append(path)

    if cli.args.relative_path and '.' not in sys.path:
        sys.path.append('.')

    module_name, app_name = gourd_app.split(':', 1)
    cli.log.debug('Importing module "%s" with sys.path of %s', module_name, repr(sys.path))
    module = import_module(module_name)

    try:
        cli.log.debug('Getting object "%s" from module "%s"', app_name, module_name)
        app = getattr(module, app_name)
    except AttributeError:
        cli.log.error('Could not find object %s in module %s!', app_name, module_name)
        sys.exit(2)

    _apply_overrides(app)
    app.run_forever()


def _apply_overrides(app: Any) -> None:
    """Apply CLI/env overrides using milc's resolved config.

    milc resolves values in cli.config.general with arg > env > config file >
    defaults/constructor precedence.
    """
    _apply_credential_overrides(app)
    _apply_log_mqtt_overrides(app)
    _apply_tls_overrides(app)

    if cli.config.general.mqtt_host is not None:
        app.mqtt_host = cli.config.general.mqtt_host

    if cli.config.general.mqtt_port is not None:
        app.mqtt_port = cli.config.general.mqtt_port

    if cli.config.general.timeout is not None:
        app.timeout = cli.config.general.timeout

    if cli.config.general.qos is not None:
        app.qos = cli.config.general.qos
        if app.mqtt_log_handler:
            app.mqtt_log_handler.qos = cli.config.general.qos

    if cli.config.general.status_enabled is not None:
        app.status_enabled = cli.config.general.status_enabled
        if app.status_enabled:
            app.mqtt.will_set(app.status_topic, payload=app.status_offline, qos=1, retain=True)
        else:
            app.mqtt.will_clear()

    if cli.config.general.max_inflight_messages is not None:
        app.mqtt.max_inflight_messages_set(cli.config.general.max_inflight_messages)

    if cli.config.general.max_queued_messages is not None:
        app.mqtt.max_queued_messages_set(cli.config.general.max_queued_messages)


def _apply_credential_overrides(app: Any) -> None:
    """Apply MQTT username/password overrides.

    Both --mqtt-username and --mqtt-password must be provided together.
    """
    mqtt_username = cli.config.general.mqtt_username
    mqtt_password = cli.config.general.mqtt_password
    has_username = mqtt_username is not None
    has_password = mqtt_password is not None

    if (has_username and not has_password) or (has_password and not has_username):
        cli.log.error('Both --mqtt-username and --mqtt-password must be provided together.')
        sys.exit(2)

    if not (has_username or has_password):
        return

    app.username = mqtt_username
    app.mqtt.username_pw_set(mqtt_username, mqtt_password)  # Not storing mqtt_password is a deliberate choice


def _apply_log_mqtt_overrides(app: Any) -> None:
    """Apply MQTT logging overrides."""
    default_log_topic = f'{app.mqtt_topic}/debug'
    log_mqtt = cli.config.general.log_mqtt
    log_mqtt_topic = cli.config.general.log_mqtt_topic

    if log_mqtt is not None:
        if log_mqtt and not app.mqtt_log_handler:
            topic = log_mqtt_topic or default_log_topic
            app.mqtt_log_handler = MQTTLogHandler(mqtt_client=app.mqtt, topic=topic, qos=app.qos, retain=False)
            app.mqtt_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))
            app.log.addHandler(app.mqtt_log_handler)

        elif not log_mqtt and app.mqtt_log_handler:
            app.log.removeHandler(app.mqtt_log_handler)
            app.mqtt_log_handler.close()
            app.mqtt_log_handler = None

    if log_mqtt_topic is not None and app.mqtt_log_handler:
        app.mqtt_log_handler.topic = log_mqtt_topic


def _apply_tls_overrides(app: Any) -> None:
    """Apply MQTT TLS overrides."""
    if cli.config.general.tls_enabled is not None:
        app.tls_enabled = cli.config.general.tls_enabled

    if cli.config.general.tls_verify is not None:
        app.tls_verify = cli.config.general.tls_verify

    if cli.config.general.tls_ca_certs is not None:
        app.tls_ca_certs = cli.config.general.tls_ca_certs

    if cli.config.general.tls_certfile is not None:
        app.tls_certfile = cli.config.general.tls_certfile

    if cli.config.general.tls_keyfile is not None:
        app.tls_keyfile = cli.config.general.tls_keyfile

    if cli.config.general.tls_enabled is None and not app.tls_enabled and app._should_auto_enable_tls():
        app.tls_enabled = True


if __name__ == '__main__':
    cli()
