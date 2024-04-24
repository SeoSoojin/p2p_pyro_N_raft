import random as rd
import Pyro5.api
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .state import State

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
                    
    def start_heartbeat(self):

        while self.state == State.LEADER:

            for peer in self.peer_list:
                uri = f'PYRO:peer@localhost:{peer}'
                peer = Pyro5.api.Proxy(uri).heartbeat(f'{self.name} is sending heartbeat to you!')
            
            time.sleep(5)

    def hearbeat(self, message:str):
        
        self.timer_ms = rd.randint(15, 20)
        self.last_heartbeat = time.time()
        print(f'{self.name} received heartbeat: {message}')
    
    def send_message(self, message:str):

        for peer in self.peer_list:
            uri = f'PYRO:peer_{peer}@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.receive_message(self.name, message)

    def receive_message(self, message:str):

        print(f'{self.name} received message: {message}')

    def start_election(self):

        print(f'{self.name} is starting election')
        self.state = State.LEADER
        self.start_heartbeat()


