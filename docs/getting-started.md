---
layout: base.njk
title: Getting Started
order: 1
tags: docs
---

# Getting Started with Gourd

Gourd is an opinionated Python framework for writing MQTT applications. It handles connection management, status reporting, and logging so you can focus on your application logic.

## Prerequisites

- Python 3.9 or higher
- A reachable MQTT broker (e.g. [Mosquitto](https://mosquitto.org/))
- Install Gourd:

```shell
pip install gourd
```

## Your First App

Create a file `my_app.py`:

```python
import logging
from gourd import Gourd

# basicConfig enables console logging
logging.basicConfig()

app = Gourd(
    app_name='my_app',
    mqtt_host='localhost',
    username='mqtt',
    password='my_password',
)

@app.subscribe('sensors/#')
def handle_sensor(message):
    app.log.info(f'{message.topic}: {message.payload}')

if __name__ == '__main__':
    app.run_forever()
```

Run it with the `gourd` CLI:

```shell
gourd my_app:app
```

Or run it directly with Python (the `if __name__ == '__main__'` block calls `run_forever()`):

```shell
python my_app.py
```

## What Happens Automatically

Gourd does three things for you without any configuration:

**Status topic (Last Will and Testament)**

When your app connects, Gourd publishes `ON` to `{app_name}/{hostname}/status` with `retain=True`. If your app exits cleanly, it publishes `OFF`. If your app crashes or loses its connection, the broker delivers the LWT `OFF` payload automatically.

**Debug log topic**

All messages sent via `app.log` are published to `{app_name}/{hostname}/debug` in addition to the console. This lets you monitor your app's logs in real time from any MQTT client.

**JSON payload parsing**

If an incoming message payload looks like a JSON object (`{...}`), Gourd automatically parses it and makes it available as `message.json`. No setup required.

## Stopping the App

Press `Ctrl-C`. Gourd catches the interrupt, publishes the offline status payload, disconnects cleanly, and exits.

## Next Steps

- [Configuration](../configuration/) — all `Gourd()` constructor arguments
- [API Reference](../api-reference/) — `subscribe`, `publish`, `GourdMessage`, and more
- [Examples](../examples/) — copy-paste patterns for common tasks
- [Upgrading](../upgrading/) — migration guide for breaking changes
