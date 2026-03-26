---
layout: base.njk
title: Configuration
order: 2
tags: docs
---

# Configuration

All configuration is passed to the `Gourd()` constructor when you create your app instance.

```python
app = Gourd(
    app_name='my_app',
    mqtt_host='broker.local',
    username='mqtt',
    password='secret',
)
```

`app_name` is the only required argument. It is used as the base of the auto-generated status and log topics.

---

## Connection Settings

| Argument | Default | Description |
|---|---|---|
| `app_name` | *(required)* | Application name; used as the base of auto-generated topics |
| `mqtt_host` | `'localhost'` | Hostname or IP of the MQTT broker |
| `mqtt_port` | `1883` | TCP port of the MQTT broker |
| `username` | `''` | Username for broker authentication |
| `password` | `''` | Password for broker authentication |
| `timeout` | `30` | Connection keepalive timeout in seconds |

---

## QoS and Message Buffering

| Argument | Default | Description |
|---|---|---|
| `qos` | `1` | Default QoS level for published and subscribed messages (0, 1, or 2). Can be overridden per `publish()` call. |
| `max_inflight_messages` | `20` | Maximum number of QoS > 0 messages that can be in flight simultaneously. See [paho-mqtt docs](https://eclipse.dev/paho/files/paho.mqtt.python/html/index.html) for details. |
| `max_queued_messages` | `0` | Maximum number of messages to queue when the connection is unavailable. `0` means unlimited. |

---

## Status Topic

Gourd publishes your app's online/offline state to an MQTT topic using a [Last Will and Testament](https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/). This lets other systems react to your app going offline unexpectedly.

| Argument | Default | Description |
|---|---|---|
| `status_enabled` | `True` | Set to `False` to disable status publishing entirely |
| `status_topic` | `{app_name}/{hostname}/status` | Topic to publish status to. Overrides the auto-generated default. |
| `status_online` | `'ON'` | Payload published when the app connects |
| `status_offline` | `'OFF'` | Payload published when the app exits (and set as the LWT for unexpected disconnects) |

The status message is published with `retain=True` so clients that connect after the fact still see the current state.

### Home Assistant Integration

The default `ON`/`OFF` payloads are compatible with Home Assistant's MQTT `binary_sensor`. You can track your app's availability directly in HA:

```yaml
mqtt:
  binary_sensor:
    - name: "My App"
      state_topic: "my_app/myhost/status"
      payload_on: "ON"
      payload_off: "OFF"
```

---

## MQTT Logging

By default, all messages sent via `app.log` are published to an MQTT topic in addition to the console.

| Argument | Default | Description |
|---|---|---|
| `log_mqtt` | `True` | Set to `False` to disable publishing logs to MQTT |
| `log_topic` | `{app_name}/{hostname}/debug` | Topic to publish log messages to. Overrides the auto-generated default. |

`app.log` is a standard Python `logging.Logger`. Use it like any other logger:

```python
app.log.debug('details')
app.log.info('status update')
app.log.warning('something unexpected')
app.log.error('something went wrong')
```

To see `DEBUG`-level messages on the console, call `logging.basicConfig(level=logging.DEBUG)` before creating your `Gourd` instance.

The `gourd` CLI also supports log file output and other log controls — run `gourd --help` for details.

---

## Deprecated Arguments

| Argument | Status |
|---|---|
| `message_retry_sec` | **Deprecated.** Accepted but ignored. Will be removed in a future release. |

`message_retry_sec` was used to configure paho-mqtt v1's message retry interval. paho-mqtt v2 removed that API. Passing this argument now emits a `DeprecationWarning`. Remove it from your code.

See [Upgrading](../upgrading/) for migration details.
