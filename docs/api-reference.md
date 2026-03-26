---
layout: base.njk
title: API Reference
order: 3
tags: docs
---

# API Reference

## `Gourd.subscribe(topic)`

A decorator that registers a function as a handler for an MQTT topic. When a message arrives on a matching topic, Gourd calls the function with a [`GourdMessage`](#gourdmessage) argument.

```python
@app.subscribe('sensors/temperature')
def handle_temp(message):
    app.log.info(f'Temperature: {message.payload}')
```

Registering the handler also subscribes to the topic on the broker — you don't need to call anything else.

### Wildcard Patterns

MQTT supports two wildcard characters in topic filters:

| Wildcard | Meaning | Example pattern | Matches | Does not match |
|---|---|---|---|---|
| `+` | Single level (one segment between `/`) | `sensors/+/temp` | `sensors/room1/temp` | `sensors/room1/humidity`, `sensors/a/b/temp` |
| `#` | Multi-level (parent and all subtopics; must be last) | `sensors/#` | `sensors`, `sensors/room1`, `sensors/room1/temp` | `other/topic` |
| `#` alone | Everything | `#` | any topic | — |

Malformed patterns (e.g. `foo+bar`, `home/#/temp`) raise `ValueError` at match time.

### Multiple Handlers

You can register multiple functions for the same topic. They are called in registration order. An exception in one handler does not prevent others from running.

```python
@app.subscribe('sensors/temperature')
def log_temp(message):
    app.log.info(message.payload)

@app.subscribe('sensors/temperature')
def store_temp(message):
    db.insert(message.payload)
```

### One Handler for Multiple Topics

Stack decorators to register the same function for multiple topics:

```python
@app.subscribe('sensors/temperature')
@app.subscribe('sensors/humidity')
def handle_sensor(message):
    app.log.info(f'{message.topic}: {message.payload}')
```

---

## `Gourd.publish(topic, payload=None, *, qos=None, **kwargs)`

Publishes a message to the MQTT broker.

```python
app.publish('lights/kitchen', 'ON')
app.publish('lights/kitchen', 'ON', retain=True)
app.publish('lights/kitchen', None, retain=True)  # delete retained message
```

- `qos` — overrides the instance default if provided
- All additional keyword arguments are forwarded to paho-mqtt's `publish()` (e.g. `retain=True`)
- Pass `payload=None` to publish an empty message; combined with `retain=True` this deletes any retained message on that topic

---

## `Gourd.run_forever()`

Connects to the broker and runs the MQTT loop in the current thread until interrupted.

```python
if __name__ == '__main__':
    app.run_forever()
```

This is the normal way to run a Gourd app. It handles `KeyboardInterrupt` (Ctrl-C) gracefully and triggers clean shutdown via the registered `atexit` handler.

The `gourd` CLI calls `run_forever()` for you when you use the `gourd module:app` command.

---

## `Gourd.loop_start()` / `Gourd.loop_stop()`

Runs the MQTT loop in a background thread, returning immediately so the calling thread can do other work.

```python
app.loop_start()

try:
    while True:
        value = read_sensor()
        app.publish('sensors/temperature', str(value))
        time.sleep(5)
except KeyboardInterrupt:
    pass
finally:
    app.loop_stop()
```

- `loop_start()` calls `connect()` automatically if not already connected
- `loop_stop()` stops the background thread

---

## `Gourd.connect()`

Connects to the MQTT broker. Called automatically by `run_forever()` and `loop_start()`.

Only call this directly if you are managing the paho-mqtt loop yourself.

---

## `GourdMessage`

The object passed to every subscriber function. It wraps the underlying paho-mqtt message with convenient properties.

### Properties

**`message.topic`** — `str`

The exact topic the message arrived on (not the wildcard pattern used to subscribe).

```python
@app.subscribe('sensors/+/temp')
def handle(message):
    print(message.topic)  # e.g. "sensors/room1/temp"
```

**`message.payload`** — `str`

The message payload decoded as UTF-8, with leading and trailing whitespace stripped.

**`message.json`** — `dict`

If the payload looks like a JSON object (starts with `{` and ends with `}`), this is the parsed result. Otherwise it is an empty dict `{}`.

**Important:** `message.json` returns `{}` (empty dict) when parsing fails or the payload is not a JSON object — it never returns `None` and never raises an exception. An empty dict is falsy, so use `if message.json` to check whether parsing succeeded.

```python
@app.subscribe('sensors/#')
def handle(message):
    if message.json:
        temp = message.json.get('celsius')
    else:
        # plain string payload
        raw = message.payload
```

**All other attributes** delegate to the underlying `paho.mqtt.client.MQTTMessage`, including `qos`, `retain`, `mid`, `timestamp`, etc.

---

## `app.log`

A standard Python `logging.Logger` instance. It is pre-configured to send log output to both the console and the MQTT debug topic (`{app_name}/{hostname}/debug` by default).

```python
app.log.debug('detailed trace')
app.log.info('normal status')
app.log.warning('unexpected but handled')
app.log.error('something failed')
```

See [Configuration — MQTT Logging](configuration.md#mqtt-logging) for options.
