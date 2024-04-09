import argparse
from skylab.app import Config
from skylab.rpc import compile_proto, serve_consensus, serve_request
from skylab.broker.queue import PubSubQueue, consume_by_rpc, consume_by_consensus
from skylab.consensus.consensus import Consensus
import threading
import os
import logging


def main():
    Config.load()

    parser = argparse.ArgumentParser(
        prog='Skylab',
        description='Reach consensus on everything',
    )

    parser.add_argument('-c', '--compile-proto', action='store_true')
    parser.add_argument('-s', '--run-consensus-server', action='store_true')
    parser.add_argument('-sr', '--run-request-server', action='store_true')
    parser.add_argument('-a', '--run-consensus', action='store_true')
    args = parser.parse_args()

    if args.compile_proto:
        os.chdir("skylab/rpc/config")
        for proto_file in Config.proto_files():
            if not proto_file:
                break
            compile_proto(proto_file)
    if args.run_consensus_server:
        logging.basicConfig(level=getattr(logging, Config.logging_level()),
                            filename=Config.logging_filename(),
                            filemode="a",
                            format="%(asctime)s - %(levelname)s - CONSENSUS_SERVER - %(message)s", )
        logging.info("-> SKYLAB STARTED")
        pubsub_queue = PubSubQueue()
        consumer_by_consensus = threading.Thread(target=consume_by_consensus, args=(pubsub_queue,))
        consumer_by_consensus.start()
        serve_consensus(host=Config.grpc_consensus_server_host(),
                        port=str(Config.grpc_consensus_server_port()),
                        max_workers=10)
    if args.run_request_server:
        logging.basicConfig(level=getattr(logging, Config.logging_level()),
                            filename=Config.logging_filename(),
                            filemode="a",
                            format="%(asctime)s - %(levelname)s - REQUEST_SERVER - %(message)s", )
        logging.info("-> SKYLAB STARTED")
        pubsub_queue = PubSubQueue()
        consumer_by = threading.Thread(target=consume_by_rpc, args=(pubsub_queue,))
        consumer_by.start()
        serve_request(host=Config.grpc_request_server_host(),
                      port=str(Config.grpc_request_server_port()),
                      max_workers=10)
    if args.run_consensus:
        logging.basicConfig(level=getattr(logging, Config.logging_level()),
                            filename=Config.logging_filename(),
                            filemode="a",
                            format="%(asctime)s - %(levelname)s - CONSENSUS_PROTOCOL - %(message)s", )
        logging.info("-> SKYLAB STARTED")
        consensus_service = Consensus()
        consensus_service.start()


if __name__ == '__main__':
    main()
