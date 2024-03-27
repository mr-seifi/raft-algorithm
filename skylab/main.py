import argparse
from skylab.app import Config
from skylab.rpc import compile_proto, serve
import os
import logging


def main():
    Config.load()

    parser = argparse.ArgumentParser(
        prog='Skylab',
        description='Reach consensus on everything',
    )

    parser.add_argument('-c', '--compile-proto', action='store_true')
    parser.add_argument('-s', '--run-server', action='store_true')
    args = parser.parse_args()

    if args.compile_proto:
        os.chdir("skylab/rpc/config")
        for proto_file in Config.proto_files():
            if not proto_file:
                break
            compile_proto(proto_file)
    if args.run_server:
        logging.basicConfig()
        serve(port=str(Config.grpc_server_port()),
              max_workers=10)


if __name__ == '__main__':
    main()
