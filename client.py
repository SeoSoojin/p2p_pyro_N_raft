import Pyro5.api
import json
import signal
import sys

class Client():
    def __init__(self):
        self.running = False

        self.port_list = []

        with open('./data/peers.json', 'r') as f:
            config = json.load(f)
            self.port_list = config['ports']

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        self.functionMap = {
            'get_attr': self.get_attr,
            'set_attr': self.set_attr,
            'exit': self.exit
        }

        self.ns = Pyro5.api.locate_ns()

    def run(self):

        self.running = True

        print('Client running...')
        print('Commands available: ')
        print('1. get_attr <name>')
        print('2. set_attr <name> <value>')
        print('3. exit')
        
        while self.running:
            try:
                command = input("Enter a command: ")
                if not (command.startswith('get_attr') or command.startswith('set_attr') or command=='exit'):
                    print('Invalid command.')
                    continue

                fn_parts = command.split(' ')
                fn_name = fn_parts[0]
                args = fn_parts[1:]

                self.functionMap[fn_name](args)

            except Exception as e:
                print(f'Error: {e}')
                
    def set_attr(self, args:list):
        
        if len(args) < 2 or args[0] == '' or args[1] == '':
            print('Invalid number of arguments.')
            return
        
        uri = self.ns.lookup('leader')

        leader = Pyro5.api.Proxy(uri)

        json_data = {
            args[0]: args[1]
        }

        leader.client_request(json.dumps(json_data))

        
    def get_attr(self, args:list):

        if len(args) < 1 or args[0] == '':
            print('Invalid number of arguments.')
            return
        
        uri = self.ns.lookup('leader')

        leader = Pyro5.api.Proxy(uri)

        attr = leader.get_attr(args[0])
        print(f'{args[0]}: {attr}')


    def exit(self, args:list):
        self.running = False
        sys.exit(0)
    def stop(self, signum, frame):
        self.running = False

if __name__ == '__main__':
    main = Client()
    main.run()


