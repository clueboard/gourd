# Examples

## Basic App

```python
import logging
from gourd import Gourd

logging.basicConfig()

app = Gourd(
    app_name='my_app',
    mqtt_host='broker.local',
    username='mqtt',
    password='secret',
)

@app.subscribe('#')
def print_all(message):
    print(f'{message.topic}: {message.payload}')

if __name__ == '__main__':
    app.run_forever()
```

---

## Multiple Topics, Separate Handlers

```python
@app.subscribe('lights/#')
def handle_lights(message):
    app.log.info(f'Light update: {message.topic} = {message.payload}')

@app.subscribe('sensors/#')
def handle_sensors(message):
    app.log.info(f'Sensor reading: {message.topic} = {message.payload}')
```

---

## One Handler for Multiple Topics

Stack `@app.subscribe` decorators to call the same function for multiple topics:

```python
@app.subscribe('home/kitchen/light')
@app.subscribe('home/living_room/light')
def handle_light(message):
    app.log.info(f'{message.topic} is now {message.payload}')
```

---

## Handling JSON Payloads

`message.json` is a dict when the payload parses successfully, or an empty dict `{}` when it doesn't. An empty dict is falsy, so `if message.json` is a reliable guard:

```python
@app.subscribe('sensors/+/reading')
def handle_reading(message):
    if message.json:
        temp = message.json.get('celsius')
        humidity = message.json.get('humidity')
        app.log.info(f'temp={temp}°C humidity={humidity}%')
    else:
        app.log.warning(f'Unexpected payload on {message.topic}: {message.payload!r}')
```

---

## Publishing Messages

```python
# Basic publish
app.publish('lights/kitchen', 'ON')

# With explicit QoS
app.publish('alerts/critical', 'FIRE', qos=2)

# Retained message (persisted by broker for new subscribers)
app.publish('devices/thermostat/setpoint', '72', retain=True)

# Delete a retained message (empty payload + retain=True)
app.publish('devices/thermostat/setpoint', None, retain=True)
```

---

## Background Thread with Main-Thread Loop

Use `loop_start()` when you need the main thread for your own work (e.g. polling a sensor):

```python
import time
import logging
from gourd import Gourd

logging.basicConfig()

app = Gourd(app_name='sensor_publisher', mqtt_host='broker.local')

@app.subscribe('commands/#')
def handle_command(message):
    app.log.info(f'Command received: {message.topic} = {message.payload}')

app.loop_start()

try:
    while True:
        value = read_sensor()  # your sensor reading function
        app.publish('sensors/temperature', str(value))
        time.sleep(10)
except KeyboardInterrupt:
    pass
finally:
    app.loop_stop()
```

---

## Disable Automatic Features

For a minimal footprint app with no status topic or MQTT logging:

```python
app = Gourd(
    app_name='minimal_app',
    mqtt_host='broker.local',
    log_mqtt=False,       # don't publish logs to MQTT
    status_enabled=False, # don't publish online/offline status
)
```

---

## CLI with a Non-Standard Module Location

If your app module is not in the current directory, use `--sys-path` to add it:

```shell
gourd --sys-path /opt/myapps mymodule:app
```

You can pass `--sys-path` multiple times to add several paths. Run `gourd --help` to see all available CLI options.
