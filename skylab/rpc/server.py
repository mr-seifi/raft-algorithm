import logging
import grpc
import time
from concurrent import futures
from .config import consensus_pb2, consensus_pb2_grpc
from skylab.broker.queue import PubSubQueue, produce_by_rpc
from skylab.app.config import Config
from uuid import uuid4


class Consensus(consensus_pb2_grpc.ConsensusServicer):
    append_entries_messages = {}
    request_vote_messages = {}

    def authorize(self, ip_address: str):
        allowed_hosts = [address.split(':')[0] for address in Config.trusted_nodes()]
        return ip_address in allowed_hosts

    def SayHello(self, request, context):
        ip_address = context.peer().split(':')[1]
        if not self.authorize(ip_address=ip_address):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Access Denied!")
            return context, None
        return consensus_pb2.HelloResponse(message=f"Hello, {request.name}")

    def AppendEntries(self, request, context):
        ip_address = context.peer().split(':')[1]
        if not self.authorize(ip_address=ip_address):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Access Denied!")
            return context, None

        pubsub_queue = PubSubQueue()
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
        success = produce_by_rpc(queue=pubsub_queue,
                                 data_type='append_entries',
                                 data=data)
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
        ip_address = context.peer().split(':')[1]
        if not self.authorize(ip_address=ip_address):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Access Denied!")
            return context, None

        pubsub_queue = PubSubQueue()
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'term': request.term,
                'candidate_id': request.candidateId,
                'last_log_index': request.lastLogIndex,
                'last_log_term': request.lastLogTerm}

        logging.info(f"Received RequestVote: {data.items()}")
        success = produce_by_rpc(queue=pubsub_queue,
                                 data_type='request_vote',
                                 data=data)
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


class Request(consensus_pb2_grpc.RequestServicer):
    requests = {}

    def SayHello(self, request, context):
        return consensus_pb2.HelloResponse(message=f"Hello, {request.name}")

    def AddLog(self, request, context):
        pubsub_queue = PubSubQueue()
        _random_id = uuid4().hex
        data = {'_id': _random_id,
                'log': request.log}

        success = produce_by_rpc(queue=pubsub_queue,
                                 data_type='add_log_request',
                                 data=data)
        if not success:
            logging.error('[Exception|AddLog]: Failed to produce by rpc')
            context.set_code(grpc.StatusCode.CANCELLED)
            context.set_details("Bad request!")
            return context, None

        response = {}
        timeout = time.time() + 60
        while True:
            if Request.requests.get(_random_id):
                response = Request.requests.pop(_random_id)
                break
            if time.time() > timeout:
                break
            time.sleep(0.01)

        logging.info(f"Respond Request: [{_random_id}] "
                     f"(success, {response.get('success')})")
        return consensus_pb2.AddLogResponse(success=response.get('success'),
                                            response=response.get('response'))

        return consensus_pb2.AddLogResponse(response="")


def serve(host: str, port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_ConsensusServicer_to_server(Consensus(), server)
    server.add_insecure_port(host + ":" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
