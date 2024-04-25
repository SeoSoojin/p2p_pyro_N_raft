import Pyro5.api

if __name__ == '__main__':
    # look for leader on name server

    ns = Pyro5.api.locate_ns()

    uri = ns.lookup('leader')

    leader = Pyro5.api.Proxy(uri)

    leader.receive_client_request("cliente 1")

