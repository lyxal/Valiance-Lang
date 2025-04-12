# The Valiance Programming Language

<!--

Come with me,
and you'll be,
in a world of array language indignation.

Take a look,
and you'll see,
non-rectangular arrays.

And a whole bunch of other stuff that will make array language regulars
cry.
-->

## Introduction

Valiance is an array-oriented programming language designed to make the
array programming paradigm accessible to mainstream programmers. It does
so by:

- Incorporating familiar programming constructs from traditional languages
- Providing a tacit and expressive programming environment
- De-emphasising pure mathematical elegance in favour of practicality
- Aiming to actually look like a programming language.

## Language Design Principles

1. **Looking Like Code**: The ultimate goal of Valiance is to make array programming
   look like, well, programming. This means forgoing the traditional symbol-based
   notation of array languages in favour of syntax reminiscent of mainstream languages.
2. **Simplicity**: While simplicity is completely subjective, Valiance should be able
   to pass the pub test. For the non-Australians out there, this means a regular
   programmer should be able to look at Valiance code and say "yep, that's reasonable,
   and makes sense". Ideally, features will "just work" without requiring extra
   consideration, structuring, or handling.
3. **Intentional OOP**: If you've ever used an array language with OO features, you'll
   notice that they feel like a sort of afterthought. (Most times, that's because they are.)
   Valiance integrates object-oriented programming from the start, treating it not as an add-on but as a native and natural feature of the array programming paradigm.
4. **Statically Typed**: Static typing has become a highly desirable feature in modern
   programming languages. And for good reason: it catches more bugs at compile time,
   and allows for potentially compiler optimisations. Array languages, save for
   outliers like Remora and Futhark, are dynamically typed. Breaking the trend,
   Valiance will be statically typed, but in a way that ideally feels dynamic.
5. **Functional Programming**: Array languages are notable for having a lack of first-class
   functions, opting instead for more "call-on-site" syntax and "second-class" objects (
   or at least, not first-class). First-class functions allow for a more expressive functional
   programming experience.

## Table of Contents

1. The Stack
2. Elements
3. Literals
4. The List Model
5. Types
6. Functions
   1. Arity-Dependent Functions
   2. Function Overloading
7. Modifiers
8. Variables
9. Extension Methods
10. Objects
11. Traits
12. Modules

## The Stack

The stack is the fundamental concept of Valiance. All operations are performed
on the stack, with data being pushed to and popped from the stack as needed.

A stack is pretty much a list that only allows items to be appended ("pushed") and only
allows the last item to be removed ("popped"). Multiple values can be pushed
or popped at once.

The stack can contain any number of items, and the items need not be of the same type.

Attempting to pop from an empty stack will result in a compile-time error.

## Elements

What you would call "built-ins" or "primitives" in other languages are called
"elements" in Valiance. The idea is that they are the fundamental building blocks
of Valiance programs.

They take input from the stack, perform some operation, and push the result back onto the stack.

Some examples of elements are:

- `+` / `add` / `plus`: Adds two numbers together.
- `-` / `subtract` / `minus`: Subtracts the second number from the first.
- `length`: Returns the length of a list.
- `map`: Applies a function to each element of a list.

Eventually, there will be a reference for all pre-defined elements.

## Literals

Numbers, strings, lists, tuples, and dictionaries all have literal syntax in Valiance.
That means that it is possible to write them directly in code.

### Numbers

Numbers follow the syntax:

    NUMERIC_LITERAL = DECIMAL ("i" DECIMAL)?
    DECIMAL = "-" NUMBER ("." [0-9]+)? 
    NUMBER = 0 | ([1-9] [0-9]*)

The presence of `i` in a number indicates that it is a complex number.

A number is negative if it starts with a `-`, and there is no space between the `-` and the number.

There is no limitation on number size nor precision.

Examples:

- `69`
- `420.69`
- `-69`
- `-420.69`
- `69i420.69`
- `-69i420.69`
- `-69i-420.69`

### Strings

Strings are opened and closed with double quotes. They can contain any character except
for double quotes, which must be escaped with a backslash. Further, strings can
span multiple lines, and the line breaks will be preserved in the string.

The syntax is:

      STRING_LITERAL = '"' ([^"\] | ESCAPED_CHAR)* '"'
      ESCAPED_CHAR = "\" [\"]

Examples:

- `"Hello, world!"`
- `"Hello, \"world\"!"`

    "Hello
    World!"

### Lists

Lists are opened and closed with square brackets. List items can be any
Valiance construct that is not:

- variable assignment
- extension method definition
- object definition
- trait definition

Items are separated by commas, a design choice made for familiarity and
clarity.

Lists can contain any number of items, can be empty, and can even
be arbitrarily nested. Additionally, list items do not need to be of
the same type. More will be said about this in the section on the list model,
because this list model breaks the traditional array model of array languages.

Examples:

- `[]`
- `[1, 2, 3]`
- `[1, 2, 3, "Hello, world!"]` (sacrilege, allegedly)
- `[1, 2, [3, 4, 5], 6]` (look away uiuaboos, APLers and other array language users)
- `[[1], [2, 3], [4, 5, 6]]`

### Tuples

Tuples are a bit like lists but with a few key differences:

- They contain a fixed number of items, with fixed types.
- Values in a tuple cannot be changed after the tuple is created.
- Values cannot be added or removed from a tuple after the tuple is created.
- Tuples are not rectangular, and do not have a shape.

While this may seem useless, tuples are useful for tasks like representing
state between function calls, or for passing multiple values to a function.

Tuples are opened with `@(` and closed with `)`. Items are separated by commas,
and follow the same rules as list items. Tuples can be empty, and can even be
nested.

Examples:

- `@()`
- `@(1, 2, 3)`
- `@(1, 2, 3, "Hello, world!")`
- `@(1, 2, @(3, 4, 5), 6)`
- `@([1], [2, 3], @(4, 5, 6))`

### Dictionaries

Dictionaries are mappings of keys/labels to values. They might be called
hashmaps, tables, or associative arrays in other languages. They are opened
with `#{` and closed with `}`.

Key-value pairs are separated by commas, and the key/value pair itself
is delimited with a colon.

Keys can only be strings. Values can be any Valiance construct that is not:

- variable assignment
- extension method definition
- object definition
- trait definition

Examples:

    #{
      "firstname": "Joe",
      "lastname": "Mama",
      "age": 69,
      "height": 420.69,
    }

    #{}

    #{"attr1": [1,2,3], "attr2": #{}, "attr3": 69}

## The List Model

Whereas the typical array language uses rectilinear arrays, Valiance instead
opts for a more flexible list model. This is because:

- The rigidity of rectangular arrays can be hard to reason about.
- Sometimes you want to have a list of lists of different lengths, without
  having to resort to approaches like boxing or padding.
- The list model is more familiar to most programmers, and is easier to understand.
- List models tend to allow for shorter code than rectangular arrays. (As evidenced
  by the fact that in the realm of code golf, the top ~23 languages all use a list model).

However, unlike list models in languages like K, lists in Valiance will be
considered rectangular if it is possible to do so. If a list looks like it's
rectangular, and can act like it's rectangular, it will be treated as a rectangular array.

This "duck shaping" ideology extends to the algorithm used to determine the shape
of a list. Although a rectangular shape is not guaranteed for lists, the shape
of a list can be thought of as the biggest bounding box that can be drawn around the list. This shape is called the "effective shape" of a list.

The effective shape of a list can be found using the following algorithm:

    1. Determine the maximum shared depth (D) across all elements.
    2. For each level `i` from 0 to D-1:
       a. At that depth, compute the maximum length of any list.
       b. Append that length to the shape list.
    3. Return the shape list.

And summarised as:

_Maximum lengths at maximum shared depths._

This gives lists like `[[1,2,3],[4,5,6]]` the rectangular shape they'd
otherwise have as arrays. For non-rectangular lists, the result may
seem a bit odd, but it is the best approximation of the shape of the list.

    [[1,2],[3,4,5]] -> [2, 3]
    [1, [2,3]] -> [2]
    [[1], [[2,3]]] -> [2, 1]
