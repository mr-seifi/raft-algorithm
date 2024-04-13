import logging
import signal
import threading
from random import randint
from skylab.app.config import Config
from skylab.consensus.consensus import Consensus
from skylab.consensus.log import Log, decode_log
from skylab.rpc.config import consensus_pb2
from skylab.rpc.client import Client


class State:
    def __init__(self, consensus_service: Consensus):
        self.consensus_service = consensus_service

    def set_timer(self):
        ...

    def reset_timer(self):
        ...

    def alarm_handler(self, signum, frame):
        ...

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        ...

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        ...

    def handle_request(self, log):
        ...

    def run(self):
        ...


class FollowerState(State):
    def __init__(self, consensus_service: Consensus):
        super().__init__(consensus_service=consensus_service)

    def set_timer(self):
        delta = Config.timeout_delta()
        Consensus.TIMEOUT = Config.timeout() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.TIMEOUT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self, signum, frame):
        self.consensus_service.state = CandidateState(consensus_service=self.consensus_service)
        return self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.current_term, True

        # TODO: Check not to be in logs
        # TODO: Check exec that should be last - 1 or last
        for entry in entries:
            log = decode_log(entry)
            self.consensus_service.log.append(log)

            log.exec()
            self.consensus_service.last_applied += 1

        # TODO: Check the first condition
        if len(self.consensus_service.log) - 1 < prev_log_index:
            return self.consensus_service.current_term, False

        if self.consensus_service.log and (self.consensus_service.log[prev_log_index].term != prev_log_term):
            self.consensus_service.log = self.consensus_service.log[:prev_log_index]

        if leader_commit > self.consensus_service.commit_index:
            self.consensus_service.commit_index = min(leader_commit, len(self.consensus_service.log) - 1)

        return self.consensus_service.current_term, True

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            self.voted_for = candidate_id
            return self.consensus_service.current_term, True

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                ((not self.consensus_service.log) or (
                        last_log_term == self.consensus_service.log[-1].term and last_log_index == len(
                    self.consensus_service.log) - 1)):
            self.consensus_service.voted_for = candidate_id
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def handle_request(self, log):
        # TODO: Forward it to leader
        return True

    def run(self):
        self.reset_timer()

    def __str__(self) -> str:
        return "FOLLOWER"


class CandidateState(State):
    def __init__(self, consensus_service: Consensus):
        super().__init__(consensus_service=consensus_service)

    def set_timer(self):
        delta = Config.timeout_delta()
        Consensus.TIMEOUT = Config.timeout() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.TIMEOUT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self, signum, frame):
        self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.current_term, True

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            self.consensus_service.voted_for = candidate_id
            return self.consensus_service.current_term, True

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                (last_log_term == self.consensus_service.log[-1].term and
                 last_log_index == len(self.consensus_service.log) - 1):
            self.consensus_service.voted_for = candidate_id
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def handle_request(self, log):
        return True

    def run(self):  # Start Election
        self.consensus_service.current_term += 1
        self.consensus_service.voted_for = self.consensus_service.id
        self.reset_timer()

        client = Client()
        responses, all_granted = client.broadcast_request_votes(term=self.consensus_service.current_term,
                                                                candidate_id=self.consensus_service.id,
                                                                last_log_index=self.consensus_service.last_applied,
                                                                last_log_term=self.consensus_service.log[
                                                                    -1].term if self.consensus_service.log else 0)

        total_granted = len(list(filter(lambda resp: resp[1] is True, responses)))
        majority = len(Config.trusted_nodes()) // 2 + 1
        if total_granted >= majority:
            self.consensus_service.state = LeaderState(consensus_service=self.consensus_service)
            self.consensus_service.next_index = [self.consensus_service.last_applied + 1 for _ in
                                                 Config.trusted_nodes()]
            self.consensus_service.match_index = [-1 for _ in Config.trusted_nodes()]
            return self.consensus_service.run()

    def __str__(self) -> str:
        return "CANDIDATE"


class LeaderState(State):
    def __init__(self, consensus_service: Consensus):
        super().__init__(consensus_service=consensus_service)

    def set_timer(self):
        delta = Config.heartbeat_delta()
        Consensus.HEARTBEAT = Config.heartbeat() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.HEARTBEAT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self, signum, frame):
        self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.current_term, True

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            self.consensus_service.voted_for = candidate_id
            return self.consensus_service.current_term, True

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                (last_log_term == self.consensus_service.log[-1].term and
                 last_log_index == len(self.consensus_service.log) - 1):
            self.consensus_service.voted_for = candidate_id
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def handle_request(self, log: dict) -> bool:
        log = Log(term=log['log_term'], command=log['command'])
        self.consensus_service.log.append(log)

        self.consensus_service.last_applied += 1
        log.exec()
        return True

    def run(self):
        self.consensus_service.reset_timer()
        client = Client()
        client.broadcast_append_entries(term=self.consensus_service.current_term,
                                        leader_id=self.consensus_service.id,
                                        prev_log_index=self.consensus_service.last_applied,
                                        prev_log_term=self.consensus_service.log[-1].term if \
                                            self.consensus_service.log else 0,
                                        entries=[],
                                        leader_commit=self.consensus_service.commit_index)

        for node_index, node in enumerate(Config.trusted_nodes()):
            if self.consensus_service.last_applied >= self.consensus_service.next_index[node_index]:
                term, success = client.append_entries(
                    base_url=node,
                    term=self.consensus_service.current_term,
                    leader_id=self.consensus_service.id,
                    prev_log_index=self.consensus_service.last_applied,
                    prev_log_term=self.consensus_service.log[-1].term if self.consensus_service.log else 0,
                    entries=[consensus_pb2.Log(logTerm=self.consensus_service.log[self.consensus_service.next_index[node_index]].term,
                                               command=self.consensus_service.log[self.consensus_service.next_index[node_index]].command)],  # TODO: [
                    # EFF] Can send batch batch
                    leader_commit=self.consensus_service.commit_index
                )

                if term > self.consensus_service.current_term:
                    self.consensus_service.current_term = term
                    self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
                    return self.consensus_service.run()

                if success:
                    self.consensus_service.match_index[node_index] = self.consensus_service.next_index[node_index]
                    self.consensus_service.next_index[node_index] += 1
                # else:
                #     self.consensus_service.next_index[node_index] -= 1

        if len(self.consensus_service.log) > self.consensus_service.commit_index:
            majority_match_indices = 0
            N = self.consensus_service.commit_index + 1
            for match_index in self.consensus_service.match_index:
                if match_index >= N:
                    majority_match_indices += 1

            if majority_match_indices >= len(Config.trusted_nodes()) // 2 + 1 and \
                    self.consensus_service.log[N].term == self.consensus_service.current_term:
                self.consensus_service.commit_index = N

    def __str__(self) -> str:
        return "LEADER"
