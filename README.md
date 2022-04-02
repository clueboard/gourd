# Gourd - An MQTT framework

Gourd is an opinionated framework for writing MQTT applications. 

# Simple example

Create a file `gourd_example.py`:

```python
from gourd import Gourd

app = Gourd(app_name='my_app', mqtt_host='localhost', mqtt_port=1883, username='mqtt', password='my_password')


@app.subscribe('#')
def print_all_messages(message):
    app.log.info(f'{message.topic}: {message.payload}')
```

Run it:

```shell
$ gourd gourd_example:app
```

# Features

* Create a fully-functional MQTT app in minutes
* Status published to `<app_name>/<hostname>/status` with a Last Will and Testament
* Debug logs published to `<app_name>/<hostname>/debug`
* Use decorators to associate topics with one or more functions

# Documentation

## Installation

Gourd is available on pypi and can be installed with pip:

    python3 -m pip install gourd

## API Reference

### `Gourd` objects

To create your app you'll need an instance of the Gourd class. Unless your MQTT server is running on your local machine with no authentication you'll need to pass in some arguments:

```python
class Gourd:
    def __init__(self, app_name, *, mqtt_host='localhost', mqtt_port=1883, username='', password='', qos=1, timeout=30, log_mqtt=True, log_topic=None, status_enabled=True, status_topic=None, status_online='ON', status_offline='OFF', max_inflight_messages=20, max_queued_messages=0, message_retry_sec=5):
```

#### Recommended arguments

These are the arguments you should almost always use:

* mqtt_host
    * Default: `localhost`
    * The MQTT server to connect to
* username
    * Default: ``
    * The username to connect to the MQTT server with
* password
    * Default: ``
    * The password to connect to the MQTT server with

#### Optional arguments

These are the arguments that only need to be set if the default behavior does not work for your application:

* mqtt_port
    * Default: `1883`
    * The port number to connect to
* qos
    * Default: `1`
    * Default QOS Level for messages
* timeout
    * Default: `30`
    * The timeout for the MQTT connection
* log_mqtt
    * Default: `True`
    * Set to false to disable mqtt logging
* log_topic
    * Default: Generated based on app_name and hostname: `{app_name}/{gethostname()}/debug`
    * The MQTT topic to send debug logs to
* status_enabled
    * Default: ``
    * Set to false to disable the status topic
* status_topic
    * Default: Generated based app_name and hostname: `{app_name}/{gethostname()}/status`
    * The topic to publish application status (ON/OFF) to
* status_online
    * Default: `ON`
    * The payload to publish to status_topic when we are running
* status_offline
    * Default: `OFF`
    * The payload to publish to status_topic when we are not running
* max_inflight_messages
    * Default: `20`
    * How many messages can be in-flight. See [Paho MQTT documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#option-functions) for more details.
* max_queued_messages
    * Default: `0`
    * How many messages can be queued at a time. See [Paho MQTT documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#option-functions) for more details.
* message_retry_sec
    * Default: `5`
    * How long to wait before retrying messages. See [Paho MQTT documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#option-functions) for more details.

### `subscribe` Decorators

Once you've instaniated your gourd object you can use the `subscribe` decorator to subscribe to a topic. This will both subscribe to the specified topic and register your function to be called when a message for that topic is received. You can register multiple functions for the same topic and they will be called in the order they were registered.

```python
    def subscribe(self, topic):
```

## Logging

By default all logging will be sent to both the console and to the `status_topic` on the MQTT server.

### Logging to a file

You can also log to a file with `gourd --log-file <path>`. There are more ways to control the log output, see `gourd --help` for details.

### Logging to the MQTT server

By default your app will log to the topic `{app_name}/{gethostname()}/debug`. You can disable this behavior by passing `log_mqtt=False` when you instaniate `Gourd`.

### Sending Log Messages

A logger has been provided for you to use, no setup needed. Just use `app.log.<level>()` to log your messages.

## Last Will and Testament

By default your app will publish its online status and a LWT to `{app_name}/{gethostname()}/status`. You can disable this behavior by passing `status_enabled=False` when instaniating `Gourd`.

# Reporting Bugs and Requesting Features

Please let us know about any bugs and/or feature requests you have: <https://github.com/clueboard/gourd/issues>

# Contributing

Contributions are welcome! You don't need to open an issue first, if
you've developed a new feature or fixed a bug in Gourd simply open
a PR and we'll review it.

Please follow this checklist before submitting a PR:

* [ ] Format your code: `yapf -i -r .`
