"""CLI for starting gourd apps
"""
import logging
import sys
from importlib import import_module
from socket import gethostname

from milc import cli

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
@cli.argument('--sys-path', action='append', default=[], help='Append this path to sys.path (Can be passed multiple times.)')
@cli.argument('--relative-path', action='store_boolean', default=True, help='relative path for the entrypoint. (Default: Enabled)')
@cli.argument('gourd_app', arg_only=True, help='The entrypoint for your application in `<module>:<object>` format. EG: gourd_example:app')
@cli.entrypoint('CLI for starting Gourd apps.')
def main(cli):
    if ':' not in cli.args.gourd_app:
        cli.log.error('Invalid entrypoint: %s', cli.args.gourd_app)
        exit(2)

    for path in cli.args.sys_path:
        sys.path.append(path)

    if cli.args.relative_path and '.' not in sys.path:
        sys.path.append('.')

    module_name, app_name = cli.args.gourd_app.split(':', 1)
    cli.log.debug('Importing module "%s" with sys.path of %s', module_name, repr(sys.path))
    module = import_module(module_name)

    try:
        cli.log.debug('Getting object "%s" from module "%s"', app_name, module_name)
        app = getattr(module, app_name)
    except AttributeError:
        cli.log.error('Could not find object %s in module %s!', app_name, module_name)
        exit(2)

    _apply_overrides(cli, app)
    app.run_forever()


def _apply_overrides(cli, app):
    """Apply CLI/env overrides using milc's resolved config.

    milc handles arg > env > default precedence via cli.config.general.
    Only values explicitly set (not None) override the app's constructor defaults.
    """
    config = cli.config.general

    _apply_credential_overrides(cli, config, app)

    if config.mqtt_host is not None:
        app.mqtt_host = config.mqtt_host

    if config.mqtt_port is not None:
        app.mqtt_port = config.mqtt_port

    if config.timeout is not None:
        app.timeout = config.timeout

    if config.qos is not None:
        app.qos = config.qos
        if app.mqtt_log_handler:
            app.mqtt_log_handler.qos = config.qos

    if config.status_enabled is not None:
        app.status_enabled = config.status_enabled
        if app.status_enabled:
            app.mqtt.will_set(app.status_topic, app.status_offline, qos=app.qos, retain=True)
        else:
            app.mqtt.will_clear()

    if config.max_inflight_messages is not None:
        app.mqtt.max_inflight_messages_set(config.max_inflight_messages)

    if config.max_queued_messages is not None:
        app.mqtt.max_queued_messages_set(config.max_queued_messages)

    _apply_log_mqtt_overrides(config, app)


def _apply_credential_overrides(cli, config, app):
    """Apply MQTT username/password overrides.

    Both --mqtt-username and --mqtt-password must be provided together.
    """
    if config.mqtt_username is not None and config.mqtt_password is None:
        cli.log.error('Both --mqtt-username and --mqtt-password must be provided together.')
        sys.exit(2)

    if config.mqtt_password is not None and config.mqtt_username is None:
        cli.log.error('Both --mqtt-username and --mqtt-password must be provided together.')
        sys.exit(2)

    if config.mqtt_username is not None and config.mqtt_password is not None:
        app.username = config.mqtt_username
        app.mqtt.username_pw_set(config.mqtt_username, config.mqtt_password)


def _apply_log_mqtt_overrides(config, app):
    """Apply MQTT logging overrides."""
    if config.log_mqtt is not None:
        if config.log_mqtt and not app.mqtt_log_handler:
            topic = config.log_mqtt_topic or f'{app.name}/{gethostname()}/debug'
            app.mqtt_log_handler = MQTTLogHandler(mqtt_client=app.mqtt, topic=topic, qos=app.qos, retain=False)
            app.mqtt_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))
            app.log.addHandler(app.mqtt_log_handler)
        elif not config.log_mqtt and app.mqtt_log_handler:
            app.log.removeHandler(app.mqtt_log_handler)
            app.mqtt_log_handler.close()
            app.mqtt_log_handler = None

    if config.log_mqtt_topic is not None and app.mqtt_log_handler:
        app.mqtt_log_handler.topic = config.log_mqtt_topic


if __name__ == '__main__':
    cli()
