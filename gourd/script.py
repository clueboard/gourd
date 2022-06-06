"""CLI for starting gourd apps
"""
import sys
from importlib import import_module

from milc import set_metadata

__VERSION__ = '0.1.1'

set_metadata(name='Gourd', version=__VERSION__, author='Clueboard')

from milc import cli


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

    app.run_forever()


if __name__ == '__main__':
    cli()
