Name: `dimensions`

Purpose: Utilities for applying functions to named dimensions. Also utilities for applying functions to indexed dimensions.

Example Functions and Objects:

- `Dimension` (object) - represents a named dimension reference.
- `over` (`𝔽[|T, U| in: T~, dim: Dimension, 𝔽[T~ -> U] -> out: U~ ; $in.dims $dim - ~> $out.dims]`) - Apply a function over each sub-list from the target dimension.

---
Name: `aggregators`

Purpose: Higher order functions providing collection functions that would otherwise clutter the default element space. 

Example Functions:

- `collectBy` (`𝔽[|T, U| T+$n, 𝔽[T+$n -> U] -> T+{$m} ; $n 1+ ~> m]`) Group items in a list by collecting items until the result changes, and then collecting from the remaining list again.
