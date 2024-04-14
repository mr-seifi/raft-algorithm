import logging
from enum import Enum
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
                data_type, data = MessageBroker._decode(message['data'].decode())
                callback(data_type, data)


class MessageBroker:
    class Channels(Enum):
        RPC_TO_CONSENSUS = 1  # Also REQUEST_TO_CONSENSUS
        CONSENSUS_TO_RPC = 2
        # REQUEST_TO_CONSENSUS = 3
        CONSENSUS_TO_REQUEST = 4

    def __init__(self, channel_name: Channels):
        self._channel_names = {
            1: ('rpc_to_consensus', _callback_rpc_to_consensus),
            2: ('consensus_to_rpc', _callback_consensus_to_rpc),
            # 3: ('request_to_consensus', _callback_request_to_consensus),
            4: ('consensus_to_request', _callback_consensus_to_request)
        }

        self.queue = PubSubQueue()
        self.channel_name = self._channel_names[channel_name.value][0]
        self.callback = self._channel_names[channel_name.value][1]

    def produce(self, data_type: str, data: dict):
        try:
            encoded_message = self._encode(data_type, **data)
            self.queue.publish(channel_name=self.channel_name, item=encoded_message)
            return True
        except Exception as e:
            logging.exception(f'[Exception|{self.channel_name}]')
            return False

    def consume(self):
        self.queue.subscribe(channel_name=self.channel_name, callback=self.callback)

    @staticmethod
    def _encode(data_type: str, **kwargs) -> str:
        kwargs['_data_type'] = data_type
        return json.dumps(kwargs)

    @staticmethod
    def _decode(encoded_message: str) -> (str, dict):
        message = json.loads(encoded_message)
        data_type = message['_data_type']
        return data_type, message


def _callback_rpc_to_consensus(_: str, item: dict):
    from skylab.consensus.consensus import Consensus
    Consensus.Q.put(item)


def _callback_consensus_to_rpc(data_type: str, item: dict):
    from skylab.rpc.server import Consensus
    _id = item.pop('_id')
    if data_type == 'append_entries':
        Consensus.append_entries_messages[_id] = item
    elif data_type == 'request_vote':
        Consensus.request_vote_messages[_id] = item
    elif data_type == 'add_log_request':
        Consensus.add_log_messages[_id] = item


def _callback_request_to_consensus(_: str, item: dict):
    from skylab.consensus.consensus import Consensus
    Consensus.Q.put(item)


def _callback_consensus_to_request(data_type: str, item: dict):
    from skylab.rpc.server import Node
    _id = item.pop('_id')
    if data_type == 'node_request':
        Node.requests[_id] = item
