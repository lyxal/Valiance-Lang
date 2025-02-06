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