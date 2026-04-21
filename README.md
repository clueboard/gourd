# Gourd - An MQTT framework

Gourd is an opinionated framework for writing MQTT applications.

> See [BREAKING_CHANGES.md](BREAKING_CHANGES.md) if you are upgrading from a previous version.

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
def print_all(message):
    app.log.info(f'{message.topic}: {message.payload}')
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
uv run ty check gourd/ tests/
uv run pytest
```

See [docs/contributing.md](docs/contributing.md) for docs-site development and contribution guidance.

## Reporting Bugs and Requesting Features

Please let us know about any bugs and/or feature requests you have: <https://github.com/clueboard/gourd/issues>
