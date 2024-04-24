# import Pyro5.api
# import threading

# class Daemon(object):

#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(Daemon, cls).__new__(cls)
#             cls._instance.daemon = Pyro5.api.Daemon()
#         return cls._instance
    
#     def get_daemon(self) -> Pyro5.api.Daemon:
#         return self.daemon
    
#     def run(self):
#         self.daemon.requestLoop()

#     def start_on_thread(self):
#         self.th = threading.Thread(target=self.run)
#         self.th.daemon = True
#         self.th.start() 
        

#     def close(self):
#         self.daemon.close()
        


# DAEMON = Daemon()



