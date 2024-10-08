import logging
import grpc
import time
import re
from concurrent import futures
from .config import consensus_pb2, consensus_pb2_grpc
from skylab.broker import MessageBroker
from skylab.app.config import Config
from uuid import uuid4


class Consensus(consensus_pb2_grpc.ConsensusServicer):
    append_entries_messages = {}
    request_vote_messages = {}
    add_log_messages = {}
    WHITELIST_REGEX = r'(?:10\.\d+\.\d+\.\d+)'

    def authorize(self, context):
        allowed_hosts = [address.split(':')[0] for address in Config.trusted_nodes()]
        ip_address = context.peer().split(':')[1]
        return ip_address in allowed_hosts or (re.match(self.WHITELIST_REGEX, ip_address) is not None)

    def SayHello(self, request, context):
        if not self.authorize(context=context):
            # context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            # context.set_details("Access Denied!")
            # return context, None
            return consensus_pb2.HelloResponse(message="")
        return consensus_pb2.HelloResponse(message=f"Hello, {request.name}")

    def AppendEntries(self, request, context):
        if not self.authorize(context=context):
            # context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            # context.set_details("Access Denied!")
            # return context, None
            return consensus_pb2.AppendEntriesResponse(term=-1, success=False)

        message_broker = MessageBroker(channel_name=MessageBroker.Channels.RPC_TO_CONSENSUS)
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'term': request.term,
                'leader_id': request.leaderId,
                'prev_log_index': request.prevLogIndex,
                'prev_log_term': request.prevLogTerm,
                'entries': [{'log_term': entry.logTerm, 'command': entry.command}
                            for entry in request.entries],
                'leader_commit': request.leaderCommit}

        logging.info(f"Received AppendEntries: {data.items()}")
        success = message_broker.produce(data_type='append_entries', data=data)
        if not success:
            logging.error('[Exception|AppendEntries]: Failed to produce by rpc')
            context.set_code(grpc.StatusCode.CANCELLED)
            context.set_details("Bad request!")
            return context, None

        response = {}
        timeout = time.time() + 60
        while True:
            if Consensus.append_entries_messages.get(_random_id):
                response = Consensus.append_entries_messages.pop(_random_id)
                break
            if time.time() > timeout:
                break
            time.sleep(0.01)

        logging.info(f"Respond AppendEntries: [{_random_id}] "
                     f"(term, {response.get('term')}), (success, {response.get('success')})")
        return consensus_pb2.AppendEntriesResponse(term=response.get('term'),
                                                   success=response.get('success'))

    def RequestVote(self, request, context):
        if not self.authorize(context=context):
            # context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            # context.set_details("Access Denied!")
            # return context, None
            return consensus_pb2.RequestVoteResponse(term=-1, granted=False)

        message_broker = MessageBroker(channel_name=MessageBroker.Channels.RPC_TO_CONSENSUS)
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'term': request.term,
                'candidate_id': request.candidateId,
                'last_log_index': request.lastLogIndex,
                'last_log_term': request.lastLogTerm}

        logging.info(f"Received RequestVote: {data.items()}")
        success = message_broker.produce(data_type='request_vote', data=data)
        if not success:
            logging.error('[Exception|RequestVote]: Failed to produce by rpc')
            context.set_code(grpc.StatusCode.CANCELLED)
            context.set_details("Bad request!")
            return context, None

        response = {}
        timeout = time.time() + 60
        while True:
            if Consensus.request_vote_messages.get(_random_id):
                response = Consensus.request_vote_messages.pop(_random_id)
                break
            if time.time() > timeout:
                break
            time.sleep(0.01)

        logging.info(f"Respond RequestVote: [{_random_id}] "
                     f"(term, {response.get('term')}), (granted, {response.get('granted')})")
        return consensus_pb2.RequestVoteResponse(term=response.get('term'), granted=response.get('granted'))

    def AddLog(self, request, context):
        if not self.authorize(context=context):
            # context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            # context.set_details("Access Denied!")
            # return context, None
            return consensus_pb2.AddLogResponse(success=False, response="Authorization failure.")
        message_broker = MessageBroker(channel_name=MessageBroker.Channels.RPC_TO_CONSENSUS)
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'log': {'log_term': request.log.logTerm,
                        'command': request.log.command}}

        logging.info(f"Received AddLogRequest: [{data.items()}]")
        success = message_broker.produce(data_type='add_log_request',
                                         data=data)
        if not success:
            return consensus_pb2.AddLogResponse(success=False,
                                                response="")

        response = {}
        timeout = time.time() + 60
        while True:
            if Consensus.add_log_messages.get(_random_id):
                response = Consensus.add_log_messages.pop(_random_id)
                break
            if time.time() > timeout:
                break
            time.sleep(0.01)

        logging.info(f"Respond AddLogRequest: [{_random_id}] "
                     f"(success, {response.get('success')})")
        return consensus_pb2.AddLogResponse(success=response.get('success'),
                                            response=response.get('response'))


class Node(consensus_pb2_grpc.NodeServicer):
    requests = {}

    def SayHello(self, request, context):
        return consensus_pb2.HelloResponse(message=f"Hello, {request.name}")

    def Request(self, request, context):
        message_broker = MessageBroker(channel_name=MessageBroker.Channels.RPC_TO_CONSENSUS)
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'command': request.command}

        logging.info(f"Received NodeRequest: [{data.items()}]")
        success = message_broker.produce(data_type='node_request',
                                         data=data)
        if not success:
            return consensus_pb2.NodeResponse(success=False,
                                              response="")

        response = {}
        timeout = time.time() + 60
        while True:
            if Node.requests.get(_random_id):
                response = Node.requests.pop(_random_id)
                break
            if time.time() > timeout:
                break
            time.sleep(0.01)

        logging.info(f"Respond NodeRequest: [{_random_id}] "
                     f"(success, {response.get('success')})")
        return consensus_pb2.NodeResponse(success=response.get('success'),
                                          response=response.get('response'))


def serve_consensus(host: str, port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_ConsensusServicer_to_server(Consensus(), server)
    server.add_insecure_port(host + ":" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


def serve_node(host: str, port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_NodeServicer_to_server(Node(), server)
    server.add_insecure_port(host + ":" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
