---
layout: base.njk
title: Upgrading
order: 6
tags: docs
---

# Upgrading

## Upgrading to 2.0.0

### `message.json` now returns `None` on failure instead of `{}`

Previously, `message.json` returned an empty dict `{}` when the payload could not be decoded or was not a JSON object. It now returns `None`.

Code that distinguishes a failed parse from a successfully parsed empty-ish result should be updated. Code that simply uses `if message.json:` as a truthy check will continue to work unchanged, since both `None` and `{}` are falsy.

**Before** — guarded by truthiness (still works):

```python
@app.subscribe('sensors/#')
def handle(message):
    if message.json:
        temp = message.json.get('celsius')
```

**Before** — explicit empty-dict check (must update):

```python
@app.subscribe('sensors/#')
def handle(message):
    if message.json != {}:
        temp = message.json.get('celsius')
```

**After** — check against `None` if an explicit check is needed:

```python
@app.subscribe('sensors/#')
def handle(message):
    if message.json is not None:
        temp = message.json.get('celsius')
```

---

### `message.payload` now preserves the original MQTT payload

In previous releases, `message.payload` was decoded as UTF-8 text and stripped. In 2.0.0, `message.payload` preserves the original payload from paho-mqtt unchanged, which is typically `bytes`.

Use `message.text` when you want UTF-8 decoded text. This keeps binary payloads available without losing the original bytes.

**Before:**

```python
@app.subscribe('sensors/#')
def handle_sensor(message):
    app.log.info(f'{message.topic}: {message.payload}')
```

**After** — use `message.text` for decoded text payloads:

```python
@app.subscribe('sensors/#')
def handle_sensor(message):
    app.log.info(f'{message.topic}: {message.text}')
```

---

## Upgrading to 1.0.0

### paho-mqtt upgraded from v1 to v2

Gourd 1.0.0 requires `paho-mqtt>=2`. If you are upgrading from an earlier version of Gourd, update paho-mqtt:

```shell
pip install --upgrade paho-mqtt
```

### `message_retry_sec` is deprecated

The `message_retry_sec` argument to `Gourd()` is no longer functional. paho-mqtt v2 removed the underlying `message_retry_set()` API. Passing this argument now emits a `DeprecationWarning` and has no effect. It will be removed in a future release.

**Before:**

```python
app = Gourd(app_name='my_app', message_retry_sec=10)
```

**After** — remove the argument:

```python
app = Gourd(app_name='my_app')
```

---

<!-- When adding a new release section, copy this template:

## Upgrading to X.Y.Z

### Change title

Description of the breaking change and why it was made.

**Before:**

```python
# old code
```

**After:**

```python
# new code
```

-->
