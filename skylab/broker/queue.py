import redis
import threading
from skylab.app.config import Config


class PubSubQueue:
    def __init__(self):
        self.redis_conn = redis.Redis(host=Config.redis_host(),
                                      port=Config.redis_port())
        self.pubsub = self.redis_conn.pubsub()

    def publish(self, channel_name: str, item):
        self.redis_conn.publish(channel_name, item)

    def subscribe(self, channel_name: str, callback):
        self.pubsub.subscribe(channel_name)
        thread = threading.Thread(target=self._listen, args=(callback,))
        thread.daemon = True
        thread.start()

    def _listen(self, callback):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                callback(message['data'])


def produce_by_rpc(queue, data):
    for item in data:
        queue.publish(channel_name='rpc_to_consensus', item=item)
        print(f"Published {item} to the channel")


def consume_by_consensus(queue, callback):
    queue.subscribe(channel_name='rpc_to_consensus', callback=callback)


# TODO: Encode Messages


def produce_by_consensus(queue, data):
    for item in data:
        queue.publish(channel_name='consensus_to_rpc', item=item)
        print(f"Published {item} to the channel")


def consume_by_rpc(queue, callback):
    queue.subscribe(channel_name='consensus_to_rpc', callback=callback)


class RedisQueue:
    def __init__(self):
        self.redis_conn = redis.Redis(host=Config.redis_host(),
                                      port=Config.redis_port())
        self.append_entries_queue = Config.redis_append_entries_queue()
        self.request_vote_queue = Config.redis_request_vote_queue()

    def put_append_entry(self, item):
        self.redis_conn.rpush(self.append_entries_queue, item)

    def get_append_entry(self, timeout=0):
        return self.redis_conn.blpop([self.append_entries_queue], timeout=timeout)[1]

    def put_request_vote(self, item):
        self.redis_conn.rpush(self.request_vote_queue, item)

    def get_request_vote(self, timeout=0):
        return self.redis_conn.blpop([self.request_vote_queue], timeout=timeout)[1]

    def consume(self):
        while True:
            received_append_entry = self.get_append_entry()
            if received_append_entry:
                print(f"Processing {received_append_entry}")

            received_vote_request = self.get_request_vote()
            if received_vote_request:
                print(f"Processing {received_vote_request}")
