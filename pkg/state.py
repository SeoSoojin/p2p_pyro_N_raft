from enum import Enum

class State(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3
