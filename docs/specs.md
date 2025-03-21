# The Valiance Programming Language

## Overview

Valiance is a statically typed stack-based array programming language designed
to make array programming accessible to a wider audience. It does so by
de-emphasising the need for cryptic symbols, opting instead for a dash of
verbosity. Ideally, the meaning of programs should be somewhat obvious to
programmers coming from other languages.

## The Stack

As Valiance is a stack-based language, values are pushed onto and popped
from a central stack when performing operations. The stack can hold as
many values as needed, and can store any type of value.

## Literals

### Numbers

- Numbers can be integers, rational numbers, or complex numbers.
- There is no bound on the size of numbers.

```valiance
50
34.3
-5.3
4i3
2.4i-4
```

### Strings

- Strings are enclosed in double quotes.
- UTF-8 encoded.
- Double quotes can be escaped with a backslash.
- `#s"` starts a interpolated string.
- Can be multiline by default.

```valiance
"Hello, world!"
"Hello, \"world\"!"
#s"Hello, #{$name}!"
"Multi
line
string"
```

### Lists

- Lists are enclosed in square brackets.
- Need not be rectangular.
- Can be nested.
- Supports mixed types, but will be represented as a union type.

```valiance
[1, 2, 3]
[1, 2, [3, 4]]
[1, "Hello", 3.4]
```

### Tuples

- Tuples start with `@(` and end with `)`.
- Allow for grouping of values into a single stack value.
- Different from lists in that they are fixed size and type.
- Tuples are immutable, can't be vectorised upon.

```valiance
@("Hello", 1, 3.4)
@("Hello", 1, 3.4, [1, 2, 3])
```

## The List Model

Unlike other array languages, Valiance does not enforce homogenous rectilinear
arrays. Instead, it utilises a list model that allows for sublists to be
of different lengths.

The shape of a list is defined as the greatest rectangle that a list could
effectively be considered. If it looks like a rectangle, and can act like a
rectangle, then it is a rectangle. This is known as effective shape.

The effective shape of a list is defined as the maximum length of lists
at each depth up to the maximum shared depth.

For example, the effective shape of the following lists would be:

```valiance
[[1,2],[3,4,5]] -> [2, 3]
[1, [2,3]] -> [2]
[[1], [[2,3]]] -> [2, 1]
```