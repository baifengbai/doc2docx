#!/usr/bin/env python
# encoding: utf-8

import pika


class RabbitMQConsumer(object):
    def __init__(self, host, queue, arguments=None):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.queue = queue
        self.channel = self.connection.channel()
        self.channel.queue_declare(self.queue, durable=True, arguments=arguments)
        self.channel.basic_qos(prefetch_count=1)

    def begin_consume(self, callback):
        self.channel.basic_consume(callback, self.queue)
        self.channel.start_consuming()

    def close(self):
        pass


class RabbitMQProducer(object):
    def __init__(self, host, queue):
        self.host = host
        self.queue = queue

    def send_message(self, message, qn=0):
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
        channel = connection.channel()
        channel.queue_declare(queue=self.queue, durable=True)
        channel.basic_publish(exchange='', routing_key=self.queue, body=message,
                              properties=pika.BasicProperties(delivery_mode=2))
        connection.close()

    def send_priority_message(self, message, priority):
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
        channel = connection.channel()
        arguments = {
            "x-max-priority": 1000
        }
        channel.queue_declare(self.queue, durable=True, arguments=arguments)
        properties = pika.BasicProperties(delivery_mode=2)
        properties.priority = priority
        channel.basic_publish(exchange='', routing_key=self.queue, body=message,
                              properties=properties)
        connection.close()

    def stop(self):
        pass


def main():
    mq = RabbitMQProducer(host='10.200.3.114', queue='pdf_test')
    for i in range(10):
        message = '23'
        mq.send_message(message=message)
        print 'success'


if __name__ == '__main__':
    main()
