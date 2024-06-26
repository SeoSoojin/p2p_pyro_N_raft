import threading
import json
import signal
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from .peer import Peer

class Server():
    def __init__(self):
        self.running = False
        
        self.port_list = []

        with open('./data/peers.json', 'r') as f:
            config = json.load(f)
            self.port_list = config['ports']

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def run(self):

        self.running = True

        peer_list = []
        
        for port in self.port_list:
            name = f'peer_{port}'
            peer = Peer(name=name, port=port, peer_list=self.port_list)
            peer_list.append(peer)

        for peer in peer_list:
            th = threading.Thread(target=peer.main_loop)
            th.daemon = True
            th.start()

        while self.running:
            pass

    def stop(self, signum, frame):
        self.running = False