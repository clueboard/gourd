import re


def _validate_wildcard(pattern):
    """Raises ValueError if pattern is not a valid MQTT topic filter."""
    levels = pattern.split('/')
    for i, level in enumerate(levels):
        if '#' in level:
            if level != '#':
                raise ValueError(
                    f"Invalid MQTT topic filter: '#' must occupy an entire level: {pattern!r}"
                )
            if i != len(levels) - 1:
                raise ValueError(
                    f"Invalid MQTT topic filter: '#' must be the last level: {pattern!r}"
                )
        if '+' in level and level != '+':
            raise ValueError(
                f"Invalid MQTT topic filter: '+' must occupy an entire level: {pattern!r}"
            )


def mqtt_wildcard(topic, wildcard):
    """Returns True if topic matches the wildcard string.

    Raises ValueError for malformed wildcard patterns.
    """
    _validate_wildcard(wildcard)

    levels = wildcard.split('/')
    regex_levels = []

    for i, level in enumerate(levels):
        if level == '#':
            # Validated to be the last level; matches parent and all subtopics
            if i == 0:
                regex = '.*'
            else:
                regex = '/'.join(regex_levels) + '(/.*)?'
            return bool(re.fullmatch(regex, topic))
        elif level == '+':
            regex_levels.append('[^/]*')
        else:
            regex_levels.append(re.escape(level))

    return bool(re.fullmatch('/'.join(regex_levels), topic))
