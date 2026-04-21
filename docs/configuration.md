---
layout: base.njk
title: Configuration
order: 2
tags: docs
---

# Configuration

Gourd is configured through the `Gourd()` constructor:

```python
app = Gourd(
    app_name='my_app',
    mqtt_host='broker.local',
    username='mqtt',
    password='secret',
)
```

`app_name` is the only required argument. By default, topic values are generated from `{app_name}/{hostname}` unless overridden with `mqtt_topic`.

Constructor defaults can be overridden at runtime via command-line flags, environment variables, or a config file. Gourd uses [MILC](https://milc.clueboard.co/) to resolve values in this order:

1. **Command-line argument** (`--mqtt-host broker.local`)
2. **Environment variable** (`MQTT_HOST=broker.local`)
3. **Config file** (INI-style under the `[general]` section)
4. **Constructor default** (the value passed in your Python code)

---

## Naming Convention

CLI flags, environment variables, and config file tokens share the same naming scheme. Given a CLI flag, you can derive the other forms:

- **CLI flag**: `--mqtt-host 127.0.0.1`
- **Environment variable**: strip the leading `--`, replace `-` with `_`, uppercase → `MQTT_HOST=127.0.0.1`
- **Config file token**: strip the leading `--`, replace `-` with `_`, place in the `general` section → 
    - in code: `cli.config.general.mqtt_host`
    - in config file:  
```
[general]
mqtt_host = 127.0.0.1
```

---

## Config File

The file format is [ConfigParser](https://docs.python.org/3/library/configparser.html) INI style. Settings go under the `[general]` section:

```ini
[general]
mqtt_host = broker.local
mqtt_port = 1883
mqtt_username = mqtt
mqtt_password = secret
```

Use `--config-file` to specify a config file path:

```shell
gourd --config-file /etc/gourd/my_app.ini my_app:app
```

---

## Settings Reference

| Setting | Constructor Arg | CLI Flag | Env Var | Default |
|---|---|---|---|---|
| Application name | `app_name` | — | — | *(required)* |
| MQTT host | `mqtt_host` | `--mqtt-host` | `MQTT_HOST` | `'localhost'` |
| MQTT port | `mqtt_port` | `--mqtt-port` | `MQTT_PORT` | `1883` |
| MQTT username | `username` | `--mqtt-username` | `MQTT_USERNAME` | `''` |
| MQTT password | `password` | `--mqtt-password` | `MQTT_PASSWORD` | `''` |
| MQTT topic base | `mqtt_topic` | — | — | `{app_name}/{hostname}` |
| [MQTT QoS](https://eclipse.dev/paho/files/mqttdoc/MQTTClient/html/qos.html) | `qos` | `--qos` | `QOS` | `1` |
| Keepalive timeout (seconds) | `timeout` | `--timeout` | `TIMEOUT` | `30` |
| Enable [LWT](https://eclipse.dev/paho/files/mqttdoc/MQTTClient/html/struct_m_q_t_t_client__will_options.html) status | `status_enabled` | `--status-enabled` / `--no-status-enabled` | `STATUS_ENABLED` | `True` |
| Status topic | `status_topic` | — | — | `{mqtt_topic}/status` |
| Status online payload | `status_online` | — | — | `'ON'` |
| Status offline payload | `status_offline` | — | — | `'OFF'` |
| Enable MQTT logging | `log_mqtt` | `--log-mqtt` / `--no-log-mqtt` | `LOG_MQTT` | `True` |
| Log topic | `mqtt_log_topic` | `--log-mqtt-topic` | `LOG_MQTT_TOPIC` | `{mqtt_topic}/debug` |
| Log topic (deprecated alias) | `log_topic` | — | — | `None` |
| Max in-flight messages | `max_inflight_messages` | `--max-inflight-messages` | `MAX_INFLIGHT_MESSAGES` | `20` |
| Max queued messages | `max_queued_messages` | `--max-queued-messages` | `MAX_QUEUED_MESSAGES` | `0` (unlimited) |
| Enable TLS | `tls_enabled` | `--tls-enabled` / `--no-tls-enabled` | `TLS_ENABLED` | `False` |
| Verify TLS cert + hostname | `tls_verify` | `--tls-verify` / `--no-tls-verify` | `TLS_VERIFY` | `True` |
| Trusted CA bundle (root/intermediate) | `tls_ca_certs` | `--tls-ca-certs` | `TLS_CA_CERTS` | `None` |
| Client certificate (optionally with chain) | `tls_certfile` | `--tls-certfile` | `TLS_CERTFILE` | `None` |
| Client private key | `tls_keyfile` | `--tls-keyfile` | `TLS_KEYFILE` | `None` |

`--mqtt-username` and `--mqtt-password` must be provided together at runtime.

`tls_verify` is only relevant when TLS is enabled (`tls_enabled=True` or TLS cert paths are provided).

---

## Status Topic

Gourd publishes your app's online/offline state using a [Last Will and Testament](https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/). This lets other systems react to your app going offline unexpectedly.

The status message is published with `retain=True` so clients that connect after the fact still see the current state.

### Home Assistant Integration

The default `ON`/`OFF` payloads are compatible with Home Assistant's MQTT `binary_sensor`:

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

`app.log` is a standard Python `logging.Logger`:

```python
app.log.debug('details')
app.log.info('status update')
app.log.warning('something unexpected')
app.log.error('something went wrong')
```

To see `DEBUG`-level messages on the console, call `logging.basicConfig(level=logging.DEBUG)` before creating your `Gourd` instance.

The `gourd` CLI also supports log file output and other log controls — run `gourd --help` for details.

---

## Examples

Run your app against a different broker using an environment variable:

```shell
MQTT_HOST=broker.local gourd my_app:app
```

Or use command-line flags:

```shell
gourd --mqtt-host broker.local --mqtt-username mqtt --mqtt-password secret my_app:app
```

TLS example with custom trust and mTLS files:

```shell
gourd --mqtt-host broker.local --mqtt-port 8883 --tls-enabled \
  --tls-ca-certs /etc/ssl/my-ca-chain.pem \
  --tls-certfile /etc/ssl/client-chain.pem \
  --tls-keyfile /etc/ssl/client.key \
  my_app:app
```

To disable broker certificate/hostname verification (not recommended outside controlled environments):

```shell
gourd --tls-enabled --no-tls-verify my_app:app
```

---

## Deprecated Arguments

| Argument | Status |
|---|---|
| `message_retry_sec` | **Deprecated.** Accepted but ignored. Will be removed in a future release. |

`message_retry_sec` was used to configure paho-mqtt v1's message retry interval. paho-mqtt v2 removed that API. Passing this argument now emits a `DeprecationWarning`. Remove it from your code.

See [Upgrading](../upgrading/) for migration details.
