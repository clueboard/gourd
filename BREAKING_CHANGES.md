# Breaking Changes

## gourd 1.0.0

### paho-mqtt upgraded from v1 to v2

gourd now requires `paho-mqtt>=2`. If you are upgrading from a previous version:

**`message_retry_sec` is deprecated**

The `message_retry_sec` argument to `Gourd()` is no longer functional. paho-mqtt v2
removed the underlying `message_retry_set()` API. Passing this argument will emit a
`DeprecationWarning` and has no effect. It will be removed in a future release.

Before:

```python
app = Gourd(app_name='my_app', message_retry_sec=10)
```

After (remove the argument):

```python
app = Gourd(app_name='my_app')
```
