import logging

import redis
import threading
from skylab.app.config import Config
import json


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
                data_type, data = _decode(message['data'].decode())
                callback(data_type, data)


def produce_by_rpc(queue: PubSubQueue, data_type: str, data: dict) -> bool:
    try:
        encoded_message = _encode(data_type, **data)
        queue.publish(channel_name='rpc_to_consensus', item=encoded_message)
        return True
    except Exception as e:
        logging.exception('[Exception|produce_by_rpc]')
        return False


def consume_by_consensus(queue: PubSubQueue):
    queue.subscribe(channel_name='rpc_to_consensus', callback=_callback_rpc_to_consensus)


def produce_by_consensus(queue: PubSubQueue, data_type: str, data: dict):
    try:
        encoded_message = _encode(data_type, **data)
        queue.publish(channel_name='consensus_to_rpc', item=encoded_message)
        return True
    except Exception as e:
        logging.exception('[Exception|produce_by_consensus]')
        return False


def consume_by_rpc(queue: PubSubQueue):
    queue.subscribe(channel_name='consensus_to_rpc', callback=_callback_consensus_to_rpc)


def _encode(data_type: str, **kwargs) -> str:
    kwargs['_data_type'] = data_type
    return json.dumps(kwargs)


def _decode(encoded_message: str) -> (str, dict):
    message = json.loads(encoded_message)
    data_type = message['_data_type']
    return data_type, message


def _callback_rpc_to_consensus(_: str, item: dict):
    from skylab.consensus.consensus import Consensus
    Consensus.Q.put(item)


def _callback_consensus_to_rpc(data_type: str, item: dict):
    from skylab.rpc.server import Consensus, Request
    _id = item.pop('_id')
    if data_type == 'append_entries':
        Consensus.append_entries_messages[_id] = item
    elif data_type == 'request_vote':
        Consensus.request_vote_messages[_id] = item
    elif data_type == 'add_log_request':
        Request.requests[_id] = item
