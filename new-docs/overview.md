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
otherwise have as arrays. A consequence is that ragged lists will have
a shape that may result in some hypothetically "empty" items. E.g.
`[[1,2],[3,4,5]]` also has shape `[2,3]`, despite the fact `[1,2]` only
has 2 items.
