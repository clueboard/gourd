"""Unit tests for gourd.mqtt_wildcard.
"""
import pytest
from gourd.mqtt_wildcard import mqtt_wildcard


def test_mqtt_wildcard_1():
    assert mqtt_wildcard('foo', 'foo') is True


def test_mqtt_wildcard_2():
    assert mqtt_wildcard('foo', 'bar') is False


def test_mqtt_wildcard_3():
    assert mqtt_wildcard('foo/baz/bar', 'foo/+/bar') is True


def test_mqtt_wildcard_4():
    assert mqtt_wildcard('foo/bar/baz', 'foo/+/bar') is False


def test_mqtt_wildcard_hash_matches_parent():
    assert mqtt_wildcard('foo', 'foo/#') is True


def test_mqtt_wildcard_hash_matches_child():
    assert mqtt_wildcard('foo/bar', 'foo/#') is True


def test_mqtt_wildcard_hash_matches_deep():
    assert mqtt_wildcard('foo/bar/baz', 'foo/#') is True


def test_mqtt_wildcard_hash_no_match():
    assert mqtt_wildcard('bar/baz', 'foo/#') is False


def test_mqtt_wildcard_hash_alone_matches_everything():
    assert mqtt_wildcard('foo/bar/baz', '#') is True


def test_mqtt_wildcard_invalid_hash_not_last():
    with pytest.raises(ValueError):
        mqtt_wildcard('foo/baz/fnord/bar', 'foo/#/bar')


def test_mqtt_wildcard_invalid_hash_embedded():
    with pytest.raises(ValueError):
        mqtt_wildcard('foo#', 'foo#')


def test_mqtt_wildcard_invalid_plus_embedded():
    with pytest.raises(ValueError):
        mqtt_wildcard('foobar', 'foo+bar')
