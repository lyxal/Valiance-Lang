class Identifier:
  def __init__(self, is_error=False):
    self.name: str = ""
    self.property: Identifier | None = None
    self.error: bool = is_error