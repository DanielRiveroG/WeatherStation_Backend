from datetime import datetime


class EdgeValue:
  def __init__(self, value, timestamp):
    self.value = value
    self.timestamp = timestamp


  def update_max_edge(self, value):
    if self.value is None or self.value < value:
      self.value = value
      self.timestamp = int(datetime.now().timestamp())


  def update_min_edge(self, value):
    if self.value is None or self.value > value:
      self.value = value
      self.timestamp = int(datetime.now().timestamp())


  def reset_value(self):
    self.value = None
    self.timestamp = None

