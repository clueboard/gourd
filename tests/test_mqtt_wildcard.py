"""Unit tests for gourd.mqtt_wildcard.
"""
from gourd.mqtt_wildcard import mqtt_wildcard


def test_mqtt_wildcard_1():
    assert mqtt_wildcard('foo', 'foo') is True


def test_mqtt_wildcard_2():
    assert mqtt_wildcard('foo', 'bar') is False


def test_mqtt_wildcard_3():
    assert mqtt_wildcard('foo/baz/bar', 'foo/+/bar') is True


def test_mqtt_wildcard_4():
    assert mqtt_wildcard('foo/bar/baz', 'foo/+/bar') is False


def test_mqtt_wildcard_5():
    assert mqtt_wildcard('foo/baz/fnord/bar', 'foo/#/bar') is True


def test_mqtt_wildcard_6():
    assert mqtt_wildcard('foo/bar/fnord/baz', 'foo/#/bar') is False
