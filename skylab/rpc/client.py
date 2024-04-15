import logging

import grpc
from skylab.rpc.config import consensus_pb2, consensus_pb2_grpc
from skylab.app.config import Config
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed


class Client:
    def __init__(self):
        self.base_url = f"{Config.grpc_consensus_server_host()}:{Config.grpc_consensus_server_port()}"
        self.trusted_nodes = Config.trusted_nodes()
        self.node_id_to_url = {
            Config.node_id(): self.base_url,
            **{
                int(node[-1]): node for node in self.trusted_nodes
            }
        }

    def _request(self, base_url: str, stub: str, rpc: str, request: str, arguments: dict):
        with grpc.insecure_channel(base_url) as channel:
            _stub = getattr(consensus_pb2_grpc, stub + 'Stub')(channel)
            _rpc = getattr(_stub, rpc)
            message = getattr(consensus_pb2, request)
            response = _rpc(message(**arguments))
        return response

    def say_hello(self, base_url: str, name: str):
        response = self._request(base_url=base_url,
                                 stub='Consensus',
                                 rpc='SayHello',
                                 request='HelloRequest',
                                 arguments={'name': name})
        return response.message

    def append_entries(self, base_url: str, term: int, leader_id: int, prev_log_index: int,
                       prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        response = self._request(base_url=base_url,
                                 stub='Consensus',
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
                                 stub='Consensus',
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
        return results, len(results) == len(self.trusted_nodes)

    def add_log_request(self, base_url: str, log: consensus_pb2.Log) -> (int, bool):
        response = self._request(base_url=base_url,
                                 stub='Consensus',
                                 rpc='AddLog',
                                 request='AddLogRequest',
                                 arguments={'log': log})

        return response.success, response.response

    def forward_add_log_request(self, node_id: int, log: consensus_pb2.Log) -> (int, bool):
        logging.info(f"Forwarding the message to leader: {self.node_id_to_url.get(node_id, 1)}")
        return self.add_log_request(base_url=self.node_id_to_url.get(node_id, 1), log=log)

    def node_request(self, base_url: str, command: str) -> (int, bool):
        response = self._request(base_url=base_url,
                                 stub='Node',
                                 rpc='Request',
                                 request='NodeRequest',
                                 arguments={'command': command})

        return response.success, response.response
