import grpc
import time
from concurrent import futures
from .config import consensus_pb2, consensus_pb2_grpc
from skylab.broker.queue import PubSubQueue, produce_by_rpc
from uuid import uuid4


class Consensus(consensus_pb2_grpc.ConsensusServicer):
    append_entries_messages = {}
    request_vote_messages = {}

    def AppendEntries(self, request, context):
        pubsub_queue = PubSubQueue()
        _random_id = uuid4().hex
        success = produce_by_rpc(queue=pubsub_queue,
                                 data_type='append_entries',
                                 data={'_id': _random_id,
                                       'term': request.term,
                                       'leader_id': request.leaderId,
                                       'prev_log_index': request.prevLogIndex,
                                       'prev_log_term': request.prevLogTerm,
                                       'entries': [{'log_term': entry.logTerm, 'command': entry.command}
                                                   for entry in request.entries],
                                       'leader_commit': request.leaderCommit})
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

        return consensus_pb2.AppendEntriesResponse(term=response.get('term'),
                                                   success=response.get('success'))

    def RequestVote(self, request, context):
        pubsub_queue = PubSubQueue()
        _random_id = uuid4().hex
        success = produce_by_rpc(queue=pubsub_queue,
                                 data_type='request_vote',
                                 data={'_id': _random_id,
                                       'term': request.term,
                                       'candidate_id': request.candidateId,
                                       'last_log_index': request.lastLogIndex,
                                       'last_log_term': request.lastLogTerm})
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

        return consensus_pb2.RequestVoteResponse(term=response.get('term'), granted=response.get('granted'))


def serve(port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_ConsensusServicer_to_server(Consensus(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
