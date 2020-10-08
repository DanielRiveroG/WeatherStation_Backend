from datetime import datetime


class EdgeValue:
  def __init__(self, value, timestamp):
    self.value = value
    self.timestamp = timestamp


  def update_max_edge(self, value):
    if self.value < value or self.value is None:
      self.value = value
      self.timestamp = datetime.now().strftime("%H:%M:%S")


  def update_min_edge(self, value):
    if self.value > value or self.value is None:
      self.value = value
      self.timestamp = datetime.now().strftime("%H:%M:%S")


  def reset_value(self):
    self.value = None
    self.timestamp = None

