# Gourd - An MQTT framework

Gourd is an opinionated framework for writing MQTT applications. 

# Simple example

```python
from gourd import Gourd

mqtt = Gourd(app_name='my_app', server='localhost', port=1883, user='mqtt', password='my_password')


@mqtt.subscribe('#')
def print_all_messages(message):
    print(f'{message.topic}: {message.payload}')


if __name__ == '__main__':
    mqtt.run_forever()
```

# Features

* Create a fully-functional MQTT app in minutes
* Status published to `<app_name>/<hostname>/status` with a Last Will and Testament
* Use decorators to associate topics with functions

# Installation

Gourd is available on pypi, you can use pip to install it:

    python3 -m pip install gourd

# Documentation

WIP

# Reporting Bugs and Requesting Features

Please let us know about any bugs and/or feature requests you have: <>

# Contributing

Contributions are welcome! You don't need to open an issue first, if
you've developed a new feature or fixed a bug in Gourd simply open
a PR and we'll review it.

Please follow this checklist before submitting a PR:

* [ ] Format your code: `yapf -i -r .`
