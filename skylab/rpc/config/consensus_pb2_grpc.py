# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import consensus_pb2 as consensus__pb2


class ConsensusStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SayHello = channel.unary_unary(
                '/consensus.Consensus/SayHello',
                request_serializer=consensus__pb2.HelloRequest.SerializeToString,
                response_deserializer=consensus__pb2.HelloResponse.FromString,
                )
        self.AppendEntries = channel.unary_unary(
                '/consensus.Consensus/AppendEntries',
                request_serializer=consensus__pb2.AppendEntriesRequest.SerializeToString,
                response_deserializer=consensus__pb2.AppendEntriesResponse.FromString,
                )
        self.RequestVote = channel.unary_unary(
                '/consensus.Consensus/RequestVote',
                request_serializer=consensus__pb2.RequestVoteRequest.SerializeToString,
                response_deserializer=consensus__pb2.RequestVoteResponse.FromString,
                )
        self.AddLog = channel.unary_unary(
                '/consensus.Consensus/AddLog',
                request_serializer=consensus__pb2.AddLogRequest.SerializeToString,
                response_deserializer=consensus__pb2.AddLogResponse.FromString,
                )


class ConsensusServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SayHello(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AppendEntries(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestVote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddLog(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ConsensusServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SayHello': grpc.unary_unary_rpc_method_handler(
                    servicer.SayHello,
                    request_deserializer=consensus__pb2.HelloRequest.FromString,
                    response_serializer=consensus__pb2.HelloResponse.SerializeToString,
            ),
            'AppendEntries': grpc.unary_unary_rpc_method_handler(
                    servicer.AppendEntries,
                    request_deserializer=consensus__pb2.AppendEntriesRequest.FromString,
                    response_serializer=consensus__pb2.AppendEntriesResponse.SerializeToString,
            ),
            'RequestVote': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestVote,
                    request_deserializer=consensus__pb2.RequestVoteRequest.FromString,
                    response_serializer=consensus__pb2.RequestVoteResponse.SerializeToString,
            ),
            'AddLog': grpc.unary_unary_rpc_method_handler(
                    servicer.AddLog,
                    request_deserializer=consensus__pb2.AddLogRequest.FromString,
                    response_serializer=consensus__pb2.AddLogResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'consensus.Consensus', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Consensus(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SayHello(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Consensus/SayHello',
            consensus__pb2.HelloRequest.SerializeToString,
            consensus__pb2.HelloResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AppendEntries(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Consensus/AppendEntries',
            consensus__pb2.AppendEntriesRequest.SerializeToString,
            consensus__pb2.AppendEntriesResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Consensus/RequestVote',
            consensus__pb2.RequestVoteRequest.SerializeToString,
            consensus__pb2.RequestVoteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AddLog(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Consensus/AddLog',
            consensus__pb2.AddLogRequest.SerializeToString,
            consensus__pb2.AddLogResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class NodeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SayHello = channel.unary_unary(
                '/consensus.Node/SayHello',
                request_serializer=consensus__pb2.HelloRequest.SerializeToString,
                response_deserializer=consensus__pb2.HelloResponse.FromString,
                )
        self.Request = channel.unary_unary(
                '/consensus.Node/Request',
                request_serializer=consensus__pb2.NodeRequest.SerializeToString,
                response_deserializer=consensus__pb2.NodeResponse.FromString,
                )


class NodeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SayHello(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Request(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_NodeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SayHello': grpc.unary_unary_rpc_method_handler(
                    servicer.SayHello,
                    request_deserializer=consensus__pb2.HelloRequest.FromString,
                    response_serializer=consensus__pb2.HelloResponse.SerializeToString,
            ),
            'Request': grpc.unary_unary_rpc_method_handler(
                    servicer.Request,
                    request_deserializer=consensus__pb2.NodeRequest.FromString,
                    response_serializer=consensus__pb2.NodeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'consensus.Node', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Node(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SayHello(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Node/SayHello',
            consensus__pb2.HelloRequest.SerializeToString,
            consensus__pb2.HelloResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Request(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/consensus.Node/Request',
            consensus__pb2.NodeRequest.SerializeToString,
            consensus__pb2.NodeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
