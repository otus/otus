class Attribute:
    def __init__(self):
        self.attrs = {}

    def set(self, name, value):
        self.attrs[name] = value

    def get(self, name, default):
        try:
            return self.attrs[name]
        except KeyError:
            return default
