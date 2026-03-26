# Upgrading

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
