import random as rd
import Pyro5.api
import sys
import os
import threading
import time
from base64 import b64encode, b64decode
import binascii
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .state import State

election_lock = False 
# This is a global variable that will be used to lock the election process, should be an redis if peers would be in different machines
@Pyro5.api.expose
class Peer():
    def __init__(self, name:str, port:int, peer_list:list):

        self.name = name
        self.port = port
        self.peer_list = [peer for peer in peer_list if peer != self.port]

        self.daemon = Pyro5.api.Daemon(port=self.port)
        self.uri = self.daemon.register(self, objectId="peer")

        self.state = State.FOLLOWER
        self.has_voted = False
        self.timeout = 0

        self.keyPair = RSA.generate(bits=1024)
        self.signer = PKCS115_SigScheme(self.keyPair)

        th = threading.Thread(target=self.daemon.requestLoop)
        th.daemon = True
        th.start()

    def main_loop(self):

        self.timeout = self.calc_timeout()

        global election_lock
    
        while True:
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
        message = b'heartbeat'
        digest = SHA256.new(message)
        signature = self.signer.sign(digest)
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.receive_heartbeat(message, signature)
            self.timeout = self.calc_timeout()

    def receive_heartbeat(self, message:bytes, signature:bytes):
        try:
            message = SHA256.new(b64decode(message['data']))
            signature = b64decode(signature['data'])
            self.verifier.verify(message, signature)
            self.timeout = self.calc_timeout()
        except ValueError as e:
            print(f'Error: {e}')
            
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
            self.become_leader()
        else:
            self.state = State.FOLLOWER

        self.has_voted = False

    def request_vote(self) -> bool:
        self.has_voted = True
        return True

    def next_term(self, key:bytes):
        
        key = b64decode(key['data'])
        self.verifier = PKCS115_SigScheme(RSA.import_key(key))
        self.state = State.FOLLOWER
        self.has_voted = False

    def become_leader(self):
        self.state = State.LEADER
        ns = Pyro5.api.locate_ns()
        ns.register(f'leader', self.uri)

        public_key = self.keyPair.publickey().export_key()
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            peer.next_term(public_key)

        self.heartbeat()

    def receive_client_request(self, request:str):
        print(f'{self.name} - {request}')
    
    def __del__(self):
        self.daemon.shutdown()