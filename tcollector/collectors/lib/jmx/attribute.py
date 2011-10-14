import os

class Attribute:
  def __init__(self):
    self.attrs = {}

  def load(self, filename):
    if os.path.exists(filename):
      try:
        f = open(filename, "r")
        for l in f:
          items = l.split()
          if len(items) == 2:
            self.set(items[0], items[1])
        f.close()
      except:
        pass
  
  def set(self, name, value):
    self.attrs[name] = value

  def get(self, name, default):
    try:
      return self.attrs[name]
    except KeyError:
      return default
