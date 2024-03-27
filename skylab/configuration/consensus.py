import signal
from random import randint

from skylab.configuration.state import State, Role
from skylab.app.config import Config
from skylab.rpc.communicator import Communicator


class Consensus:
    TIMEOUT = -1
    HEARTBEAT = -1

    def __init__(self):
        self.state = State()
        self.set_timeout()

    def set_timeout(self):
        delta = Config.timeout_delta()
        Consensus.TIMEOUT = Config.timeout() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.alarm_handler)
        signal.alarm(Consensus.TIMEOUT)

    def reset_timeout(self):
        signal.alarm(0)
        self.set_timeout()

    def alarm_handler(self, signum, frame):
        if self.state.current_role in [Role.FOLLOWER, Role.CANDIDATE]:
            self.start_election()
        else:
            self.maintain_leader()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.reset_timeout()

        # Follower Role
        if self.state.current_role == Role.FOLLOWER:
            if self.state.current_leader != leader_id:
                return

        if term < self.state.current_term:
            return self.state.current_term, False

        if term > self.state.current_term:
            self.state.current_term = term
            self.state.current_role = Role.FOLLOWER
            return self.maintain_follower()

        # TODO: Check the first condition
        if len(self.state.log) - 1 < prev_log_index and \
                self.state.log[prev_log_index].term != prev_log_term:
            return self.state.current_term, False

        if self.state.log[prev_log_index].term != prev_log_term:
            self.state.log = self.state.log[:prev_log_term]

        # TODO: Not to be in logs
        for entry in entries:
            self.state.log.append(entry)

        if leader_commit > self.state.commit_index:
            self.state.commit_index = min(leader_commit, len(self.state.log) - 1)

        return self.state.current_term, True

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.reset_timeout()

        if term < self.state.current_term:
            return self.state.current_term, False

        if term > self.state.current_term:
            self.state.current_term = term
            self.state.current_role = Role.FOLLOWER
            return self.maintain_follower()

        if (self.state.voted_for is None or self.state.voted_for == candidate_id) and \
                (last_log_term == self.state.log[-1].term and last_log_index == len(self.state.log) - 1):
            return self.state.current_term, True

        return self.state.current_term, False

    # TODO: Write state read, write function
    # General
    def exec_log_command(self):
        if self.state.commit_index > self.state.last_applied:
            self.state.last_applied += 1
            # TODO: Write run command
            self.state.log[self.state.last_applied - 1].run()

    # General

    def start_election(self):
        self.state.current_role = Role.CANDIDATE
        self.state.current_term += 1
        self.state.voted_for = self.state.id
        self.reset_timeout()

        communicator = Communicator()
        responses, all_granted = communicator.broadcast_request_votes(term=self.state.current_term,
                                                                      candidate_id=self.state.id,
                                                                      last_log_index=self.state.last_applied,
                                                                      last_log_term=self.state.log[
                                                                          -1].term if self.state.log else 0)

        total_granted = len(list(filter(lambda resp: resp[1] is True, responses)))
        majority = len(Config.trusted_nodes()) // 2 + 1
        if total_granted >= majority:
            self.state.current_role = Role.LEADER
            self.state.next_index = [self.state.last_applied + 1 for _ in Config.trusted_nodes()]
            self.state.match_index = [0 for _ in Config.trusted_nodes()]
            self.maintain_leader()

        # TODO: if appendEntries received --> FOLLOWER

    # Leader
    def set_heartbeat(self):
        delta = Config.heartbeat_delta()
        Consensus.HEARTBEAT = Config.heartbeat() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.alarm_handler)
        signal.alarm(Consensus.HEARTBEAT)

    def reset_heartbeat(self):
        signal.alarm(0)
        self.set_heartbeat()

    def maintain_follower(self):
        ...

    def maintain_leader(self):
        self.reset_heartbeat()
        communicator = Communicator()
        communicator.broadcast_append_entries(term=self.state.current_term,
                                              leader_id=self.state.id,
                                              prev_log_index=self.state.last_applied,
                                              prev_log_term=self.state.log[-1].term if self.state.log else 0,
                                              entries=[],
                                              leader_commit=self.state.commit_index)

        for node_index, node in enumerate(Config.trusted_nodes()):
            if self.state.last_applied >= self.state.next_index[node_index]:
                term, success = communicator.append_entries(
                    base_url=node,
                    term=self.state.current_term,
                    leader_id=self.state.id,
                    prev_log_index=self.state.last_applied,
                    prev_log_term=self.state.log[-1].term if self.state.log else 0,
                    entries=[self.state.log[self.state.next_index[node_index]]], # TODO: [EFF] Can send batch batch
                    leader_commit=self.state.commit_index
                )

                if term > self.state.current_term:
                    self.state.current_term = term
                    self.state.current_role = Role.FOLLOWER
                    return self.maintain_follower()

                if success:
                    self.state.match_index[node_index] = self.state.next_index[node_index]
                    self.state.next_index[node_index] += 1
                else:
                    self.state.next_index[node_index] -= 1

    def request(self, log):
        if self.state.current_role == Role.FOLLOWER:
            # TODO: Send it to leader
            ...
        elif self.state.current_role == Role.LEADER:
            self.state.log.append(
                log
            )
            self.state.last_applied += 1

        return # RESPONSE

