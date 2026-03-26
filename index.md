---
layout: base.njk
title: Gourd
---

# Gourd

Gourd is an opinionated Python framework for writing MQTT applications.
It handles connection management, status reporting, and logging so you
can focus on your application logic.

## Quick Start

Install with pip:

```shell
pip install gourd
```

Create `my_app.py`:

```python
from gourd import Gourd

app = Gourd(app_name='my_app', mqtt_host='localhost')

@app.subscribe('#')
def print_all(message):
    app.log.info(f'{message.topic}: {message.payload}')

if __name__ == '__main__':
    app.run_forever()
```

Run it:

```shell
gourd my_app:app
```

## Features

- Create a fully-functional MQTT app in minutes
- Status published to `<app_name>/<hostname>/status` with a Last Will and Testament
- Debug logs published to `<app_name>/<hostname>/debug`
- Use decorators to associate topics with one or more handler functions
- JSON dictionary payloads automatically decoded to `msg.json`

## Documentation

- [Getting Started](docs/getting-started/) — prerequisites, your first app, and what Gourd does automatically
- [Configuration](docs/configuration/) — all `Gourd()` constructor arguments
- [API Reference](docs/api-reference/) — `subscribe`, `publish`, `GourdMessage`, and more
- [Examples](docs/examples/) — copy-paste patterns for common tasks
- [Upgrading](docs/upgrading/) — migration guide for breaking changes
