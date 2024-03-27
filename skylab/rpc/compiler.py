import grpc_tools.protoc
import os


def compile_proto(proto_file):
    grpc_tools.protoc.main([
        'grpc_tools.protoc',
        '-I../protos',
        '--python_out=.',
        '--pyi_out=.',
        '--grpc_python_out=.',
        '../protos/{0}'.format(proto_file)
    ])

    proto_name = proto_file.split('.')[0]
    os.system("bash -c 'cat {0}_pb2_grpc.py | sed \"s/import {0}_pb2 as {0}__pb2/from ".format(proto_name) +
              ". import {0}_pb2 as {0}__pb2/g\" > {0}_pb2_grpcc.py && mv {0}_pb2_grpcc.py".format(proto_name) +
              " {0}_pb2_grpc.py'".format(proto_name))
