"""CLI for starting gourd apps
"""
import sys
from importlib import import_module

from milc import cli

__VERSION__ = '1.0.2'

cli.milc_options(name='Gourd', version=__VERSION__, author='Clueboard', env_prefix='')


@cli.argument('--mqtt-host', default=None, help='The MQTT broker hostname or IP. (Env: MQTT_HOST)')
@cli.argument('--mqtt-port', default=None, type=int, help='The MQTT broker port. (Env: MQTT_PORT)')
@cli.argument('--mqtt-username', default=None, help='Username for MQTT broker authentication. (Env: MQTT_USERNAME)')
@cli.argument('--mqtt-password', default=None, help='Password for MQTT broker authentication. (Env: MQTT_PASSWORD)')
@cli.argument('--qos', default=None, type=int, help='Default QoS level (0, 1, or 2). (Env: QOS)')
@cli.argument('--timeout', default=None, type=int, help='MQTT connection keepalive timeout in seconds. (Env: TIMEOUT)')
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
    except AttributeError as e:
        cli.log.error('Could not find object %s in module %s!', app_name, module_name)
        exit(2)

    # Apply CLI/env settings to the app before running.
    # milc resolves settings with arg > env > default precedence.
    if cli.args.mqtt_host is not None:
        app.mqtt_host = cli.args.mqtt_host

    if cli.args.mqtt_port is not None:
        app.mqtt_port = cli.args.mqtt_port

    if cli.args.timeout is not None:
        app.timeout = cli.args.timeout

    if cli.args.qos is not None:
        app.qos = cli.args.qos

    if cli.args.mqtt_username is not None or cli.args.mqtt_password is not None:
        username = cli.args.mqtt_username if cli.args.mqtt_username is not None else app.username
        password = cli.args.mqtt_password
        app.username = username
        app.mqtt.username_pw_set(username, password)

    app.run_forever()


if __name__ == '__main__':
    cli()
