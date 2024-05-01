import json
import random as rd
import Pyro5.api
import sys
import os
import threading
import time
from base64 import b64decode
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .state import State
from .state_machine import State_Machine

election_lock = False 
# This is a global variable that will be used to lock the election process, should be an redis if peers would be in different machines
@Pyro5.api.expose
class Peer():
    """Class that represents a peer or node in the environment"""
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

        self.state_machine = State_Machine()

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
    
    def election(self):

        self.state = State.CANDIDATE
        votes = 1
        self.has_voted = True
        
        # TODO: Implement this using lambda
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

    def heartbeat(self):
        """Heartbeat to maintain the leader's authority, 
        sending messages to the followers and preventing new elections"""
        message = b'heartbeat'
        digest = SHA256.new(message)
        signature = self.signer.sign(digest)
        self.broadcast(lambda peer: peer.receive_heartbeat(message, signature))
        
        self.timeout = self.calc_timeout()

    def request_vote(self) -> bool:
        
        self.has_voted = True
        return True

    def calc_timeout(self) -> float:

        now = time.time()
        return rd.uniform(0.15, 0.3) + now
    
    def become_leader(self):

        self.state = State.LEADER
        ns = Pyro5.api.locate_ns()
        ns.register(f'leader', self.uri)

        public_key = self.keyPair.publickey().export_key()
        self.broadcast(lambda peer: peer.next_term(public_key))

        self.heartbeat()

    def receive_heartbeat(self, message:bytes, signature:bytes):
        """Receives a heartbeat, from leader"""
        if self.verify_signature(message, signature):
            self.timeout = self.calc_timeout()
            
    
    def verify_signature(self, message:bytes, signature:bytes) -> bool:
        """Verifies message signature using leader's public key"""
        try:
            message = SHA256.new(b64decode(message['data']))
            signature = b64decode(signature['data'])
            self.verifier.verify(message, signature)
            return True
        except ValueError as e:
            print(f'Error: {e}')
            return False
        

    def next_term(self, key:bytes):
        """Sets leader public key and passes to next term"""
        key = b64decode(key['data'])
        self.verifier = PKCS115_SigScheme(RSA.import_key(key))
        self.state = State.FOLLOWER
        self.has_voted = False

    def client_request(self, request:str):

        request_json = json.loads(request)

        for key in request_json:
            self.state_machine.set_attribute(key, request_json[key])

        request = request.encode()
        digest = SHA256.new(request)
        signature = self.signer.sign(digest)
        count = 0

        # TODO: Implement this using lambda
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            has_written = peer.leader_request(request, signature)
            if has_written:
                count += 1

        if count > (len(self.peer_list) + 1) / 2:
            self.commit()
            return 
        
        self.rollback()

    def leader_request(self, request:bytes, signature:bytes):
        """Leader requests followers to write the attribute received in the request"""
        if self.verify_signature(request, signature):
            request_json = json.loads(b64decode(request['data']))
            for key in request_json:
                self.state_machine.set_attribute(key, request_json[key])
            return True
        
        return False

    def commit(self):
        """Commits status as gotten in the request"""
        self.state_machine.commit()

        if self.state == State.LEADER:
            self.broadcast(lambda peer: peer.commit())
        
    def rollback(self):
        """Resets status to what it was before the request"""
        self.state_machine.rollback()

        if self.state == State.LEADER:
            self.broadcast(lambda peer: peer.rollback())

    def get_attr(self, attribute:str):
        """Gets the attribute that was changed after the request."""
        #print(f'{self.name}.{attribute}: {self.state_machine.get_attribute(attribute)}')

        if self.state == State.LEADER:
            self.broadcast(lambda peer: peer.get_attr(attribute))
            return self.state_machine.get_attribute(attribute)

    def broadcast(self, action:callable):
        """Method to broadcast an action to the leader's followers"""
        for peer in self.peer_list:
            uri = f'PYRO:peer@localhost:{peer}'
            peer = Pyro5.api.Proxy(uri)
            action(peer)
                
    def __del__(self):
        """Shutsdown daemon"""
        self.daemon.shutdown()