import signal
from random import randint
from skylab.app.config import Config
from skylab.consensus.consensus import Consensus
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

    def exec_last_log_command(self):
        if self.consensus_service.commit_index > self.consensus_service.last_applied:
            self.consensus_service.last_applied += 1
            # TODO: Write run command
            self.consensus_service.log[self.consensus_service.last_applied - 1].run()

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
            self.consensus_service.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            # return self.consensus_service.run()

        # Follower Role
        if self.consensus_service.current_leader != leader_id:
            return -1, False

        # TODO: Check the first condition
        if len(self.consensus_service.log) - 1 < prev_log_index and \
                self.consensus_service.log[prev_log_index].term != prev_log_term:
            return self.consensus_service.current_term, False

        if self.consensus_service.log[prev_log_index].term != prev_log_term:
            self.consensus_service.log = self.consensus_service.log[:prev_log_index]

        # TODO: Check not to be in logs
        # TODO: Check exec that should be last - 1 or last
        for entry in entries:
            self.consensus_service.log.append(entry)
            self.exec_last_log_command()
            self.consensus_service.last_applied += 1

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
            return self.consensus_service.run()

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                (last_log_term == self.consensus_service.log[-1].term and last_log_index == len(
                    self.consensus_service.log) - 1):
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def exec_last_log_command(self):
        super().exec_last_log_command()

    def handle_request(self, log):
        # TODO: Forward it to leader
        ...

    def run(self):
        self.reset_timer()


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
            self.consensus_service.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.run()

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.run()

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                (last_log_term == self.consensus_service.log[-1].term and
                 last_log_index == len(self.consensus_service.log) - 1):
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def exec_last_log_command(self):
        super().exec_last_log_command()

    def handle_request(self, log):
        ...

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
            self.consensus_service.match_index = [0 for _ in Config.trusted_nodes()]
            self.consensus_service.current_leader = self.consensus_service.id
            return self.consensus_service.run()

        # TODO: if appendEntries received --> FOLLOWER


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
            self.consensus_service.current_leader = leader_id
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.run()

        return -1, False

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        self.consensus_service.reset_timer()

        if term < self.consensus_service.current_term:
            return self.consensus_service.current_term, False

        if term > self.consensus_service.current_term:
            self.consensus_service.current_term = term
            self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
            return self.consensus_service.run()

        if (self.consensus_service.voted_for is None or self.consensus_service.voted_for == candidate_id) and \
                (last_log_term == self.consensus_service.log[-1].term and
                 last_log_index == len(self.consensus_service.log) - 1):
            return self.consensus_service.current_term, True

        return self.consensus_service.current_term, False

    def exec_last_log_command(self):
        super().exec_last_log_command()

    def handle_request(self, log):
        self.consensus_service.log.append(
            log
        )
        self.exec_last_log_command()
        self.consensus_service.last_applied += 1

        return  # RESPONSE

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
                    entries=[self.consensus_service.log[self.consensus_service.next_index[node_index]]],  # TODO: [
                    # EFF] Can send batch batch
                    leader_commit=self.consensus_service.commit_index
                )

                if term > self.consensus_service.current_term:
                    self.consensus_service.current_term = term
                    self.consensus_service.current_leader = -1  # TODO: Fill current_leader
                    self.consensus_service.state = FollowerState(consensus_service=self.consensus_service)
                    return self.consensus_service.run()

                if success:
                    self.consensus_service.match_index[node_index] = self.consensus_service.next_index[node_index]
                    self.consensus_service.next_index[node_index] += 1
                else:
                    self.consensus_service.next_index[node_index] -= 1

        # TODO: Last Condition: Exist N > ...
