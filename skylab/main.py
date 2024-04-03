import argparse
from skylab.app import Config
from skylab.rpc import compile_proto, serve
from skylab.broker.queue import PubSubQueue, consume_by_rpc, consume_by_consensus
from skylab.consensus.consensus import Consensus
import threading
import os
import logging


def main():
    Config.load()

    logging.basicConfig(level=getattr(logging, Config.logging_level()),
                        filename=Config.logging_filename(),
                        filemode="w",
                        format="$(asctime)s-$(levelname)s-$(message)s",)

    parser = argparse.ArgumentParser(
        prog='Skylab',
        description='Reach consensus on everything',
    )

    parser.add_argument('-c', '--compile-proto', action='store_true')
    parser.add_argument('-s', '--run-server', action='store_true')
    parser.add_argument('-a', '--run-consensus', action='store_true')
    args = parser.parse_args()

    logging.info("-> SKYLAB STARTED")

    if args.compile_proto:
        os.chdir("skylab/rpc/config")
        for proto_file in Config.proto_files():
            if not proto_file:
                break
            compile_proto(proto_file)
    if args.run_server:
        pubsub_queue = PubSubQueue()
        consumer_thread = threading.Thread(target=consume_by_rpc, args=(pubsub_queue, ))
        consumer_thread.start()
        serve(host=Config.grpc_server_host(),
              port=str(Config.grpc_server_port()),
              max_workers=10)
    if args.run_consensus:
        pubsub_queue = PubSubQueue()
        consumer_thread = threading.Thread(target=consume_by_consensus, args=(pubsub_queue, ))
        consumer_thread.start()
        consensus_service = Consensus()
        consensus_service.start()


if __name__ == '__main__':
    main()
