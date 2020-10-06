from datetime import datetime


class EdgeValue:
  def __init__(self, value, timestamp):
    self.value = value
    self.timestamp = timestamp


  def update_max_edge(self, value):
    if self.value < value or self.value is None:
      self.value = value
      self.timestamp = datetime.now()


  def update_min_edge(self, value):
    if self.value > value or self.value is None:
      self.value = value
      self.timestamp = datetime.now()


  def reset_value(self):
    self.value = None
    self.timestamp = None

