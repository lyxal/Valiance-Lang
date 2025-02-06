# Types

## Primitive Types

- `Number` / `ℕ` => Represents both Whole and Decimal numbers
- `Number.Whole` / `ℤ` => A whole number (like `Int`, but unbounded)
- `Number.Decimal` / `ℚ` => A decimal to any number of decimal places
- `String` / `❞` => String type
- `Function` / `∫` => Function type, can have generics to specify argument type(s)
- `None` / `∅` => None Type
- `Any` / `⧆` => Any

## Type Operations

- `T+` => Array of `T`, can be arbitrarily nested
- `T?` => `T` or `None`
- `T|U` => Union type - Something that is either `T` _or_ `U`
- `T&U` => Intersection type - Something that is `T` _and_ `U`. Usually traits. 

## Generics 

- `T[U]` => Type `T` with generic `U`. 
- `T[U;V]` => Type `T` with multiple branches. At this stage, only for functions.
- `∫[T]` => A function taking a single argument of type  `T`
- `∫[T;U]` => A function taking a single argument of type `T` and returning an item of type `U`
- `∫[T;U;V]` => Function taking type `T` with a branch that returns `U` and a branch that returns `V`. 
- `∫[T...]` => This type matches any function that takes one or more arguments of type `T`. This does not mean varargs, but rather allows for specification of a family of function types. 
- `T<U>[U]` => A type `T` with its own defined generic type. The `U` belongs to `T`
