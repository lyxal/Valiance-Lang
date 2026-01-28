class Branch:
  def __init__(self, parent_branch: Branch = None):
    # Unique, branch-dependent mappings
    self.stack: list[VType] = []
    self.variables: dict[Identifier, VType] = {}
 
    # Store the needed info to be able to lookup variables from higher branches
    self.parent_branch = parent_branch

  def push(self, vtype: VType): self.stack.append(vtype)
  def pop(self) -> VType: self.stack.pop()
  def get_variable(self, name: Identifier) -> VType:
    if name in self.variables: return self.variables[name]
    if self.parent_branch is None: raise ValueError("Variable not found")
    return self.parent_branch.get_varaiable(name)

  def set_variable(self, name: Identifier, vtype: VType):
    if name in self.variables:
      assert self.variables[name].compatible_with(vtype)
      return
    self.variables[name] = vtype

  def type_of(self, node: ASTNode) -> VType:
    # Get the type of `node` relative to this branch
    # Don't bother if this is not a node that has a type
    assert isinstance(node, (ListNode, TupleNode, LiteralNode))
    # TODO: Implementation
    return CustomType("Not Implemented Yet")
