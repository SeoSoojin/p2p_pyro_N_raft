class State_Machine():
    def __init__(self):
        self.current_state = {}
        self.temp_state = {}
        self.old_state = {}

    def set_attribute(self, attribute:str, value):
        if attribute in self.current_state:
            self.old_state[attribute] = self.current_state[attribute]

        self.temp_state = self.current_state
        self.temp_state[attribute] = value
        
    def commit(self):
        self.current_state = self.temp_state
        self.temp_state = {}

    def rollback(self):
        self.current_state = self.old_state
        self.temp_state = {}
        self.old_state = {}

    def get_attribute(self, attribute:str):
        if attribute in self.current_state:
            return self.current_state[attribute]