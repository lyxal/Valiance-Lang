# The Valiance Programming Language

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
   notice that they feel like a sort of afterthought.
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
6. Vectorisation
7. Functions
   1. Arity-Dependent Functions
   2. Function Overloading
8. Modifiers
9. Variables
10. Extension Methods
11. Objects
12. Generics
13. Traits
14. Modules

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

_Eventually, there will be a reference for all pre-defined elements._

Some elements may be defined for multiple sets of inputs. Each definition is called an overload. For example, addition also performs concatenation of two strings.

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

- `8`
- `53.87`
- `-8`
- `-53.87`
- `8i2`
- `-8i2.3`
- `-8i-2.3`

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
- `[1, 2, 3, "Hello, world!"]`
- `[1, 2, [3, 4, 5], 6]`
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
- List models tend to allow for shorter code than rectangular arrays.

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

## Types

Given Valiance is a statically typed language, there is a type system ensuring data is passed only where it's supposed to go.

Every object in Valiance has a type. Some built-in types are pre-provided:

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
| `ArityDependentFunction` | `𝕗` | A function with an arity and multiplicity unknown, but statically calculatable. | `TODO`|
| `OverloadedFunction` | `ℽ` | A function with multiple overloads | `TODO` |
| `Tuple` | `@` | A tuple of multiple values | `@(12, "Hello")` |
| `Constructor` | `⨂` | A constructor for a type | NA |

There is no dedicated list type in Valiance. Rather, lists are expressed as "type operations" upon a base type.

The `+` type operation indicates a rank 1 list of a type. For example, `ℕ+` is a list of numbers. Multiple `+`s increase the rank of the list: `ℕ+++` is a 3d list of Numbers (list of lists of lists of numbers). To save characters, a number can be specified after the `+` to indicate rank. `ℕ+8` is a horribly nested 8 dimensional list of numbers.

However, it is impossible to always know the exact rank of a list: elements like `reshape` can turn a list into any shape, even dynamically generated shapes. Luckily, it is possible to tell the _minimum_ rank of a list - at the very least, a list will be a flat list, regardless of shape. Therefore, the `~` type operation is used to indicate minimum rank. For example, `ℕ~` is at least a flat list of numbers, although it could also be `ℕ++`, or even a mix of numbers and other number lists. Like `+`, `~`s can be stacked to indicate a higher minimum rank. `ℕ~~` is at least a list of lists of numbers, and each item in the list is at least `ℕ~`. Arbitrary ranks can be specified with a number like with `+`.

`+`s and `~`s can't be mixed in a type, but a `+` list can be used where a `~` list is expected if the rank of the `+` list is >= the rank of the `~` list. In other words, `T+n` is considered `T~m` if `n >= m`.

For example, `T++` can be safely considered as `T~`. On the other hand, `T+` cannot be safely considered as `T~~`.

There are other type operations that can be used in types:

| Operator | Description |
|----------|-------------|
| `+` | A rank 1 list of the type. |
| `~` | A list of at least rank 1 of the type. |
| `/` | A union of types. |
| `&` | An intersection of types. |
| `?` | An optional type. Same as `T / None`|
| `!` | Exactly an atomic type, never a list. Useful for controlling vectorisation. |

Any type that is not a list is termed "atomic".

## Vectorisation

One of the most important aspects of the array programming paradigm is pervasiveness - applying functions across all atomic items in a list. For example, `[1,2,3] + 4` gives `[5,6,7]` as a result. In Valiance, this is referred to as "vectorisation", and the act of doing is called "vectorising". Some elements do vectorise, others do not.

Generally speaking, an element vectorises when it expects an argument of a certain rank, but is given an argument with a higher rank. Atomic values can be considered to have rank 0.

Elements will "dig down" the higher-rank argument until the expected type is reached. For example, `+` is defined for the inputs `Number, Number`. If given `Number+, Number` as input, it will add the second number to each number in the first list.

Vectorisation behaviour changes slightly when multiple higher-ranked lists are given as inputs to an element. Instead of digging down a single list, the element will dig down *multiple* lists at once until a point is reached where all arguments are the expected rank. More specifically:

> If all arguments match the function overload, apply the function. Otherwise, zip, at the maximum shared depth, all arguments that do not match a function argument, keeping matching arguments as-is. To each item in the zip, try the vectorisation algorithm again.

Zipping simply means to group corresponding items across multiple lists. For example, zipping `[1,2,3]` and `[4,5,6]` together gives `[[1, 4], [2, 5], [3, 6]]`.

Therefore, adding `[1,2,3]` and `[4,5,6]` would give `[5, 7, 9]`, as corresponding items are added together (`[1 + 4, 2 + 5, 3 + 6]`).

There is an exception to the vectorisation rule. An element will not vectorise if a higher-ranked argument is given where a `!` type is expected. For example, if addition was instead defined on `Number!, Number!`, calling addition with `Number+, Number` would result in a type error. This allows elements to explicitly _not_ vectorise if it wouldn't make sense to do so. Given the importance of vectorisation in array programming, it is recommended to use the `!` type operation sparingly.

## Functions

Functions are user-definable objects that take input values and transform them into other values. In this way, functions can be seen as a sort of element. Unlike elements, functions are not automatically applied to stack items, but instead reside on the stack until needed.

A function has inputs and outputs. The number of inputs to a function is called the "arity" of a function. The number of outputs from a function is called the "multiplicity" of a function.

As Valiance is stack based, all functions must have a fixed arity and multiplicity - varargs are not allowed (they create too many problems when trying to do static analysis).

Functions are opened with a `{` and are closed with a `}`. The inputs and outputs of a function are specified in the format `(inputs) -> (outputs)`, and is followed by a `=>`. Both inputs and outputs can be empty, and the outputs can be omitted. If outputs are omitted, Valiance will infer the return type from the top of the stack. If inputs or outputs are empty, then the function is considered to take no arguments or return no results respectively.

The inputs part of the function can be a mixed list of:

- A number, indicating to pop that many items from the stack,
- A colon followed by a type, indicating to pop an item of that type from the stack,
- A variable name, indicating to pop an item from the stack and assign it to that variable.
- A variable name followed by a colon and a type, indicating to pop an item from the stack, assign it to that variable, and check that it is of that type.

Similarly, the outputs part of the function can be a mixed list of:

- A number, indicating to push that many items onto the stack,
- A colon followed by a type, indicating to push an item of that type onto the stack,

The type of a function is `𝔽[<inputs>;<outputs>]`

Some examples of functions are:

    {(:Number, :Number) => +} ## 𝔽[Number, Number; Number] (Output inferred)
    {(:Number{2}) => +} ## Same deal
    {(x: Number, y: Number) -> (:Number) => $x $y +} ## Same deal
    {() -> () => } ## 𝔽[]
    {() -> (:Number) => 1} ## 𝔽[;Number];
    {(2) -> (1) =>
        2tuple #match: {
         @(x: Number, y: Number) => $x $y +,
        }
    } ## 𝔽[^1, ^2; Number/^2] (implicit generics)

As seen above, if a function has a number in its argument list, it will have
implicitly created generics. These generics act as if they were normal generics,
but can't be accessed directly in a function body. More will be said about this in the
section on generics.

Here are some key things to note about functions:

- Functions operate on their own stack. What's passed to a function is the only
  external data available to the function.
- Variables outside of a function can only be accessed, not modified.
- However, a variable outside a function will be bound to any returned functions. This
  allows for closures.
- Functions can be called using the `!()` element. 
- If a function is stored in a variable, it can be called by wrapping the function name in backticks. 

### Arity-Dependent Functions

Some functions may need to take a variable number of arguments depending on any
function arguments passed. For example, consider a function named `both`. `both`
takes a function F, and applies F to two sets of (F.arity) arguments. The code

    1 2 3 4 {(:Number, :Number) => +} both

Would return `3` and `7`.

Because functions require a fixed arity, `both` is not possible with normal
functions - while one may think function overloads would work, they aren't
generalised to functions of any arity.

The solution is to use a special type of function called an "arity-dependent
function" (ADF). An ADF is able to refer to the arity of its function type
arguments to effectively simulate varargs. To make the usage of ADFs easier,
only functions with a known arity can be used as arguments to ADFs. This restriction
allows the ADF system to operate within a static type system.

There are some extra limitations to how ADFs can be defined/used, and there's
also some extra semantics to how they work. These will be discussed in the
section about extension methods.

### Function Overloading

Much like elements, and other programming languages, functions can be overloaded to perform different behaviours depending on the types of its input arguments. 

Function overloading is accomplished by using the addition element:

    {(:Number!) => "Got a number!"}
	{(:String!) => "String input"}
	+ ::=overloaded
	5 `overloaded` ## "Got a number!"
	"yes" `overloaded` ## "String input"

A function overload's arguments are not allowed to be a prefix of another function overload's arguments. For example, a function `𝔽[Number; Number]` can't be overloaded with another function `𝔽[Number, Number; Number]`, as it would be impossible to tell which overload to use if the top of the stack were two numbers. 

_As a consequence, unit functions cannot appear as a function overload_

An overloaded function has type:

    ℽ[𝔽1, 𝔽2, ..., 𝔽n] 

Where `𝔽n` is the type of each function.

## Modifiers

A common pattern in functional programming is to pass functions as arguments to other functions.
For example, consider the `map` element, which takes a function and a list, and applies the function to each element of the list. To map the function `{(:Number) => 2 *}` over the list `[2, 4, 5]`, you would write:

    [2, 4, 5] {(:Number) => 2 *} map

Notice how the element always appears after the function. For long functions, this means that
the element will be far away from the start of the function, distancing the element from the
data it operates on. This is not ideal, and can make code harder to read.

In Valiance, an element can be followed by a `:` to "modify" the element to read its function
arguments from the next tokens. This is slightly different to other array languages where
modifiers (or whatever the language calls them) are dedicated keywords/symbols.

To turn the `map` element into a modifier, you would write:

    [2, 4, 5] map: {(:Number) => 2 *}

The `map` element no longer takes a function from the stack, but instead takes the function
directly next to it. The code now reads more naturally, and readers do not need to scan
to the end of the function to see how the function is used.

An element can only be modified if it takes at least one function as an argument.

### Design Rationale

One of the main reasons for treating modifiers as syntactic sugar is to avoid potential duplication of elements. Traditionally, modifiers, by design, require a fixed function to operate on. This creates a fundamental limitation: when only a modifier exists for a functional programming construct, that construct cannot dynamically reference or apply first-class functions from the stack.

To overcome this limitation, it's desirable to introduce a corresponding keyword—one that can access function arguments dynamically from the stack. However, this leads to an overlap in functionality: now both a modifier and a keyword exist for the same purpose. This redundancy leads to one form inevitably being preferred over the other, making the lesser-used form useless.

There is a very simple solution to this problem: realise that modifiers are really just wrappers
around elements. Then, only a single element is required, and the benefits of modifier syntax is
retained.

Notably, this is not a problem in other array languages where functions are not first-class. In fact,
modifiers acting upon fixed functions is the _only_ way to do functional programming in those languages.
The duplication problem is unique to Valiance resulting from its design goals.

As an aside, the `:` was chosen as the modifier symbol because:

1. Originally, modifiers _were_ separate keywords. To help indicate that a keyword was
   a modifier, modifier keywords were suffixed with a `:`. Upon attempting to solve the
   redundancy problem, it was realised that only the `:` needed to be special syntax.
2. `:` already acts as a modifier-esque construct in Valiance. For example, arguments in
   functions can have a type specified after a `:`. The metaphor translates nicely to modifiers.

## Variables 

Variables are stores of data that exist outside of the stack. Each variable has a name, a designated type it can store, and can be retrieved or overwritten ("getting"/"setting" respectively). 

Variables are set by prefixing a valid name with a `::=`. Valid names must start with a letter, and can contain `A-Za-z0-9_`. Whatever is on the top of the stack is placed into the variable. 

The first time a variable is set, the type can be specified with a colon followed by the type name. However, in most cases, the type of the variable can be omitted, as it can be inferred from the top of the stack. 

Once a variable has a type, attempting to store a value of an incompatible type will result in a compiler error. 

Some examples include:

    10 ::=myNumber
	20 ::=yourNumber: Number? ## Useful for specifying a type that wouldn't be inferred. 
	"Jam" ::=condiment: String ## Redundant, as it would otherwise be inferred as string.

The value of a variable can be retrieved by prefixing the name of the variable with a `$`. This will push the value to the stack. Note that the variable will still contain a copy of the value (i.e retrieving a variable does not empty it). To continue the examples from earlier:

    $myNumber $yourNumber #or: 5 ==
	$condiment " is put on toast" +

All variables are local. This means that modifying a variable in a function will not change a variable with the same name outside of the function. This is called "scoping" in other languages. When a variable is set inside a function, it is added to that function's scope. When a function returns a value, all values inside that function's scope are deleted. 

There is one exception to this. A function returned from another function will retain the values of any variables from outer scopes. This is referred to as "closures" in other programming languages. It can be seen as the returned function taking a snapshot of its environment at the time it was returned. This concept is useful for functional programming constructs.
 