import grpc
from concurrent import futures
from .config import consensus_pb2, consensus_pb2_grpc
from skylab.consensus.consensus import Consensus as ConsensusService


class Consensus(consensus_pb2_grpc.ConsensusServicer):
    def AppendEntries(self, request, context):
        consensus_service = ConsensusService()
        # print(request.entries)
        current_term, success = consensus_service.reply_append_entries(term=request.term,
                                                                       leader_id=request.leaderId,
                                                                       prev_log_index=request.prevLogIndex,
                                                                       prev_log_term=request.prevLogTerm,
                                                                       entries=request.entries,
                                                                       leader_commit=request.leaderCommit)
        return consensus_pb2.AppendEntriesResponse(term=current_term, success=success)

    def RequestVote(self, request, context):
        consensus_service = ConsensusService()
        current_term, granted = consensus_service.reply_vote_request(term=request.term,
                                                                     candidate_id=request.candidateId,
                                                                     last_log_index=request.lastLogIndex,
                                                                     last_log_term=request.lastLogTerm)
        return consensus_pb2.RequestVoteResponse(term=current_term, granted=granted)


def serve(port: str, max_workers: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    consensus_pb2_grpc.add_ConsensusServicer_to_server(Consensus(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
