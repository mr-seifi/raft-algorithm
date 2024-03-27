import grpc
from skylab.rpc.config import consensus_pb2, consensus_pb2_grpc
from skylab.app.config import Config
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed


class Communicator:
    def __init__(self):
        self.base_url = f"{Config.grpc_server_host()}:{Config.grpc_server_port()}"
        self.trusted_nodes = Config.trusted_nodes()

    def _request(self, base_url: str, rpc: str, request: str, arguments: dict):
        with grpc.insecure_channel(base_url) as channel:
            stub = consensus_pb2_grpc.ConsensusStub(channel)
            _rpc = getattr(stub, rpc)
            message = getattr(consensus_pb2, request)
            response = _rpc(message(**arguments))
        return response

    def append_entries(self, base_url: str, term: int, leader_id: int, prev_log_index: int,
                       prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        response = self._request(base_url=base_url,
                                 rpc='AppendEntries',
                                 request='AppendEntriesRequest',
                                 arguments={'term': term, 'leaderId': leader_id, 'prevLogIndex': prev_log_index,
                                            'prevLogTerm': prev_log_term, 'entries': entries,
                                            'leaderCommit': leader_commit})

        return response.term, response.success

    def broadcast_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                                 prev_log_term: int, entries: list, leader_commit: int) -> (list, bool):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.append_entries, node, term, leader_id, prev_log_index,
                                       prev_log_term, entries, leader_commit) for node in self.trusted_nodes]

            try:
                for future in as_completed(futures, timeout=Config.append_entries_timeout()):
                    result = future.result()
                    results.append(result)
            except TimeoutError:
                ...
        return result, len(results) == len(self.trusted_nodes)

    def request_vote(self, base_url: str, term: int, candidate_id: int,
                     last_log_index: int, last_log_term: int) -> (int, bool):
        response = self._request(base_url=base_url,
                                 rpc='RequestVote',
                                 request='RequestVoteRequest',
                                 arguments={'term': term, 'candidateId': candidate_id,
                                            'lastLogIndex': last_log_index, 'lastLogTerm': last_log_term})

        return response.term, response.granted

    def broadcast_request_votes(self, term: int, candidate_id: int,
                                last_log_index: int, last_log_term: int) -> (list, bool):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.request_vote, node, term, candidate_id, last_log_index,
                                       last_log_term) for node in self.trusted_nodes]

            try:
                for future in as_completed(futures, timeout=Config.request_vote_timeout()):
                    result = future.result()
                    results.append(result)
            except TimeoutError:
                ...
        return result, len(results) == len(self.trusted_nodes)
