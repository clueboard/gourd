import re


def mqtt_wildcard(topic, wildcard):
    """Returns True if topic matches the wildcard string.
    """
    regex = wildcard.replace('.', r'\.').replace('#', '.*').replace('+', '[^/]*')

    if re.fullmatch(regex, topic):
        return True

    return False
