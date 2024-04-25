from pkg.peer import Peer
import threading

if __name__ == '__main__':

    port_list = [50001, 50002, 50003, 50004]
    peer_list = []

    for port in port_list:
        name = f'peer_{port}'
        peer = Peer(name=name, port=port, peer_list=port_list)
        peer_list.append(peer)

    for peer in peer_list:
        th = threading.Thread(target=peer.main_loop)
        th.daemon = True
        th.start()

    while True:
        pass
