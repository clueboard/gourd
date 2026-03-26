"""Unit tests for gourd.gourd_message.GourdMessage."""
import json
from unittest.mock import MagicMock, patch
from gourd.gourd_message import GourdMessage


def make_paho_msg(payload, topic='test/topic'):
    msg = MagicMock()
    msg.topic = topic
    if isinstance(payload, bytes):
        msg.payload = payload
    else:
        msg.payload = payload.encode('utf-8')
    return msg


def test_bytes_payload_decoded():
    msg = GourdMessage(make_paho_msg(b'hello'))
    assert msg.payload == 'hello'


def test_payload_stripped():
    msg = GourdMessage(make_paho_msg(b'  hello\n'))
    assert msg.payload == 'hello'


def test_string_payload_passed_through():
    paho_msg = MagicMock()
    paho_msg.payload = 'already a string'
    msg = GourdMessage(paho_msg)
    assert msg.payload == 'already a string'


def test_json_valid():
    msg = GourdMessage(make_paho_msg(b'{"key": "value"}'))
    assert msg.json == {'key': 'value'}


def test_json_invalid_returns_empty_dict(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger='gourd.gourd_message'):
        msg = GourdMessage(make_paho_msg(b'{not valid json}'))
        assert msg.json == {}
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'


def test_json_empty_payload_returns_empty_dict():
    msg = GourdMessage(make_paho_msg(b''))
    assert msg.json == {}


def test_json_non_object_returns_empty_dict():
    msg = GourdMessage(make_paho_msg(b'"just a string"'))
    assert msg.json == {}


def test_json_cached():
    with patch('gourd.gourd_message.json.loads', wraps=json.loads) as mock_loads:
        msg = GourdMessage(make_paho_msg(b'{"a": 1}'))
        _ = msg.json
        _ = msg.json
        assert mock_loads.call_count == 1


def test_getattr_proxies_to_paho_message():
    paho_msg = make_paho_msg(b'data')
    paho_msg.qos = 1
    msg = GourdMessage(paho_msg)
    assert msg.qos == 1


def test_topic_proxied():
    paho_msg = make_paho_msg(b'data', topic='foo/bar')
    msg = GourdMessage(paho_msg)
    assert msg.topic == 'foo/bar'
