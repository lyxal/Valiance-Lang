# The Valiance Programming Language

## Introduction

Valiance is a stack-based array-oriented programming language designed to make the
array programming paradigm accessible to mainstream programmers. It does
so by:

- Incorporating familiar programming constructs from traditional languages
- Providing a tacit and expressive programming environment
- De-emphasising pure mathematical elegance in favour of practicality
- Aiming to actually look like a programming language.

## Language Design Principles

1. **Looking Like Code**: The ultimate goal of Valiance is to make array programming
   look like, well, programming. This means forgoing the traditional symbol-based
   notation of array languages in favour of syntax reminiscent of mainstream languages. Programs should be able to be quickly understood 10 (metaphorical) feet away from the code.
2. **Simplicity**: While simplicity is completely subjective, Valiance should be able
   to pass the pub test. For the non-Australians out there, this means a regular
   programmer should be able to look at Valiance code and say "yep, that's reasonable,
   and makes sense". Ideally, features will "just work" without requiring extra
   consideration, structuring, or handling.
4. **Intentional OOP**: If you've ever used an array language with OO features, you'll
   notice that they feel like a sort of afterthought.
   Valiance integrates object-oriented programming from the start, treating it not as an add-on but as a native and natural feature of the array programming paradigm.
5. **Statically Typed**: Static typing has become a highly desirable feature in modern
   programming languages. And for good reason: it catches more bugs at compile time,
   and allows for potentially compiler optimisations. Array languages, save for
   outliers like Remora and Futhark, are dynamically typed. Breaking the trend,
   Valiance will be statically typed, but in a way that ideally feels dynamic.
6. **Functional Programming**: Array languages are notable for having a lack of first-class
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
8. Modifiers
9. Variables
10. System Keywords
11. Extension Methods
12. Stack Elements
13. Objects
14. Generics
15. Traits
16. Variants
17. Modules
18. Function Annotations

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

#### String Formatting

A common pattern in programming is concatenating strings to other values. For example, personalising a greeting by adding in a person's name. This often leads to a rather unpleasant chain of `+`s, and obscures the intention of inserting data into a string. 

Valiance has two workarounds for this. The first is *string formatting*, which allows for a string to declare placeholder points able to be filled in later. Placeholders are designated with `{}`, and are filled in when the format overload of `%` is used. 

For example:

    "Hello, {}" 

Allows for any value to be inserted in the place of the `{}`:

    "Hello, {}" "Joe" %
	## "Hello, Joe" 

Any operations can be performed on the data in the `{}`:

    "Your string in lowercase is: {lower}" "PiZZa" %
	## "Your string in lowercase is: pizza" 

Placeholders can only include expressionable code, code which is not:

- variable assignment
- extension definition
- object definition
- trait definition

The second workaround is template strings. It can be described as immediate string formatting. Rather than waiting until `%` is used, a template string will pop from the stack to fill its placeholders. A template string starts with `#"`:

    "Joe" #"Hello, {}" 
	## "Hello, Joe"

Placeholders can have the same values as strings used in formatting.
 

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
the same type (well, at least in list literals). More will be said about this in the section on the list model,
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

Where most array programming languages use a rectangular array model, Valiance opts instead for a list-like model. However unlike array languages, like K, that use a standard list model, Valiance has a slightly different perspective on lists.

Lists:

- Can contain any number of items.
- Can be arbitrarily nested.
- Must have all items be the same type.
- Need not have the same number of items in sublists. 

This differs to normal lists which can have a wide mix of types. For example:

```
[1, "2", [3, 4, "5"]]
```

Is completely fine in a language using a normal list model. 

However, these restrictions are merely formalisations for static typing. In practice the list from earlier is completely fine in Valiance. It has the type `Number/String/((Number/String)+)+`. Verbose, but rugged. This lines up with how lists would be represented in a language like Scala. 

### The Rank of Lists 

In array programming, the "rank" of an array is a very important concept. It represents the number of dimensions present in an array. A 2d matrix has a rank of 2. A 3d cube has a rank of 3. This is crucial for determining how to apply operations, especially when it comes to vectorisation (more on that later).

Usually, rank is a difficult concept to apply to a list model; the lack of regularity in dimensions would require a slight change to how rank is defined. However, because Valiance lists are required to have the same type, rank is easily translated from array programming. 

For example, the list from before:

```
[1, "2", [3, 4, "5"]]
```

Is considered to be a rank 1 list of `Number/String/((Number/String)+)`s. 

```
[[1, 2, 3], [4, 5, 6, 7]]
```

Is considered to be a rank 2 list of `Number`s, even though the sublists are of different lengths. 

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
| `OverloadedFunction` | `ℽ` | A function with multiple overloads | `TODO` |
| `Tuple` | `@` | A tuple of multiple values | `@(12, "Hello")` |
| `Constructor` | `⨂` | A constructor for a type | NA |

There is no dedicated list type in Valiance. Rather, lists are expressed as "type operations" upon a base type.

The `+` type operation indicates a rank 1 list of a type. For example, `ℕ+` is a list of numbers. Multiple `+`s increase the rank of the list: `ℕ+++` is a 3d list of Numbers (list of lists of lists of numbers). To save characters, a number can be specified after the `+` to indicate rank. `ℕ+8` is a horribly nested 8 dimensional list of numbers.

However, it is impossible to always know the exact rank of a list: elements like `reshape` can turn a list into any shape, even dynamically generated shapes. Luckily, it is possible to tell the _minimum_ rank of a list - at the very least, a list will be a flat list, regardless of shape. Therefore, the `~` type operation is used to indicate minimum rank. For example, `ℕ~` is at least a flat list of numbers, although it could also be any depth-uniform list. Like `+`, `~`s can be stacked to indicate a higher minimum rank. `ℕ~~` is at least a list of lists of numbers, and each item in the list is at least `ℕ~`. Arbitrary ranks can be specified with a number like with `+`.

`+`s and `~`s can't be mixed in a type, but a `+` list can be used where a `~` list is expected if the rank of the `+` list is >= the rank of the `~` list. In other words, `T+n` is considered `T~m` if `n >= m`.

For example, `T++` can be safely considered as `T~`. On the other hand, `T+` cannot be safely considered as `T~~`.

There are other type operations that can be used in types:

| Operator | Description |
|----------|-------------|
| `+` | A rank 1 list of the type. |
| `~` | A list of at least rank 1 of the type. |
| `^` | A list of at most rank 1 of the type. | 
| `/` | A union of types. |
| `&` | An intersection of types. |
| `?` | An optional type. Same as `T / None`|
| `!` | Exactly an atomic type, never a list. Useful for controlling vectorisation. |

Any type that is not a list is termed "atomic".

### Rank Guards

A type `T` can be followed by `<m, n>` to indicate that the type must be a list be
at least rank `m` and at most rank `n`. This is called a "rank guard". For example, `ℕ<2, 3>` is a list of numbers that is at least rank 2 and at most rank 3.

### The Shape of a List
Any array language enthusiast will be quick to point out that lists — being not-arrays — do not have a shape. "After all," they will say, "what is the shape of `[[1, 2], [3, 4, 5]]` or even `[1, 2, [3, 4, 5]]`?"

While the rectangular concept of *shape* does not translate to rugged lists, it can still be adapted to provide a "close-enough" definition. The shape of a list is the longest sublist at each depth. That means `[[1, 2], [3, 4, 5]]` is a 2×3 list, and `[1, 2, [3, 4, 5]]` is a list of three `Number | Number+`s.


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

The type of a function is `𝔽[<inputs> -> <outputs>]`

Some examples of functions are:

    {(:Number, :Number) => +} ## 𝔽[Number, Number -> Number] (Output inferred)
    {(:Number{2}) => +} ## Same deal
    {(x: Number, y: Number) -> (:Number) => $x $y +} ## Same deal
    {() -> () => } ## 𝔽[]
    {() -> (:Number) => 1} ## 𝔽[;Number];
    {(2) -> (1) =>
        2tuple #match: {
         @(x: Number, y: Number) => $x $y +,
        }
    } ## 𝔽[^1, ^2; Number/^2] (implicit generics)
    {+} ## 𝔽[Number/String, Number/String -> Number/String] Subject to other types present on +
    {(x, y) => $x $y +} ## Also 𝔽[Number/String, Number/String -> Number/String], as type inference can figure out x and y

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
- Parameters and return values can be completely omitted to have the functions inputs inferred from what would suit all elements in the function. The inferred return will be whatever is on the top of the stack
- If parameters are specified, then attempting to pop from an empty stack will cycle back through the parameters. For example, `{(x:Number, y:Number) => ++}` will return `x + y + x`, as popping goes through x, y, then x again. 

The `!()` and `` `backtick` `` function calling forms push all results onto the stack individually. However, it can be useful to automatically group all function results into a tuple. To achieve this, a function can be wrapped in a tuple, causing `!()` to return a tuple of results instead. Additionally, the `` `@name` `` form always auto-tuples the function's results.

### Function Overloading

Much like elements, and other programming languages, functions can be overloaded to perform different behaviours depending on the types of its input arguments. 

Function overloading is accomplished by using the addition element:

    {(:Number!) => "Got a number!"}
	{(:String!) => "String input"}
	+ ~> overloaded
	5 `overloaded` ## "Got a number!"
	"yes" `overloaded` ## "String input"

A function overload's arguments are not allowed to be a prefix of another function overload's arguments. For example, a function `𝔽[Number -> Number]` can't be overloaded with another function `𝔽[Number, Number -> Number]`, as it would be impossible to tell which overload to use if the top of the stack were two numbers. 

_As a consequence, unit functions cannot appear as a function overload_

An overloaded function has type:

    ℽ[𝔽1, 𝔽2, ..., 𝔽n] 

Where `𝔽n` is the type of each function.

### The Return Stack

By default, a function places its return values on the top of its main stack. However, sometimes a value that should be returned is located deeper in the stack. While typical stack manipulation can usually bring such a value to the top, there are cases where that’s not feasible—or simply inconvenient. Variables can be used as a workaround, but a more implicit and streamlined approach is often preferred.

To support this, functions have access to a separate return stack. Values pushed onto this return stack are treated as return values when the function completes.

Use the `#>>` element to push a value onto the return stack.

You can also call a function in such a way that all of its return values are placed directly onto the return stack, rather than the main stack. To do this, use the `#>()` element when calling the function.

To pop a value off the return stack, use `#>_`. 

When a function returns, it first pulls values from the return stack, in the order they were pushed. If that stack doesn’t provide enough values to satisfy the return, the function falls back to the main stack, using its top values to complete the result.

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

Variables are set by prefixing a valid name with a `~>`. Valid names must start with a letter, and can contain `A-Za-z0-9_`. Whatever is on the top of the stack is placed into the variable. 

Adding a `!` after the `~>` will make the variable a constant, meaning it cannot be written to any more. For example, `3.14 ~>!PI` will set `PI` to `3.14`, and attempting to use `3.15 ~>PI` will cause a compile error.

The first time a variable is set, the type can be specified with a colon followed by the type name. However, in most cases, the type of the variable can be omitted, as it can be inferred from the top of the stack. 

Once a variable has a type, attempting to store a value of an incompatible type will result in a compiler error. 

Some examples include:

    10 ~>myNumber
	20 ~>yourNumber: Number? ## Useful for specifying a type that wouldn't be inferred. 
	"Jam" ~>condiment: String ## Redundant, as it would otherwise be inferred as string.

The value of a variable can be retrieved by prefixing the name of the variable with a `$`. This will push the value to the stack. Note that the variable will still contain a copy of the value (i.e retrieving a variable does not empty it). To continue the examples from earlier:

    $myNumber $yourNumber #or: 5 ==
	$condiment " is put on toast" +

All variables are local. This means that modifying a variable in a function will not change a variable with the same name outside of the function. This is called "scoping" in other languages. When a variable is set inside a function, it is added to that function's scope. When a function returns a value, all values inside that function's scope are deleted. 

There is one exception to this. A function returned from another function will retain the values of any variables from outer scopes. This is referred to as "closures" in other programming languages. It can be seen as the returned function taking a snapshot of its environment at the time it was returned. This concept is useful for functional programming constructs.

### Augmented Assignment

The following is a common pattern in programming:

```
0 ~> my_var
$my_var 1 + ~>my_var
```

Valiance provides a shortcut for getting a variable, applying an operation, and then putting the result back into the original variable. A `:` after a variable get will perform that operation on that variable
using items from the stack.

For example:

```
0 ~> my_var
1 $my_var: +
```

## System Keywords

Not all Valiance features can be expressed as elements and functions. Indeed, some programming constructs require special syntax and should be considered additional core units. System keywords start with a `#` an indicate that something is a core Valiance syntax construct. 

System keywords typically fall under these categories:

- Special syntax (eg `#{` for dictionaries and `#"` for template strings)
- Control flow handling
- Object oriented definitions
- Elements that would otherwise be normal elements but need to be protected from addition of user-defined overloads
- Elements that impact compilation (eg type casting)

Objects will be presented later in these specs. For now, some control flow and element-like system keywords are presented. 

### `#if`

The `#if` system keyword takes a function and a number. If the number is non-zero, the function will be called with what is left on the stack. Otherwise, `None`s will be pushed for each value the function would have otherwise returned. 

For example:

```
"secret" ~> password
readline $password ==
#if: {"TOKEN"}
## Top of stack is now type String?
```

Optional types are returned to ensure the stack remains the same size. 

### `#branch`

`#branch` is what would be an if/else block in other programming languages. It takes two functions and a number. If the number is non-zero, the first function is called. Otherwise, the second function is called. The two functions must have the same multiplicity.

For example:

```
3 4 ==
#branch: {
  "Math working just fine"
} {
  "Uh oh"
}
```

### `#match`

`#match` allows for pattern matching akin to Scala's pattern matching. `#match` pops the top of the stack and runs it against a suite of user-defined cases until it finds a suitable match, a default case, or errors with no match found.

A case can be:

- Any expression, matched if the top of the stack `===` the result
- `|` followed by an expression, which will be matched if passing the top of the stack to the expression returns a non-zero value
- A `:` followed by a type, which will be matched if the top of the stack satisfies that type
- `~>` followed by a name, `:`, and a type, which acts like a type match, but stores the result in a variable
- A list destructure match, started with `#[` continuing to `]`
- A tuple destructure match, started with `#(` continuing to `)`
- A `#"` string, pattern matching like `s"` strings in Scala.
- `_` to represent the default case

Cases are separated with `,`. The pattern and function are separated with `=>`

For example:

```
stdin parseInt #match: {
  10 => "Got 10",
  |20< => "Not 10, but less than 20",
  _ => "Don't know what number"
}

[1, 2, 3, 4] #match: {
  @[_, 2, 3, _] => "This will match",
  @[_, 2, _] => "This would also match",
  @[_] => "Also match",
  :Number+ => "Also match",
  :Number~ => "Also match",
  ~>list: Number+ => {$list 5 +}
}

## Similar concept with tuples
```

### `#for`

Valiance does not allow `for` loops that modify the stack, as they would make the stack size and types unknowable. However, Valiance draws inspiration from Scala where `for` loops are used purely for iteration with side effects. The key reason for a `#for` loop is for updating variables in the current scope without the troubles of operating in a function scope.

For example, a for loop could sum the numbers in a list:

```
0 ~> sum
10 one-range #for: {(:Number) =>
  $sum: +
}
```

(Don't do that in practice. Use `sum` or `fold: +`)

## Extension Methods

At this stage, Valiance has enough defined features to solve every programming problem solvable with a programming language. However, this is different to suitability for use in an actual production environment. It can get things done, but it can't do so in a very organised manner. A few more features are needed to boost Valiance from being a fun little toy to workplace ready. 

The first of these features is extension methods. So far, all elements have been pre-defined, and functions have been the main way to bundle user-defined code into a single reusable unit. Extension methods allow for elements to have new overloads added, and for functions to be turned into user-defined keywords. 

Fundamentally, an extension method is more of a compiler directive than a runtime directive. It either adds functionality to an existing element, or creates a new element. 

An extension method requires two things:

1. An element to extend (or create)
2. A new function to perform

Extensions are defined with the `#define` keyword, followed by the name of the element, a colon, and the function to add:

    #define name: {
	  %%%
	}

This adds the function as an overload of the element. Extension methods must follow the same prefix rules as normal function overloads. 

Existing overloads can be overwritten. For example, to make addition actually perform subtraction:

    #define +: {(:Number, :Number) => -}

This will replace the existing definition of `+` when given two numbers. To retrieve the original definition of a built-in element, prefix it with `#@`. 

## Stack Elements

Sometimes, an element cannot be expressed in terms of a function with fixed inputs and outputs. For example, higher-order functions requiring variadic stack manipulation are impossible to represent, with function overloads only able to cover a finite subset of use-cases.

Take for example the `dip` higher-order function. `dip` takes a function, stashes the top of the stack, performs that function, and then pushes the stashed top back to the stack. 

Consider first an implementation of `dip` for monads:

```
#define dip: {
 ([T, U, V] f: 𝔽[T -> U], top: V, :T) ->
 (:U, :V) =>
    `f` $top
}
```

This could be extended to dyads as:

```
#define dip: {
 ([T, U, V, W] f: 𝔽[T, U -> V], top: W, :T, :U) ->
 (:V, :W) =>
    `f` $top
}
```

And triads as:

```
#define dip: {
 ([T, U, V, W, X] f: 𝔽[T, U, V -> W], top: X, :T, :U, :V) ->
 (:W, :X) =>
    `f` $top
}
```

Evidently, this pattern quickly grows unruly. Additionally, these definitions only work for input functions with multiplicity 1 - different multiplicities would require even more overloads.

To this end, elements can have a `#stack` annotation added to indicate that the element definition will operate on whatever is the stack when the element is called. For example, `dip` becomes:

```
#define #stack dip: {(f: 𝔽) =>
  ~>temp
  `f`
  $temp
}
```

When a stack element is called, the element code is type checked against the current stack state. In this way, stack elements are kind of like macros. However, variables defined within a stack element are local to that element, and do not persist after the element is finished.

Some other examples of stack elements include:

```
#define #stack both: {(func: 𝔽) =>
  `@f` ~> temp
  `f` $temp detuple
}

#define #stack fork: {(first: 𝔽, second: 𝔽) =>
  @($first) #peek ~> firstRes
  `@second` ~> secondRes
  $firstRes $secondRes both: detuple
}

#define #stack correspond: {(first: 𝔽, second: 𝔽) =>
  `@first` ~> temp
  `@second` $temp \ both: detuple
}
```

## Object Oriented Programming

Object oriented programming is integrated into Valiance through the usage of record-like objects and multiple dispatch.

Objects can have any number of "members" - attributes specific to that object. Each member has a visibility, which is either readable or private. 

A readable member can be publicly read (ie in any context), but can only be privately written. A private member can only be read and written in a private context (ie inside an extension defined inside the object). 

Objects are defined with the `#object` keyword, and follow this syntax:

    #object Name[Generics] implements [Traits]: {constructor}

(More about generics and traits will be explained in later sections). 

The constructor is just a function with a few key differences:

- Variables set in the constructor are considered members of the object.
  - Normal variables are considered readable
  - Constant variables are considered private
- Function named arguments can be prefixed with `$` to automatically make it a readable member, or `!` to automatically make it a private member.
- No return type can be given to the constructor

Additional constructors can be specified with the `#init` keyword. However, these constructors can only set members defined in the original constructor, and failing to set any non-optional member will result in a compiler error.

For a concrete example, consider a Dog object:

    #object Dog: {($name: String, !ownerName: String, age: Number) =>
	  $age 7 * ~>!age
	  "unknown" ~> breed
	}
	
	#init Dog: {($name: String, !ownerName: String, @(age: Number, breed: String) =>
	  $age 7 * ~>!age
      $breed ~> breed
	}

This creates two constructors for the `Dog` object. One that takes `String, String, Number` and one that takes `String, String, @(Number, String)`. Constructor overloads must follow the same rules as function overloads.

Creating an instance of an object uses the same syntax as calling a function:

    "Fido" "Joe" 5 `Dog`
	"Barker" "Human" 3 $Dog !()
	"Dog" "Non-dog" 1 $Dog call
	
Members can be retrieved by:

- `$variableName.member` or
- `$.member` if the object is on the stack

So far, objects can be created and have multiple constructors, but there hasn't yet been a way to define methods for objects. In Valiance, objects do not own their methods. Rather, elements own extension methods which may be "friendly" (having full read/write access) to objects. To make an extension method friendly to an object, simply include it inside the object definition. For example, consider a rectangle object with private side size attributes:

    #object Rectangle: {(!sides: Number+<4>) =>
	  #define getPerimeter: {() -> (:Number) =>
	    $sides sum
	  }
	}
	#define errorPerimeter: {(:Rectangle) -> (:Number) =>
	  ## $.sides ## Error: Can't access sides
	  sum
	}

The `getPerimeter` extension method is able to read the `sides` list, even though `errorPerimeter` cannot.

Note that inside a friendly extension method, members do not need to be accessed with `$.`.

Friendly extension methods are called just like any other extension method:

    [1, 5, 6, 2] `Rectangle` ~> rectangle
	$rectangle getPerimeter ## 14

If an extension method needs to mutate an object, it needs to make sure it returns the updated object along with any other needed information.

### Function Object Members

_This would have gone in the section on functions, but object members hadn't been discussed yet._

Functions, being objects, have some members of their own:

- `$.arity` - Gets the number of parameters a function takes
- `$.multy` - Gets the number of values returned from a function
- `$.in` - A tuple of all types in the function's parameters
- `$.out` - A tuple of all types in the function's return values

The last two are intended for usage in specifying types. For example:

```
#define #stack both: {(func: 𝔽) -> ($func.out, $func.out) =>
  `@f` ~> temp
  `f` $temp detuple
}
```

The `.out` member will automatically be detupled, as would any references to `.in`.

## Generics

Valiance supports generic types to allow functions and objects to work on any kind of object. For example, consider an element that finds the position of a number in a list of numbers:

```
#define find: {
 (haystack: ℕ+, needle: ℕ) ->
 (:ℕ?) =>
    $haystack zipIndices filter: {
      head $needle ==
    } first last
}
```

Performance issues aside, this performs the desired search. However, it only works with a list of numbers. To make the find element work with strings, a new overload would need to be added:

```
#define find: {
 (haystack: String+, needle: String) ->
 (:ℕ?) =>
    $haystack zipIndices filter: {
      head $needle ==
    } first last
}
```

Notably, the body is the exact same as the numbers overload. Extending this pattern for all desired types would lead to massive codebase sizes and lots of code duplication.

Generic types act as a way to define an algorithm for "some type" to be specified later. Think of it like algebra but instead of substituting numbers, you substitute types.

Functions (and by extension, extension methods) and objects can use generic types. Within functions, generics are declared within the parameter list:

```
{|generics| (arguments) -> (return types) => ...}
```

A generic version of `find` from before would look like:

```
#define find: { |T|
 (haystack: T+, needle: T) ->
 (:ℕ?) =>
    $haystack zipIndices filter: {
      head $needle ==
    } first last
}
```

Generics can also be used in the parameter list. 

For objects, generics come after the object name:

```
#object List[T]: {() =>
  [] ~> items: (T|T+)+
  0 ~> size
}
```

### Generics and List Types

The type represented by `T` will be one rank lower than the input type.

For example, given the following function:

```
{|T| (list: T+) -> (:Number+) =>
  [] ~> seen: T+
  $list #foreach: {(item: T) =>
    $seen $item contains not #if: {$item $seen:append}
  }
  $seen
} ~> uniquify
```

If `uniquify` is passed `Number+`, then `T` will be `Number`. However, if it is
passed `Number++`, then `T` will be `Number+`.

### Indexed Generics

In the parameter list of a function, numbers can be used to specify taking a certain number of items from the stack. Under the hood, the popped items are automatically assigned generic types to allow for this generic behaviour. However, it may be desirable to explicitly reference the generic type of an automatically assigned generic. Therefore, `^n` will refer to the type of argument `n`. 

### Other Notes

- There is no type erasure with generics. If something is passed an object with a generic, both object and generic types are available.
- For now, generics are invariant. This is to keep the initial design simple. Covariance and contravariance may be added at a later date.

## Traits

Valiance has no object inheritance, meaning that subtyping is mostly impossible (lists can be considered a subtype of a base type, but that's more vectorising than subtyping).

However, allowing one type to be accepted where another is expected is a desirable feature of OOP. Therefore, Valiance includes a "trait" system, allowing objects to declare that they implement a specific set of methods. This enables any object that implements a trait to be passed where that trait is expected, granting access to all trait-defined methods and members.

A trait is defined with the `#trait` keyword. The syntax is otherwise (mostly) the same as an object definition:

```
#trait Name[Generics] implements [OtherTraits]: {
  ## Members and required extensions go here
}
```

Notably, the trait body does _not_ have a constructor. 

Only extensions and members defined within the body of the trait need to be implemented by objects implenting the trait. Extensions outside of the trait body will be considered to apply to any object implementing the trait.

Within the trait body, extensions may have a non-empty function body to provide a default implementation. However, all extensions must declare a set of function parameters and return types.

To declare an extension that needs to be implemented:

```
#define #required Name : {(Parameters) -> (Returns)}
```

A default implementation needs no `#required`.

To provide a concrete example of traits:

```
#trait Comparable[T]: {
  #define #required ===: {(this: T, other: T) -> (:Number)}
  #define ===: {|U| (this: T, other: U) -> (:Number) => 0}

  #define #required <: {(this: T, other: T) -> (:Number)}
  #define >: {(this: T, other: T) ->
    $this $other 
    fork: === <
    both: not
    and
  }
}

#object Person implements [Comparable[Person]]: {($name: String, $age: Number) =>
  #define ===: {(:Person, :Person) => both: {fork: $.name $.age pair} ===}
  #define <: {(:Person, :Person) => both: $.age <}
}
```

When an object implements multiple traits, there may be function signature conflicts between trait extension methods with the same name.

For example:

```
#trait A: {
  #define foo: {(:ℕ) -> (:ℕ) => 10}
}

#trait B: {
  #define foo: {(:𝕊) -> (:𝕊) => "Text"}
}
```

An object implementing both `A` and `B` will have two clashing definitions of `foo` (`𝔽[ℕ -> ℕ]` vs `𝔽[𝕊 -> 𝕊]`). To resolve this conflict, an object has to specify an overload for each non-default-implementation extension method. The syntax for doing so is:

```
#define ~TraitName.methodName: ...
```

Where `...` is the definition.

For example:

```
#trait A: {
  #define #required foo: {() -> (:Number)}
}

#trait B: {
  #define #required foo: {() -> (:String)}
}

#object MultiTrait implements [A, B]: {() =>
  #define ~A.foo: {() -> (:Number) => 30}
  #define ~B.foo: {() -> (:String) => "text"}
}

`MultiTrait` ~> baz

{(:A) => foo} ~> f1
{(:B) => foo} ~> f2

$baz `f1` ## Returns 30 - `baz` is passed in an `A` context
$baz `f2` ## Returns "text" - `baz` is passed in a `B` context
```

If default implementations are provided, they will be automatically added to the object:

```
#trait A: {
  #define foo: {() -> (:Number) => 10}
}

#trait B: {
  #define foo: {() -> (:String) => "Text"}
}

#object DefaultTraits implements [A, B]: {() =>}
`DefaultTraits` ~> bar

{(:A) => foo} ~> f1
{(:B) => foo} ~> f2

$bar `f1` ## 10
$bar `f2` ## "Text"
```

A similar principle applies to conflicting members:

```
#trait X: {
  "Text" ~> foo
}

#trait Y: {
  20 ~> foo
}

#object MultiTrait implements [X, Y]: {() =>
  "Hello" ~> ~X.foo
  30 ~> ~Y.foo
}

#object DefaultTraits implements [A, B]: {() =>}

`MultiTrait` ~> mt
`DefaultTraits` ~> dt

{(:X) => $.foo} ~> f1
{(:Y) => $.foo} ~> f2

mt `f1` ## "Hello"
mt `f2` ## 30

dt `f1` ## "Text"
dt `f2` ## 20
```
## Variants

Objects and traits provide enough object-oriented support for comfortable OOPing. However, OOP support can be taken one step further with variants (what might be called `enum`s, `sealed` classes, or sum types in other programming languages). 

Variants allow for subtyping without losing guarantees of exhaustive pattern matching. In other words, a variant is like a trait which has a finite, non-extendable, number of objects implementing the trait.

Variants are defined with the `#variant` keyword, and behave almost exactly the same as `#trait`s. The key difference is that `#object`s defined inside the `#variant` block will be considered subtypes of the variant.

To best illustrate the benefit of variants, compare a trait-based system for describing `Shape`s to a variant-based system:

```
#trait Shape: {
  #define #required area: {() -> (:Number)}
}

#object Circle implements [Shape]: {
  (!radius: Number) =>
  #define area: {$radius square 3.14 *}
}

#object Rectangle implements [Shape]: {
  (!width: Number, !height: Number) =>
  #define area: {$width $height *}
}
```

vs

```
#variant Shape: {
  #define #required area: {() -> (:Number)}

  #object Circle implements [Shape]: {
    (!radius: Number) =>
    #define area: {$radius square 3.14 *}
  }

  #object Rectangle implements [Shape]: {
    (!width: Number, !height: Number) =>
    #define area: {$width $height *}
  }
}
```

While there may not seem like much difference, the variant can be pattern matched without a default case:

```
## Assuming the trait definition

#define typeOf: {(:Shape) =>
  #match {
    :Rectangle => "Got a rectangle",
    :Circle => "Got a circle",
    _ => "Huh???"
    ## If a Triangle object were defined, there
    ## would be no compiler error to indicate a
    ## change is needed.
  }
}
```

vs

```
## Assuming the variant definition

#define typeOf: {(:Shape) =>
  #match {
    :Rectangle => "Got a rectangle",
    :Circle => "Got a circle",
    ## No need for default case
    ## Adding a Triangle object to the variant
    ## will raise an exhausivity error, indicating
    ## changes are needed
  }
}
```

## Modules

The final key to making Valiance production-usable is to have a way for code to be reused between files. Modules, much like in most other programming languages, allow for code in one file to be wrapped in a nice importable unit easily accessed from other files.

By default, each file is a module, and can be imported from other Valiance files. For example:

```
## └── MathLib.vlnc

#define abs: {(:Number) =>
  #match: {
    0 < => negate,
    _ => dup
  }
}

## Imagine there are other functions here
```

```
## └── main.vlnc
#import MathLib
-4 MathLib.abs
```

The name of a module is, by default, the file name with non-keyword characters removed. However, an explicit module name can be provided with the `#module` keyword. This name _must_ be the top statement, and there can only be one `#module` keyword in a file. The module name can only contain keyword characters.

For example:

```
## └── SomeRandomFile.vlnc
#module MathLib

#define abs: {(:Number) =>
  #match: {
    0 < => negate,
    _ => dup
  }
}
```

(`main.vlnc` would remain unchanged)

Modules can be nested by nesting the parent directories of the target file. For example:

```
## └── utils/math/operations.vlnc
#module Operations
```

```
## └── main.vlnc
#import utils.math.Operations
```

### Import Specifics

- `#import Name` will import the _namespace_ `Name`. All objects, traits, variants, and elements have to be accessed as `Name.<name>`
- `#import Name: Alias` is the same as `#import Name`, but all references will need to be `Alias` instead.
- `#import Name{attr1, attr2, ..., attrN}` will import `attr1`, `attr2`, etc, for usage without needing `Name.attr`
- `#import #all Name` will import all objects, traits, variants, and elements into the global namespace. Only use this in exceptional circumstances, as it may lead to naming conflicts
- Valiance prevents circular dependencies between modules. If module A imports module B, then module B cannot import module A, either directly or through any chain of imports.
- Attempting to import conflicting names without disambiguation will result in a compile-time error.

### Module Path Resolution

Valiance resolves module paths as follows:

1. **Relative imports**: Paths starting with `./` or `../` are resolved relative to the importing file's location.
   ```
   #import ./utils  # Imports utils.vlnc from the same directory
   #import ../common/helpers  # Goes up one directory then into common/helpers.vlnc
   ```

2. **Absolute imports**: Paths without leading `.` are resolved from project root or standard library locations.
   ```
   #import math.Operations  # Searches for math/Operations.vlnc in project and standard locations
   ```

3. **Search path order**:
   - Current package directory
   - Project root directory
   - Standard library locations
   - Additional directories specified in project configuration

Module files must have the `.vlnc` extension, but this is omitted when importing.

### Other Notes

- Modules are initialised at import time, executing all top-level code in the module when the `#import` statement is processed. This ensures that any side effects (like registering handlers or initializing resources) happen predictably during program startup.

## Function Annotations

Just like `#define` has support for annotations like `#stack` and `#required`, functions have support for their own annotations:

### `#recursive`

The `#recursive` annotation allows for easier recursion within a function. The `#this` element will call the nearest scoped function with a `#recursive` annotation. For example:

```
{(:Number) #recursive =>
  #match: {
    0 => 1,
    _ => {1 - #this *}
  }
} ~> factorial
```

Is a recursive definition of the factorial function without needing to name the function. Another example is the recursive definition of the fibonacci sequence:

```
{(:Number) #recursive =>
  #match: {
    | [0, 1] contains => 1,
    _ => {fork: {1-} {2-} both: #this +}
  }
}
```

To call a `#recursive` function outside of the currently executing recursive function, `#this[n]` will jump `n` functions up. This should be rarely needed, as it most likely is a sign something needs refactoring.

### `#where`

The `#where` annotation allows for type constraints to be placed on input parameters. This is useful for cases like:

- Ensuring function arities are the same while supporting variable arities
- Specifying that a minimum rank list is `n` ranks lower than another minimum rank list
- Calculating return types based on numerical properties of inputs

If present, the `#where` must come after the return list. The annotation is followed by a `:` and a `{}` wrapped block of constraints. Each condition is separated by a comma (`,`)

For example:

```
#define #stack if: {
  (condition: Number, true: Function, false: Function)
  -> ($true.out / $false.out)
  #where: {
    $true.arity $false.arity ==,
    $true.multy $false.multy ==
  }
  =>
  [$true, $false] condition index call
}
```

In this example, the arity of `$true` and `$false` are guaranteed to be the same. This guarantee cannot be easily made with generics or other data types.

Constraints can also specify properties of types. For example:

```
#define reshape: {|T|
  (list: T~, shape: @(Number...)) -> (:T+$n) #where: {
    $shape length ~> n
  } =>
  ## Body of reshape here
}
```

In this example the return type, an exact-rank list, is set based upon how many arguments are in the `$shape` argument. As a tuple will always have a fixed length at compile time, this constraint can be checked and utilised at compile time.

Operations allowed in the `#where` annotation are:

- Basic math (`+`, `-`, `*`, `/`)
- `dup` / `^`
- `swap` / `` \ ``
- `pop` / `_`
- Variable retrieval
- Variable setting
- `length`
- Unnamed argument reference (`` `n` `` - a different meaning to funciton call because function calls are disallowed)
- Number pushing
- Comparison operators (`==`, `<=`, `>=`, `!=`, `===`)

This list may be expanded in the future.

#### Dynamic Types

In the above examples, there were some unusal return types:

- `$true.out / $false.out`
- `T+$n`

These types are dynamic in that they are not known when writing the types. They are in fact known at compile time.

`$` followed by a variable name and potentially a member access will make the variable value part of the type. The value must fit in the context of the type: `T+$true.out` would cause a compile error, because a function's outputs are not a number. `$n / $false.out` would cause a compile error, because a number is not a type.
