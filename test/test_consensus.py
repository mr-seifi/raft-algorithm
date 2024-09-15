from skylab.app import Config
from skylab.rpc import Client
from skylab.storage.mongo import MongoService

NODES = [
    '209.38.184.90:40051',
    '209.38.184.90:40052',
    '209.38.184.90:40053'
]


MONGO_CONFIGS = [
    ''
]


def test_log_replication():
    Config.load()
    client = Client()

    for node in NODES:
        success, response = client.node_request(node, command='ls')
        assert success


