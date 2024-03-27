import signal
from random import randint
from enum import Enum
from skylab.app.config import Config
from skylab.consensus.consensus import Consensus
from skylab.rpc.communicator import Communicator


class Role(Enum):
    LEADER = 0
    CANDIDATE = 1
    FOLLOWER = 2


class State:
    def __init__(self, current_term: int, voted_for: int, log: list, commit_index: int,
                 last_applied: int, current_leader: int, next_index: list, match_index: list):
        self.id = Config.node_id()
        self.current_term = current_term
        self.voted_for = voted_for
        self.log = log
        self.commit_index = commit_index
        self.last_applied = last_applied
        # self.current_role = Role.FOLLOWER
        self.current_leader = current_leader

        # Initialized to leader
        self.next_index = next_index
        self.match_index = match_index

    def set_timer(self):
        ...

    def reset_timer(self):
        ...

    def alarm_handler(self):
        ...

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        ...

    def run(self):
        ...


class FollowerState(State):
    def __init__(self, consensus_service: Consensus, current_term=0, voted_for=None, log=[],
                 commit_index=0, last_applied=0, current_leader=None):
        super().__init__(current_term=current_term, voted_for=voted_for, log=log, commit_index=commit_index,
                         last_applied=last_applied, current_leader=current_leader, next_index=[], match_index=[])
        self.consensus_service: Consensus = consensus_service

    def set_timer(self):
        delta = Config.timeout_delta()
        Consensus.TIMEOUT = Config.timeout() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.TIMEOUT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self):
        self.consensus_service.state = CandidateState(consensus_service=self.consensus_service,
                                                      current_term=self.current_term, voted_for=self.voted_for,
                                                      log=self.log, commit_index=self.commit_index,
                                                      last_applied=self.last_applied,
                                                      current_leader=self.current_leader)
        return self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        # Follower Role
        if self.current_leader != leader_id:
            return -1, False

        # TODO: Check the first condition
        if len(self.log) - 1 < prev_log_index and \
                self.log[prev_log_index].term != prev_log_term:
            return self.current_term, False

        if self.log[prev_log_index].term != prev_log_term:
            self.log = self.log[:prev_log_index]

        # TODO: Check not to be in logs
        for entry in entries:
            self.log.append(entry)

        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)

        return self.current_term, True

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        if (self.voted_for is None or self.voted_for == candidate_id) and \
                (last_log_term == self.log[-1].term and last_log_index == len(self.log) - 1):
            return self.current_term, True

        return self.current_term, False

    def run(self):
        self.reset_timer()


class CandidateState(State):
    def __init__(self, consensus_service: Consensus, current_term=0, voted_for=None, log=[],
                 commit_index=0, last_applied=0, current_leader=None):
        super().__init__(current_term=current_term, voted_for=voted_for, log=log, commit_index=commit_index,
                         last_applied=last_applied, current_leader=current_leader, next_index=[], match_index=[])
        self.consensus_service: Consensus = consensus_service

    def set_timer(self):
        delta = Config.timeout_delta()
        Consensus.TIMEOUT = Config.timeout() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.TIMEOUT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self):
        self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        if (self.voted_for is None or self.voted_for == candidate_id) and \
                (last_log_term == self.log[-1].term and last_log_index == len(self.log) - 1):
            return self.current_term, True

        return self.current_term, False

    def run(self):  # Start Election
        self.current_term += 1
        self.voted_for = self.id
        self.reset_timer()

        communicator = Communicator()
        responses, all_granted = communicator.broadcast_request_votes(term=self.current_term,
                                                                      candidate_id=self.id,
                                                                      last_log_index=self.last_applied,
                                                                      last_log_term=self.log[
                                                                          -1].term if self.log else 0)

        total_granted = len(list(filter(lambda resp: resp[1] is True, responses)))
        majority = len(Config.trusted_nodes()) // 2 + 1
        if total_granted >= majority:
            self.consensus_service.state = LeaderState(consensus_service=self.consensus_service,
                                                       current_term=self.current_term, voted_for=self.voted_for,
                                                       log=self.log, commit_index=self.commit_index,
                                                       last_applied=self.last_applied,
                                                       current_leader=self.id)
            self.consensus_service.next_index = [self.consensus_service.last_applied + 1 for _ in Config.trusted_nodes()]
            self.consensus_service.match_index = [0 for _ in Config.trusted_nodes()]
            return self.consensus_service.run()

        # TODO: if appendEntries received --> FOLLOWER


class LeaderState(State):
    def __init__(self, consensus_service: Consensus, current_term=0, voted_for=None, log=[],
                 commit_index=0, last_applied=0, current_leader=None, next_index=[], match_index=[]):
        if not next_index:
            next_index = [last_applied + 1 for _ in Config.trusted_nodes()]
        if not match_index:
            match_index = [0 for _ in Config.trusted_nodes()]
        super().__init__(current_term=current_term, voted_for=voted_for, log=log, commit_index=commit_index,
                         last_applied=last_applied, current_leader=current_leader, next_index=next_index,
                         match_index=match_index)
        self.consensus_service: Consensus = consensus_service

    def set_timer(self):
        delta = Config.heartbeat_delta()
        Consensus.HEARTBEAT = Config.heartbeat() + randint(-delta, delta)
        signal.signal(signal.SIGALRM, self.consensus_service.alarm_handler)
        signal.alarm(Consensus.HEARTBEAT)

    def reset_timer(self):
        signal.alarm(0)
        self.consensus_service.set_timer()

    def alarm_handler(self):
        self.consensus_service.run()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        self.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.current_term:
            return self.current_term, False

        if term > self.current_term:
            self.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                         current_term=self.current_term, voted_for=self.voted_for,
                                                         log=self.log, commit_index=self.commit_index,
                                                         last_applied=self.last_applied,
                                                         current_leader=self.current_leader)
            return self.consensus_service.run()

        if (self.voted_for is None or self.voted_for == candidate_id) and \
                (last_log_term == self.log[-1].term and last_log_index == len(self.log) - 1):
            return self.current_term, True

        return self.current_term, False

    def run(self):
        self.reset_timer()
        communicator = Communicator()
        communicator.broadcast_append_entries(term=self.current_term,
                                              leader_id=self.id,
                                              prev_log_index=self.last_applied,
                                              prev_log_term=self.log[-1].term if self.log else 0,
                                              entries=[],
                                              leader_commit=self.commit_index)

        for node_index, node in enumerate(Config.trusted_nodes()):
            if self.last_applied >= self.next_index[node_index]:
                term, success = communicator.append_entries(
                    base_url=node,
                    term=self.current_term,
                    leader_id=self.id,
                    prev_log_index=self.last_applied,
                    prev_log_term=self.log[-1].term if self.log else 0,
                    entries=[self.log[self.next_index[node_index]]],  # TODO: [EFF] Can send batch batch
                    leader_commit=self.commit_index
                )

                if term > self.current_term:
                    self.current_term = term
                    self.consensus_service.state = FollowerState(consensus_service=self.consensus_service,
                                                                 current_term=self.current_term,
                                                                 voted_for=self.voted_for,
                                                                 log=self.log, commit_index=self.commit_index,
                                                                 last_applied=self.last_applied,
                                                                 current_leader=-1)  # TODO: Fill current_leader
                    return self.consensus_service.run()

                if success:
                    self.match_index[node_index] = self.next_index[node_index]
                    self.next_index[node_index] += 1
                else:
                    self.next_index[node_index] -= 1
        # TODO: Last Condition: Exist N > ...
