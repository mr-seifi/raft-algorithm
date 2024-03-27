from enum import Enum
from skylab.app.config import Config


class Role(Enum):
    LEADER = 0
    CANDIDATE = 1
    FOLLOWER = 2


class State:
    def __init__(self):
        self.id = Config.node_id()
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.current_role = Role.FOLLOWER
        self.current_leader = None

        # Initialized to leader
        self.next_index = None
        self.match_index = 0
