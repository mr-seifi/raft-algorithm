import time
from skylab.app.config import Config
from skylab.broker.queue import RedisQueue


class Consensus:
    TIMEOUT = -1
    HEARTBEAT = -1

    def __init__(self, current_term=0, voted_for=None, log=[],
                 commit_index=0, last_applied=0, current_leader=None,
                 next_index=[], match_index=[]):
        from skylab.consensus.state import FollowerState

        # TODO: Write state read, write function
        # TODO: Persist Storage
        self.id = Config.node_id()
        self.current_term = current_term
        self.voted_for = voted_for
        self.log = log
        self.commit_index = commit_index
        self.last_applied = last_applied
        self.current_leader = current_leader

        # Initialized to leader
        self.next_index = next_index
        self.match_index = match_index

        self.state = FollowerState(consensus_service=self)
        self.state.run()

    def store(self):
        ...

    def load(self):
        ...

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

    def exec_last_log_command(self):
        return self.state.exec_last_log_command()

    def request(self, log):
        return self.state.handle_request(log=log)

    def run(self):
        return self.state.run()

    def start(self):
        self.load()
        self.run()

        redis_queue = RedisQueue()
        while True:
            try:
                append_entry = redis_queue.get_append_entry()
                if append_entry:
                    ...

                vote_request = redis_queue.get_append_entry()
                if vote_request:
                    ...

            except Exception as e:
                print(f'[Exception|Consensus]: {e}')
                redis_queue = RedisQueue()



            ...