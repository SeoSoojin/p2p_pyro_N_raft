import Pyro5.api
import json

if __name__ == '__main__':
    ns = Pyro5.api.locate_ns()

    uri = ns.lookup('leader')

    leader = Pyro5.api.Proxy(uri)

    json_data = {
        'name': 'John Doe'
    }

    leader.client_request(json.dumps(json_data))
    attr = leader.get_attr('name')
    print(attr)

