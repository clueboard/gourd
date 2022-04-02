#!/usr/bin/env python3
import logging

from gourd import Gourd

logging.basicConfig()
app = Gourd(app_name='gourd_example', mqtt_host='172.16.22.1')


@app.subscribe('#')
def my_topic_here(message):
    print('Received message on topic', message.topic)
    print(message.payload)


if __name__ == '__main__':
    app.run_forever()
