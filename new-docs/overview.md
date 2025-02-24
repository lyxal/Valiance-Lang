# Valiance Overview

_Fun fact: This also serves as a general test suite for language features.
Ideally, one day, this file will be able to have examples extracted and
run as tests._

## Introduction

Valiance is a stack-based language. That means that values are pushed to a
central stack, and popped from that central stack when functions are called.

For example,

```intro.basics.simpleAddition
1 2 +
#> 3
```

In this example, `1` and `2` are pushed to the stack, and then the `+` "element"
(what other languages would call "function") pops the two values from the stack,
adds them together, and pushes the result back to the stack.

## Basic Literals

Numbers, strings, and lists can all be immediately pushed to the stack:

```literals.suite
69
#> 69
"Hello, World!"
#> "Hello, World!"
[1, 2, 3]
#> [1, 2, 3]
```

Lists can contain other lists, and need not be homogenous:

```literals.listHeresy
[1, 2, [3, 4], 5]
#> [1, 2, [3, 4], 5]
[1, "Hello, World!", [3, 4], 5]
#> [1, "Hello, World!", [3, 4], 5]
```

## Basics Elements

Elements are the fundamental instructions in Valiance. They pop values from the
stack and, if defined on the values, performs an operation. Here are some
basic elements:

```elements.basicSuite
1 2 +
#> 3
"Hello, World" length
#> 15
[1, 2, 3] first
#> 1
```

## Vectorisation

Depending on how they are defined, some elements can be automatically
"vectorised" when given a list and atomic value. This means that the
operation digs down to "atomic" levels within the list. For example:

```vectorisation.basicSuite
[1, 2, 3] 2 *
#> [2, 4, 6]
[[1, 2], [3, 4]] 2 +
#> [[3, 4], [5, 6]]
```

Whereas other array language usually define vectorisation solely in terms
of shape, Valiance also function overload signatures to determine
how something should be vectorised. If a function expects an atomic
value but is given a list, it will dig down the list.

The vectorisation algorithm is as follows:

> If all arguments match the function overload, apply the function. Otherwise, zip, at the maximum shared depth, all arguments that do _not_ match a function argument, keeping matching arguments as-is. To each item in the zip, try the vectorisation algorithm again.

This means that the following is possible:

```vectorisation.complexSuite
[1, 2, 3] [4, 5, 6] +
#> [5, 7, 9]
[[1, 2], [3, 4]] [[5, 6], [7, 8]] +
#> [[6, 8], [10, 12]]
[[1,2], [3,4]] [5,6] +
#> [[6, 7], [8, 9]]
```

## List Shape

In the world of array programming, array shape is a key concept. Operations
can only be applied if shapes are compatible, and knowing the shape of an
array allows for efficient memory allocation.

The shape of an array is its "rectangular" dimensions. That is, the size
of each dimension if the array were considered an n-dimensional rectangular
shape (like a rectangle, cube, rectangular prism, etc.). For example, the
array `[[1, 2, 3], [4, 5, 6]]` is considered to have shape `[2, 3]`:
two rows and three columns.

The keen among us (!) will notice that the word "array" has been used in
the definition of shape (in contrast to the word "list"). That's because,
in conventional array programming, shape is only defined for arrays.

> [!NOTE]
> This implies that there is a distinction between the concept of an
> "array" and the concept of a "list". Usually, semantics dictate that
> an "array" is a homogenous, rectangular structure, whereas a "list"
> can be a heterogenous, ragged structure. In Valiance, this distinction
> doesn't matter, because there is only lists. However, it is still
> useful to know the difference, as it forms the basis of the ideological
> break from the usual Iversionian school of array thought.

Shape, unfortunately, is not traditionally defined for lists. This stems
from the fact that lists can support ragged structures like `[1, [2, 3], 4]`,
which do not have a definable rectangular shape. The only "shape-esque"
information that can be derived from a list is its length and depth.

While a logically sound compromise, this system deprives collections
of a key piece of information as a consequence of how the collection
was created. `[[1, 2, 3], [4, 5, 6]]` looks like it should have a
shape, but because it's a list, it doesn't.

> [!NOTE]
> One solution here could be to have support for both lists and arrays,
> and to have a way to convert between the two. After all, that's what
> Nial does. I haven't quite figured out what it is about this solution
> that irks me, but something about it feels wrong. Having two different
> collection types isn't something desirable given the rest of the array
> programming world gets away with just one.

...

> [!NOTE]
> Boxed arrays are also a solution. The major drawback with this is that
> it entails boxed arrays. Having to use different modifiers just because
> something has boxes is a nuisance. Code should be called the same
> way regardless of whether an array is ragged or not. Extra handling
> based on shape might be needed inside a function, sure, but calling
> the function should be uniform.

To this end, Valiance extends the defintion of shape to work with all
types of lists - array-like and ragged. This principle is called "duck
shaping", where the effective shape of a list is as close to what it
would be as a rectangular array as possible.

The algorithm for shape is:

```!
1. Find the maximum shared depth of the list - the deepest level in the list all items support
2. Shape = []
3. At each depth up to the maximum shared depth:
3.1. Append the maximum length among all lists at the depth to shape
```

Or:

_Maximum lengths at maximum shared depths._

This gives lists like `[[1,2,3],[4,5,6]]` the rectangular shape they'd
otherwise have as arrays. For ragged lists, the shape will be, effectively,
the largest bounding box that can be drawn around the list.

As expected:

```shape.basicSuite
[1, 2, 3] shape
#> [3]
[[1, 2], [3, 4]] shape
#> [2, 2]
[[1, 2, 3], [4, 5, 6]] shape
#> [2, 3]
[] shape
#> [0]
```

However:

```shape.holUpWaitAMinute
[1, [2, 3], 4] shape
#> [3]
[[1, 2, 3], [4, 5, 6], [7, 8, 9, 10]] shape
#> [3, 4]
[[1], [2, 3], [4, 5, 6]] shape
#> [3, 3]
[[1, 2], [3, 4], 5]
#> [3]
```

## Functions

Functions are objects. There are no named functions, per se, only variables
that happen to hold functions. Functions can take any number of
arguments (arity), and return any number of values (multiplicity). By default,
functions have an arity of 1 and a multiplicity of 1.

Functions are wrapped in `{}`. To include an argument list, use `() =>`.
The argument list can also define generics for the function. More on
generics later.

Arguments can be:

- A number. This pops n values from the call stack and pushes them onto the function stack
- A name. This pops a single value from the call stack and sets a variable with the name to that value
- A colon followed by a name. This attempts to pop a value matching the type specified by the name. If the value does not match, an error is thrown.
- A name with a type. Combines the above two.
- A fusion. If the top of the stack is a fusion, it will unpack its contents into the variables defined. More on fusions later.

These can be mixed and matched as needed.

Functions can have multiple branches. It is not guaranteed that all branches
will be called, as it is up to elements to determine what to do with
multiple branches. Branches are separated by `|`.

The type of a function is `Function[Args; Branch1; Branch2; ...]`, where
`BranchN` is the return type of the Nth branch. The return type of a function
can also be specified with `$:` in the argument list. If both `$:` and multiple
branches are present, the return type will apply to all branches.

Functions are called with `!()`

```functions.simpleFunctions
5 {2+} !() ## 1 value in, 1 value out
#> 7
5 {(1, $: 1) => 2+} !() ## Same thing
#> 7
5 {(:Number, $: Number) => 2+} !() ## Same thing
#> 7
5 {(:Number) => 2+} !() ## Return type inferred to be Number
#> 7
5 {(in) => $in 2 +} !() ## Store arugment in variable "in"
#> 7
5 {(in: Number) => $in 2 +} !() ## Store argument in variable "in" and type-check
#> 7
```

```functions.multipleArguments
5 6 {(:Number, :Number) => +} !() ## 2 values in, 1 value out
#> 11
```

```functions.multipleBranches
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] filter: {2 divides? | 5 >=}
#> [6, 8, 10]
```

## Types

Values have associated types, and all types are known at compile time.

There are some built-in types:

| Type | Unicode Alias | Description | Examples |
|------|---------------|-------------|----------|
| `Number` | `ℕ` | A real number | `1`, `3.14`, `0.0` |
| `Number.Whole` | `ℤ` | An integer | `1`, `0`, `-1` |
| `Number.Rational` | `ℚ` | A rational number | `1/2`, `3/4`, `0/1` |
| `Number.Complex` | `ℂ` | A complex number | `1+2i`, `3.14-1.0i`, `0.0+0.0i` |
| `String` | `𝕊` | A string | `"hello"`, `"world"`, `""` |
| `None` | `∅` | A null value | `∅` |
| `EmptyList` | `⧆` | An empty list | `[]` |
| `Dictionary` | `§` | A dictionary. Can have generics for key and value types | `["hello" = "world"]` |
| `Function` | `𝔽` | A function. Generics for arguments and possibly multiple branches | `{(x) => $x 2 +}` |
| `UnitFunction` | `⨚` | A function that returns nothing | `{($:_) => 1}` |
| `ArityDependentFunction` | `𝕗` | A function with an arity and multiplicity unknown, but statically calculatable. | `{(𝔽, 𝔽, Any{_^_}, $: {_+_}) => ⋯}
| `Fusion` | `@` | A fusion of multiple values | `@(12, "Hello")` |
| `Constructor` | `⨂` | A constructor for a type | NA |

Notably there is no dedicated list type. List types are instead "extensions"
of their base type. A flat list of a type `T` is denoted as `T+`. A possibly
arbitrarily nested list of a type `T` is denoted as `T~`.

`T+` can always be considered `T~`. However, `T~` cannot be considered `T+`.

There is also support for union and intersection types. Union types are
specified as `T/U`, and intersection types are specified as `T&U`.

A type can also be optional, denoted as `T?`. This is equivalent to `T/∅`.