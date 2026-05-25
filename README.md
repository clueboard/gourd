# Gourd - An MQTT framework

Gourd is an opinionated framework for writing MQTT applications.

> See [docs/upgrading.md](docs/upgrading.md) for breaking changes when updating from a previous version.

## Features

* Create a fully-functional MQTT app in minutes
* Status published to `<app_name>/<hostname>/status` with a Last Will and Testament
* Debug logs published to `<app_name>/<hostname>/debug`
* Use decorators to associate topics with one or more functions
* JSON dictionary payloads automatically decoded to `msg.json`

## Quick Start

Install Gourd:

```shell
python3 -m pip install gourd
```

Create a file `my_app.py`:

```python
from gourd import Gourd

app = Gourd(app_name='my_app', mqtt_host='localhost')


@app.subscribe('#')
def print_all_messages(message):
    app.log.info(f'{message.topic}: {message.text}')
```

Run it:

```shell
gourd my_app:app
```

## Documentation

Full documentation is available at **https://gourd.clueboard.co/** and in the [docs/](docs/) directory:

* [Getting Started](docs/getting-started.md)
* [Configuration](docs/configuration.md)
* [API Reference](docs/api-reference.md)
* [Code Style](docs/codestyle.md)
* [Examples](docs/examples.md)
* [Upgrading](docs/upgrading.md)
* [Contributing](docs/contributing.md)

## Development

Set up a local development environment:

```shell
uv sync --dev
```

Run checks:

```shell
uv run ruff format --check gourd/ tests/
uv run ruff check gourd/ tests/
uv run ruff check --select FA102,UP007,UP045 gourd/ tests/
uv run ty check gourd/ tests/
uv run pytest
```

See [docs/contributing.md](docs/contributing.md) for docs-site development and contribution guidance.

## Reporting Bugs and Requesting Features

Please let us know about any bugs and/or feature requests you have: <https://github.com/clueboard/gourd/issues>
