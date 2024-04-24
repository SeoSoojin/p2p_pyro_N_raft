import random as rd
import Pyro5.api
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .state import State
from .daemon import DAEMON

@Pyro5.api.expose
class Peer():

    def __init__(self, name:str, port:int, peer_list:list):

        self.name = name
        self.port = port

        self.peer_list = [peer for peer in peer_list if peer != self.port]

        self.uri = DAEMON.get_daemon().register(self, objectId=self.name)
        self.ns = Pyro5.api.locate_ns()
        
        self.state = State.FOLLOWER
        self.timer_ms = rd.randint(15, 20)
        self.last_heartbeat = time.time()

    def get_uri(self) -> str:
        return self.uri
    
    def run(self):

        while True:

            match self.state:
                case State.FOLLOWER:
                    if self.last_heartbeat + self.timer_ms < time.time():
                        self.start_election()

                case State.CANDIDATE:
                    self.candidate()

                case State.LEADER:
                    self.leader()
            
                
    
    def send_message(self, message:str):
        for peer in self.peer_list:
            uri = f'PYRO:peer_{peer}@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.receive_message(self.name, message)

    def receive_message(self, message:str):
        print(f'{self.name} received message: {message}')

    def start_election(self):
        self.state = State.CANDIDATE
        print(f'{self.name} started election')


