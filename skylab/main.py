import argparse
from skylab.app import Config
from skylab.rpc import compile_proto, serve_consensus, serve_request
from skylab.broker import MessageBroker
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
        message_broker = MessageBroker(channel_name=MessageBroker.Channels.CONSENSUS_TO_RPC)
        consumer = threading.Thread(target=message_broker.consume, args=())
        consumer.start()
        serve_consensus(host=Config.grpc_consensus_server_host(),
                        port=str(Config.grpc_consensus_server_port()),
                        max_workers=10)
    if args.run_request_server:
        logging.basicConfig(level=getattr(logging, Config.logging_level()),
                            filename=Config.logging_filename(),
                            filemode="a",
                            format="%(asctime)s - %(levelname)s - REQUEST_SERVER - %(message)s", )
        logging.info("-> SKYLAB STARTED")
        message_broker = MessageBroker(channel_name=MessageBroker.Channels.CONSENSUS_TO_REQUEST)
        consumer = threading.Thread(target=message_broker.consume, args=())
        consumer.start()
        serve_request(host=Config.grpc_request_server_host(),
                      port=str(Config.grpc_request_server_port()),
                      max_workers=10)
    if args.run_consensus:
        logging.basicConfig(level=getattr(logging, Config.logging_level()),
                            filename=Config.logging_filename(),
                            filemode="a",
                            format="%(asctime)s - %(levelname)s - CONSENSUS_PROTOCOL - %(message)s", )
        logging.info("-> SKYLAB STARTED")
        rpc_message_broker = MessageBroker(channel_name=MessageBroker.Channels.RPC_TO_CONSENSUS)
        rpc_consumer = threading.Thread(target=rpc_message_broker.consume, args=())
        rpc_consumer.start()
        request_message_broker = MessageBroker(channel_name=MessageBroker.Channels.REQUEST_TO_CONSENSUS)
        request_consumer = threading.Thread(target=request_message_broker.consume, args=())
        request_consumer.start()
        consensus_service = Consensus()
        consensus_service.start()


if __name__ == '__main__':
    main()
