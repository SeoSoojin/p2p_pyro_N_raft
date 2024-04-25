import random as rd
import Pyro5.api
import sys
import os
import threading
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .state import State

election_lock = False
@Pyro5.api.expose
class Peer():
    def __init__(self, name:str, port:int, peer_list:list):
        self.name = name
        self.port = port
        self.peer_list = [peer for peer in peer_list if peer != self.port]
        self.daemon = Pyro5.api.Daemon(port=self.port)
        self.uri = self.daemon.register(self, objectId="peer")
        self.ns = Pyro5.api.locate_ns()
        self.state = State.FOLLOWER
        self.has_voted = False
        self.timeout = 0

        th = threading.Thread(target=self.daemon.requestLoop)
        th.daemon = True
        th.start()

    def main_loop(self):

        self.timeout = self.calc_timeout()

        global election_lock
    
        while True:
            print(f'{self.name} - {self.state} - {self.timeout}')
            if self.state == State.FOLLOWER and time.time() > self.timeout and not self.check_election():
                election_lock = True
                self.election()
            if self.state == State.LEADER:
                self.heartbeat()
            time.sleep(0.1)

    def check_election(self):
        global election_lock
        return election_lock

    def calc_timeout(self) -> float:
        now = time.time()
        return rd.uniform(0.15, 0.3) + now

    def heartbeat(self):
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.receive_heartbeat()
            self.timeout = self.calc_timeout()

    def receive_heartbeat(self):
        self.timeout = self.calc_timeout()

    def election(self):
        self.state = State.CANDIDATE
        votes = 1
        self.has_voted = True
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            vote = peer.request_vote()
            if vote:
                votes += 1
        self.timeout = self.calc_timeout()
        if votes > (len(self.peer_list) + 1 ) / 2:
            self.state = State.LEADER
            self.heartbeat()
        else:
            self.state = State.FOLLOWER
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.next_term()
        self.has_voted = False

    def request_vote(self) -> bool:
        self.has_voted = True
        return True

    def next_term(self):
        self.state = State.FOLLOWER
        self.has_voted = False

    def __del__(self):
        self.daemon.shutdown()