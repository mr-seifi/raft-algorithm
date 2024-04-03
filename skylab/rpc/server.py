import logging

import grpc
import time
from concurrent import futures
from .config import consensus_pb2, consensus_pb2_grpc
from skylab.broker.queue import PubSubQueue, produce_by_rpc
from uuid import uuid4


class Consensus(consensus_pb2_grpc.ConsensusServicer):
    append_entries_messages = {}
    request_vote_messages = {}

    def SayHello(self, request, context):
        return consensus_pb2.HelloResponse(message=f"Hello, {request.name}")

    def AppendEntries(self, request, context):
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
            raise Exception('[Exception|AppendEntries]: Failed to produce by rpc')

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
            raise Exception('[Exception|RequestVote]: Failed to produce by rpc')

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


def serve(host: str, port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_ConsensusServicer_to_server(Consensus(), server)
    server.add_insecure_port(host + ":" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
