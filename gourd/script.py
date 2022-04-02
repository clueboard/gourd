"""CLI for starting gourd apps
"""
from importlib import import_module

from milc import set_metadata

__VERSION__ = '0.0.4'

set_metadata(name='Gourd', version=__VERSION__, author='Clueboard')

from milc import cli


@cli.argument('gourd_app', arg_only=True, help='The entrypoint for your application in `<module>:<object>` format. EG: gourd_example:app')
@cli.entrypoint('CLI for starting Gourd apps.')
def main(cli):
    if ':' not in cli.args.gourd_app:
        cli.log.error('Invalid entrypoint: %s', cli.args.gourd_app)
        exit(2)

    module_name, app_name = cli.args.gourd_app.split(':', 1)
    module = import_module(module_name)
    try:
        app = getattr(module, app_name)
    except AttributeError as e:
        cli.log.error('Could not find object %s in module %s!', app_name, module_name)
        exit(2)

    app.run_forever()

if __name__ == '__main__':
    cli()
