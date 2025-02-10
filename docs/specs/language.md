## Introduction

Valiance is a stack and array language designed to make the array programming paradigm mainstream friendly. 

### Inspirations

A major inspiration is the Vyxal golfing language. In fact, Valiance started as a proposed version 5 of Vyxal, but exceeded the scope of what it means to be Vyxal. This can be seen through how the two languages share a lot of similarities. 

As such, the only inspiration from other array languages is the choice of built-ins that relate to array manipulation. 

## Important Terms

- _Element_ = A built-in function or a user defined keyword.
- _Arity_ = The number of arguments an element pops from the stack.
- _List_ = A collection of objects, potentially nested. 

## The Stack 

Valiance utilises stacks to perform all operations - data can be pushed to the stack and operations pop data from the stack. The stack can be arbitrarily long, and have any type of item on it. 

## Comments

Single line comments start with `##` and go to the end of the line. 

Multiline comments start with `#/` and continue until a `/#` is found. 

## Numbers 

There is a single number type in Valiance which represents both whole numbers and decimals, as well as complex numbers. A Number can be arbitrarily big and arbitrarily precise (however, not necessarily exact - e.g surds, pi, e might be calculated to a certain number of decimal places). 

The Number type can be "subtyped" as `Number.Whole`, `Number.Complex`, and `Number.Decimal` as needed. 

Numbers can be created with numeric literals:

```
69
420_
69.69
420i69
```

The grammar for numbers is


```
NUMERIC_LITERAL = DECIMAL ("i" DECIMAL)?
DECIMAL = (NUMBER ("." NUMBER)?) "_"?
NUMBER = "0" | [1-9][0-9]+
```


## Strings

Unlike most array languages, Strings in Valiance are objects (as compared to the usual approach of being an array of characters). 

Strings can be created with string literals, which may be multiline. A string can also be a formatted string by prepending `#$`

Some string examples include 

```
"Hello, World!"
"This is a
Multiline
String"
#$"2 + 2 = ${2 2+} - 1 that's $three quick maths" ## Every day man's on the block 
```

The grammar for string literals is

```
STRING_LITERAL = @" ([^"\\] | @\ .)* @"
```

## Lists

Whereas traditional array languages have a rectangular array model as their underlying data structure, Valiance opts for a list model. This means that a collection of objects need not be homogeneous nor rectangular. The philosophy of this design decision is outside of the scope of the specification, as much can be said and debated about the topic. 

Lists are created with square brackets:

```
[] ## Empty list
[1, 2, 3] ## A list of numbers
["Hello", "World!"] ## A list of strings
[[1, 2, 3], ["X", "Y", "Z"]] ## 2x3 list of multiple types
[1, [2, [3, 4]], [[5]]] ## what some will consider "heresy"
```

The grammar for lists is

```
LIST_LITERAL = @[ (LITERAL (@, LITERAL)*)? @]
```

Where `LITERAL` encompasses numbers, strings, lists, functions and any other applicable literal. 

## Functions

Functions are also objects in Valiance. This is in contrast to some array languages, but not a completely foreign concept to array programming. 

Functions can take any number of arguments, but always return a single value (unless it is a unit function). 

Function arguments can be any combination of:

- A number representing how many items to pop
- A type to pop and match from the stack
- A variable to store a value
- A typed variable
- A fusion

Within the arguments, `$`  can be specified as the last argument to indicate the type being returned. `$: T` means an object of `T` will be returned. `$: _` means the function does not return anything and is a unit function.

Some examples of function arguments include:

```
{2+}
{(1) => 2+}
{(2) => +}
{(`Number`, `Number`) => +}
{(x) => $x 2 +}
{(x) => 2 +}
{(x, y) => $x $y +}
{(x, 2) => + $x -}
{(x: Number, y: Number) => $x $y +}
{(@(x: Number, y: Number)) => $x $y +}
{(`Number`, $: Number) => 2 +}
{(2, $:_) => + println}
```

The grammar for functions is:

```
FUNCTION = "{" (GENERICS_DECL? FUNCTION_ARGS "=>")? PROGRAM "}"
GENERICS_DECL = "<" NAME ("," NAME)* ">"
FUNCTION_ARGS = ("`" TYPE "`" | NAME (COLON: TYPE)| NUMBER | FUSION)* ("$:" (NAME | "_"))?
```

## Types

As Valiance is a statically typed language, it makes sense to mention the types that exist within the language, as well as how they interact. 

### Fundamental Types

Fundamental types are built into Valiance, shipped with every installation. Fundamental types also have single character aliases to ease with keystroke count.

```
Number ℕ
Number.Whole 𝕎
Number.Decimal 𝔻
String 𝕊
Function ∫
UnitFunction ⨚
None ∅
Any ⌒
Fusion @
```

The `Fusion` type is a bit special, as it can be extended to indicate what types will be in the fusion:

```
@
@(Number)
@(Number, Number)
```

### Type Operations

One might notice the lack of a dedicated `List` type, which is intentional. After all, `List`s can be as nested or as rugged as one pleases. As an array language, the `List` type should feel like a natural extension of an object, rather than an explicit consideration. Therefore, "type operations" are used to indicate something may be a list:

```
T   = Object with type T
T+  = List of T, potentially nested at any depth
T*  = T | T+
T!  = A list of exactly T. No nesting.
T?  = Optional T (T | None)
T|U = Type T or Type U
T&U = Type T and Type U (i.e traits)
```

The concept of `T+` can be extended to "enforce" minimum depth as a type. While shape is impossible to determine at compile time, the minimum depth of a list can sometimes be inferred. E.g. Mapping a `∫[T+; T+]` (a function taking `T+` and returning `T+`) over `T+` will return a list of at least depth 2. 

This can be realised with more `+`s. The number of `+`s in a type indicate that it will be at least that depth.

E.g.

```
T+ -> List, no clue on depth.
T++ -> At least a list of lists.
T+++ -> At least a list of lists of lists.
T+3 -> Shorthand for T+++
```

and so forth. 

`T+n` is considered to be `T+m` if `n > m`. This means you can safely pass `T++` where `T+` is expected, because `T++` "satisfies" `T+`. `T+` _can_ be used where `T++` is expected, but this will cause a compiler warning. The rationale being that a `T+` _might_ be a `T++`, so it _could_ satisfy `T++`, but it can't be checked until runtime. 

Type casting/shape casting can help with this.

### Generics

Valiance allows for types to use generics. The generic type is kept when type checking (i.e. no type erasure). 

```
- `T[U]` => Type `T` with generic `U`. 
- `T[U;V]` => Type `T` with multiple branches. At this stage, only for functions.
- `∫[T]` => A function taking a single argument of type  `T`
- `∫[T;U]` => A function taking a single argument of type `T` and returning an item of type `U`
- `∫[T;U|V]` => Function taking type `T` with a branch that returns `U` and a branch that returns `V`. 
- `∫[T...]` => This type matches any function that takes one or more arguments of type `T`. This does not mean varargs, but rather allows for specification of a family of function types. 
- `T<U>[U]` => A type `T` with its own defined generic type. The `U` belongs to `T`
- `T<U[V]>[U]` => Type `T` with a generic `U`. `U` implements traits V
```

### Type Interaction

Generally, a type matches another type if:
1. The types are the same OR
2. The required type is a trait and the dependent type implements the trait

Specifically:

- `T[%%%]` is considered `T`.
- `T` is _not_ considered `T[%%%]`
- `T[%%%1]` is only considered `U[%%%2]` if `T == U` AND `%%%1` is considered `%%%2`.
- `T+n` is considered `T+m`, but a compiler warning is given if `n < m`.
- `T` is always considered `⌒`.

### Overload Matching Rules

Say a function has the following overloads, where uppercase letters are types and lowercase letters are traits:

```
1. ∫[T]
2. ∫[T|U]
3. ∫[t&c]
4. ∫[t]
5. ∫[Any]
6. ∫[U+]
7. ∫[U++]
8. ∫[T!]
9. ∫[V*]
10. ∫<H>[T[H]]
11. ∫[T[V]]
12. ∫[M]
13. ∫<H>[U[H]]
```

And imagine the following types:

```
T
U
V implements t, c
W implements t
Z implements t, c
M
```

| Input Type | Matched Overload | Why?
| -- | -- | -- |
| `T` | `1` | |
| `U` | `2` | The union allows for `U` |
| `T\|U` | `2` | Exact match
| `Z` | `3` | Has traits `t` and `c`, more specific |
| `W` | `4` | Only has trait `t` |
| `U` | `5` | No other definition. Doesn't match `13` because of the lack of generic |
| `U+` | `6` | Exact match |
| `U++` | `7` | Exact match. If the `U++` definition wasn't present, `6` would be chosen |
| `T+` | `1`, but vectorised over the input. |
| `V` | `9` | |
| `V+` | `9` | |
| `V!` | `9` | |
| `T[V]` | `11` | Exact match, takes precedence over `10` and `1` |
| `T[U]` | `10` | Would have matched `1` if there wasn't the generic catch-all. |
| `M[V]` | `12` | `M[V]`, in the abscence of other more specific `M`s with generics, matches `M`. |
