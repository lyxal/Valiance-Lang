# Valiance Type System

## Overview

Valiance is a statically typed array language. This means that types of
values are known and checked at compile time. However, unlike typical
statically typed languages, there is special consideration given to the
nature of array languages: there is no dedicated list type, as lists are
merely extensions of fundamental types.

## Fundamental Types

Valiance has the following fundamental types:

| Type | Unicode Alias | Description | Examples |
|------|---------------|-------------|----------|
| `Number` | `ℕ` | A real number | `1`, `3.14`, `0.0` |
| `Number.Whole` | `ℤ` | An integer | `1`, `0`, `-1` |
| `Number.Rational` | `ℚ` | A rational number | `1/2`, `3/4`, `0/1` |
| `Number.Complex` | `ℂ` | A complex number | `1+2i`, `3.14-1.0i`, `0.0+0.0i` |
| `String` | `𝕊` | A string | `"hello"`, `"world"`, `""` |
| `None` | `∅` | A null value | `∅` |
| `Dictionary` | `§` | A dictionary. Can have generics for key and value types | `["hello" = "world"]` |
| `Function` | `𝔽` | A function. Generics for arguments and possibly multiple branches | `{(x) => $x 2 +}` |
| `UnitFunction` | `⨚` | A function that returns nothing | `{($:_) => 1}` |
| `ArityDependentFunction` | `𝕗` | A function with an arity and multiplicity unknown, but statically calculatable. | `{(𝔽, 𝔽, Any{_^_}, $: {_+_}) => %%%}
| `Any` | `⊤` | A value of any type | `1`, `"hello"`, `∅` |
| `Fusion` | `@` | A fusion of multiple values | `@(12, "Hello")` |
| `Constructor` | `⨂` | A constructor for a type | NA |


## Type Constraint Operators


As mentioned in the overview section, there is no dedicated list type in
Valiance like you might find in typical statically typed languages. So
then how are list types represented? And further, can types have other
types of constraints applied? The answer to both of these questions is
yes. A type constraint can indicate a type is a list, a combination of types,
or even optional. The following table lists the type constraint operators

| Operator | Description |
|----------|-------------|
| `+` | A rank 1 list of the type. |
| `~` | A list of at least rank 1 of the type. |
| `/` | A union of types. |
| `&` | An intersection of types. |
| `?` | An optional type. Same as `T / None`|
| `!` | Exactly an atomic type, never a list. |

Any type that is not a list is termed "atomic".

### More on List Types

The `+` and `~` operators provide a "guarantee" on the rank of the list.
With `+` the guarantee is considered "strong", whereas with `~`, the
guarantee is considered "weak".

The guarantees can be stacked, providing guarantees on higher ranks of lists.
For example, `Number++` guarantees that a value will absolutely be a rank 2 list of `Number`s. `Number~3` guarantees that a value will be a list of at least rank 3 with `Number`s in it.

For example, `Number+` guarantees that a value will absolutely be a flat list of `Number`s.
`Number~` only guarantees a value will be a list of some rank with `Number`s in it. It may be a flat list or it may be arbitrarily nested.

Guarantees cannot be mixed, as that would always equate to a weak guarantee.
However, as will be demonstrated later, a strong guarantee can be weakened
through type inference.

Why have the weak guarantee then? Especially as strong guarantees are effectively
what every other statically typed language provides? The answer is that
some operations may not provide a list with a known compile-time shape.
For example, the `reshape` function can take a list of any rank and
reshape it into a list of any other rank. No amount of strong guarantees
can be made about the output of `reshape`. However, a weak guarantee can
be made: the output will be a list of some rank with the same type as the
input.
