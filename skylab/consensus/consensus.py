import signal
import time
from random import randint

from skylab.consensus.state import FollowerState, CandidateState, LeaderState, Role
from skylab.app.config import Config
from skylab.rpc.communicator import Communicator


class Consensus:
    TIMEOUT = -1
    HEARTBEAT = -1

    def __init__(self, current_term=0, voted_for=None, log=[],
                 commit_index=0, last_applied=0, current_leader=None,
                 next_index=[], match_index=[]):
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

        self.state = FollowerState(consensus_service=self)
        self.set_timeout()

    # NEW METHODS
    def set_timer(self):
        self.state.set_timer()

    def alarm_handler(self):
        self.state.alarm_handler()

    def reset_timer(self):
        self.state.reset_timer()

    def reply_append_entries(self, term: int, leader_id: int, prev_log_index: int,
                             prev_log_term: int, entries: list, leader_commit: int) -> (int, bool):
        return self.state.reply_append_entries(term=term, leader_id=leader_id, prev_log_index=prev_log_index,
                                               prev_log_term=prev_log_term, entries=entries,
                                               leader_commit=leader_commit)

    def reply_vote_request(self, term: int, candidate_id: int,
                           last_log_index: int, last_log_term: int) -> (int, bool):
        return self.state.reply_vote_request(term=term, candidate_id=candidate_id, last_log_index=last_log_index,
                                             last_log_term=last_log_term)

    def run(self):
        return self.state.run()

    def start(self):
        while True:
            time.sleep(10)

    # ###

    # TODO: Write state read, write function
    # General
    def exec_log_command(self):
        if self.state.commit_index > self.state.last_applied:
            self.state.last_applied += 1
            # TODO: Write run command
            self.state.log[self.state.last_applied - 1].run()

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

