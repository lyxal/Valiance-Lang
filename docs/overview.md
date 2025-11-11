# 0. Prologue 

Some of what you're about to read will be considered horribly offensive to array programming traditionalists. Heretic, even. 

If you find yourself up in arms about any of the concepts outlined in this language overview, you have my apologies. 

But then again, if you're that stuck in the trench of strict conformity to Iversonian ideals, perhaps you're part of the reason this language exists ;) 

# 1. Introduction

Valiance is a stack-based array language that moves beyond the traditional "notation as a tool of thought" dogma into "notation as a tool of _doing_". More specifically, Valiance takes the aspects of Iversonian array languages that provide such beautiful clarity of thought and balances them with practicality.

The defining features of Valiance are that it:

- Provides an inherently integrated interface to the array programming paradigm, while still being useful for software development.
- Favours conceptual brevity over literal brevity.
- Intentionally incorperates other programming paradigms like Object-Oriented and Functional Programming, rather than tacking them on as afterthoughts.
- Comes with a large suite of pre-made built-ins, rather than forcing users to build from a limited set of primitives.
- Strives to be accessible to more than just mathematicians and array-language fanatics.

Ultimately, Valiance acts to elevate array languages beyond rough sketches and algorithmatic prototypes. Valiance brings array languages to the software development table.

# 2. The Stack

## 2.1. Theory

Valiance is a stack-based programming language. This means that all computing operations take place around a centralised stack. But what exactly is a stack? 

Consider, for a moment, a pile of plates. Those familiar with English might also call this a "stack" of plates.

If one desires to take a plate from this pile, and not create a mess of broken pottery, they have to take the top plate off the pile. Likewise, if one desires to add more plates to the pile, they have to put the plates at the top of the pile. 

In Valiance, stacks operate exactly the same way, but with data instead of plates. When performing an operation, like addition, the data at the top of the stack is used, and the result is put back on top. The act of taking a value from the stack is called a "pop" and the act of putting a value on the top of the stack is called a "push". 

As a further example, consider a pile of dirty plates that need to be washed. While there are plates to be cleaned, the plate at the top of the pile will be removed, scrubbed, and placed into a new "clean plate" pile. This demonstrates how stack-based systems manage work — each operation depends on the last result, building up a history that’s undone or consumed one step at a time.

## 2.2. Practical

In Valiance, most (more on the exceptions later) operations are performed on a global stack. There is only one global stack. Here are some specifics about the global stack:

- It starts empty at the beginning of every program.
- It can contain any number of items.
- It can have items of different types stored on it.
- Trying to pop from an empty global stack is a compile error.

# 3. Basic Stack Items

What good is a stack if it is not storing anything?  Valiance has 7 fundamental types of values that can be stored on the stack:

1. Numbers
2. Strings
3. Lists
4. Tuples
5. Dictionaries
6. Functions
7. Objects

This section of the overview will outline the semantics and syntax of Numbers, Strings, Tuples and Dictionaries. The other three types require their own sections.

## 3.1. A Note on Literals

A literal in Valiance is syntax that pushes the corresponding stack item.

## 3.2. A Note on Comments

While not a stack item, Valiance supports single line comments and multiline comments. Comments are little human-readable notes one can leave in a program to make it clear what a section of code is doing. The compiler completely ignores comments. 

### 3.2.1. Single Line Comments 

A single line comment begins with `#:` and continues until the next newline character. 

```
#: This is an example comment
#: It ends at the end of the line
```

### 3.2.2. Multiple Line Comments

A multiple-line comment starts with `#{` and continues until a matching `}#` is reached. 

```
#{ This is a comment
that continues over
multiple lines. }#
```

## 3.3. Numbers

Numbers in Valiance are the same as any number one would use in real life. Well, almost. Numbers can be of any size, any precision, have a complex part, and sometimes represent an exact Real number (e.g surds, multiples of pi, multiples of `e`, `ln(2)`). 

The syntax for numbers is:

```
NumericLiteral := Decimal ["i" Decimal]
Decimal := ["-"] Number ["." Number]
Number := "0" | (<1-9> {<0-9>})
```

Valid examples of numbers include:

```
0
12
459.243
-83
-14.3
0.6
3i4
8.2i4
9.2i1.6
-8i3
9.2i-3
-9.2i-2.6
```

## 3.4. Strings

Strings in Valiance are similar to those found in languages like Python, JavaScript, and Julia. They are standalone objects, UTF-8 encoded, and indexed by grapheme clusters rather than by raw code points or bytes. Strings have arbitrary length and are immutable. Unlike in many array-oriented languages, Valiance strings are not treated as arrays of characters. Instead, they are atomic text values — single, indivisible units that can, when needed, be viewed or manipulated as sequences of characters depending on context.

Strings can span multiple lines without needing to escape newlines.

The syntax for strings is:

```
StringLiteral := '"' {<non double quote> | '\"'} '"'
```

Valid examples of strings include:

```
"Hello, World!"
""
"There's a \"quote\" in my string"
"This
String
Spans
Multiple
Lines"
```

### 3.4.1. String Interpolation

- `$""` for string interpolation a la scala.

## 3.5. Tuples

Tuples in Valiance are heterogeneous immutable collections of objects.

Their primary purpose is to act as a collection type with a well-defined compile-time length. Tuples can contain any finite number of items. 

The syntax for tuples is:

```
TupleStructure := L_PAREN [Value {COMMA Value}] R_PAREN
```

Valid examples of tuples include:

```
()
(1, 2, 3)
(1, "string", 6.2)
((1, 2, 3), ("ab"), ("abc", 1, 2, 3))
([1, 2, 3], [4, 5])
```

## 3.6. Dictionaries

Dictionaries in Valiance allow for a key-value mapping, similar to dictionaries/hashmaps/JSON. A dictionary can have any number of key-value pairs.

Any value that implements the `stdlib.Hashable` trait can be used as a key. 

`=` is used to separate keys and values.

Keys in a dictionary are unique. Writing to an already present key will overwrite the old value. 

Attempting to retrieve a key that is not present in a dictionary is a runtime error.

The syntax for dictionaries is:

```
DictionaryStructure := "[" [
  Value EQUAL Value {Value} {COMMA Value EQUAL Value {Value}
] "]"
```

Valid examples of dictionaries include:

```
[
  "name" = "Joe",
  (10, 20) = [1, 2, 3],
  "x" "y" + = 3 4 +
]
```

# 4. Types 

Every value in Valiance has a type. Types describe what a value is, what it can do, and how it can interact with other values. They prevent category errors, guide compiler optimisations, and act as a shared language between programmer and machine.

## 4.1. Simple and Composite Types

The simplest types correspond directly to the basic literals of the language. All numbers have the type `Number`, and strings have the type `String`. Tuples combine multiple values of potentially different types — for example, `(1, 2, "3")` has the type `(Number, Number, String)`. Dictionaries express mappings between types, such as `Dictionary[String -> String]`, where both keys and values have well-defined types.

These simple types form the foundation of the type system. From here, Valiance builds outward into more expressive structures.

## 4.2. Optional, Union, and Intersection Types

Valiance allows types to describe more than fixed categories — they can also express choice and conditional presence.

An optional type, written as `T?`, represents either a value of type `T` or the special value `None`. It’s often used for variables that may not yet have a value assigned.

A union type, `T|U`, indicates that a value may be one of several specific types — for example, a function that returns either a `String` or an `Error`.

An intersection type, `T&U`, is the opposite: it describes a value that satisfies multiple type constraints at once. For instance, an object might simultaneously implement two traits, each providing its own set of methods.

These forms give Valiance a flexible but precise way to express the full range of possible values a variable might hold.

## 4.3. Lists as Type Operations

Rather than defining a dedicated “List” type, Valiance treats lists as *type operations* applied to other types. Dimensionality is expressed directly in the type itself.

The `+` operator denotes a list of a fixed rank. For example, `Number+` is a one-dimensional list of numbers, `Number++` is a list of lists (a rank-2 list), and `Number+3` represents a rank-3 list.

The `*` operator indicates a *minimum* rank rather than a fixed one. `Number*` means “at least a flat list of numbers,” while `Number**` means “at least a list of lists.” Numeric suffixes can again specify depth — `Number*4` represents a structure that’s at least four levels deep.

The distinction is straightforward: `+` describes an exact shape, while `*` describes a lower bound. Any value of type `T+n` can safely be treated as type `T*m` if `n ≥ m`. For example, `T++` can safely be used where `T*` is expected, but not the other way around.

Irregular, or “ragged,” lists are represented using the tilde operator (`~`). A `T~` value can contain `T`, or lists of `T`, or any further combinations thereof. Basically, items of `T~` are `T|T~`. Multiple tildes (`T~~`, `T~3`, etc.) extend the level of nesting. These notations allow ragged and regular data to share the same conceptual framework.

The absolute base type of a list can be represented as `T_`.

Curly brackets may also be used to control grouping and operator precedence within complex type expressions. This allows for explicit composition of type operations — for example, `{Number|Number+}+` represents a list whose elements may be either individual numbers or lists of numbers. Grouping ensures that nested type structures remain unambiguous even when combining multiple operations.

Through these operations, Valiance’s type system treats structure and dimension as first-class ideas, making arrays, lists, and nested data all part of one coherent model.

## 4.4. Casting Between Types

There are times when the compiler cannot infer the exact type of a value, but the programmer can. In these cases, Valiance allows explicit *type casting* using the form `as NewType`.

Casting tells the compiler to treat a value as a specific type — for example, converting a value known to be a `Number*` into a `Number+` if the programmer knows it is a flat list. This allows for controlled flexibility without discarding type safety entirely.

## 4.5. Bridge to Lists

With this foundation in place, lists can be understood not as isolated data structures but as an expression of type behavior itself. In Valiance, lists emerge naturally from the type system rather than existing apart from it — dimensionality, rank, and nesting are all matters of type composition, not special syntax. The next section explores this idea in depth, showing how lists form the practical core of Valiance’s execution model and how this unified approach allows irregular, high-rank, and mixed data structures to coexist under a single coherent design.

# 5. Lists and the List Model

Lists are central to Valiance. They are the primary data structure through which most computation occurs, reflecting Valiance’s identity as an array language. However, in Valiance, lists are not arrays. Instead, they form a superset of arrays — providing all of the same capabilities while allowing for more general, heterogeneous, and irregular structures.

For a detailed rationale behind the choice of a list model over an array model, see *Appendix A.1.2*.

## 5.1. General Properties

Lists in Valiance are defined by a few simple but powerful properties:

* They can contain any number of "items", including infinite sequences.
* They can contain items of any type, even heterogeneous ones.
* They have a well-defined rank, derived from their type structure, not from the runtime shape of their contents.

## 5.2. Rank and Type Structure

The rank of a list is the number of nested list layers present in its type, not the maximum depth of any single item.

Formally:

* Non-list values have rank 0.
* A list of rank-`n` item has rank `n + 1`.
* If a list contains items of different ranks, their item types form a union type at that level, but the list itself still contributes exactly one layer of rank.

Under this definition, rank becomes a purely type-based property, independent of the list’s shape or uniformity.

For example:

```
[[1, 2], [3, 4]]
```

has the type `Number++` — a rank-2 list of numbers, identical to what an array model would call a 2D array.

```
[[1, 2], [3, 4, 5]]
```

is also a `Number++`. The differing sublist lengths do not affect rank, because the dimensionality implied by the type remains the same.

```
[[1, 2], 3, [4]]
```

has the type `{Number|Number+}+` — a rank-1 list whose items may be either numbers or rank-1 lists of numbers.

```
[[1, 2], 3, [[4]]]
```

has the type `{Number|Number+|Number++}+`, again a rank-1 list. Despite the deeper nesting in one item, the outer list adds only one level of rank.

This generalises neatly:

```
[
  [[1, 2, 3], 4],
  [5, 6, 7]
]
```

has the type `{Number|Number+}+2` — a rank-2 list whose items may be numbers or rank-1 lists of numbers.

This type-based definition of rank extends naturally to irregular or ragged data structures. It allows operations that depend on rank — such as broadcasting or reduction — to apply consistently without special-casing. In essence, rank describes type depth, not geometric uniformity.

## 5.3. Syntax

Lists are constructed using square brackets, following a straightforward syntax:

```
ListStructure := L_SQUARE [Value {COMMA Value}] R_SQUARE
```

This form applies to all lists, regardless of rank or content type. The type of a list is inferred from its items according to the rules above, with union types and list operators (`+`, `*`, `~`, `!`, and grouping parentheses) providing explicit control when necessary.

# 6. Variables

Variables are stores of data that exist outside of the stack. Each variable has a name, a designated type it can store, and can be retrieved or overwritten ("getting"/"setting" respectively).

Getting a variable follows this syntax:

```ebnf
VariableGet:= "$" Name
Name := (<any letter> | "_") {<any letter> | "_" | <any digit>}
```

Setting a variable follows this syntax:

```ebnf
VariableSet := VariableGet EQUAL SimpleItem {SimpleItem} NEWLINE
```

Valid examples of getting and setting variables include:

```
$pi = 3.14
$languageName = "Valiance"
$numbers = [5, 2, 7, 4]

$pi
$languageName
$numbers
```


The type of a variable is determined when it is first set. This type can be controlled by using `as Type`. This is primarily useful for empty lists or values that are optional types.

There are no global variables. Variables can only be set in the scope they are defined (this will become apparent when functions are introduced). 

Trying to get a variable that hasn't been defined or hasn't been set is a compile error.

Trying to set a variable to a value that has a type incompatible with that variable's type is a compile error. For example, the following snippet is invalid:

```
$number = 10
$number = "string" #: Compile error - string can't be assigned to Number
```

Notably, the following are not errors:

```
$listA = [] as Number~     #: Type: Number~
$listB = [] as Number*     #: Type: Number*

$listA = [[1, 2, 3]]        #: OK: Number~ accepts ragged lists
$listB = [$listA, [$listA]] #: OK: Number* accepts "at least rank 1"
```

## 6.1. Constants

A constant is a variable that cannot be changed after initial assignment. 

The syntax for constants is as follows:

```
VariableConst := "const" VariableSet
```

Attempting to assign to an already assigned constant is a compile error. 

For example:

```
$piVar = 3.14
$piVar = 3.15 #: Valid, but incorrect
const $PI = 3.14
$PI = 3.15 #: Error
const $PI = 3.15 #: Also error
```

## 6.2. Augmented Assignment

_Editor's note: will need to be moved to the section where `:` as a modifier is introduced. It's only here for completeness while writing the draft, because the section on `:` hasn't been written yet_

When using variables, it is a common pattern to update the variable based on its value. For example, incrementing a variable by 5 might be written as:

```
$x = $x 5 +
```

This is a little bit verbose, so Valiance provides syntax sugar to make it shorter:

```
$x: {5+}
```

# 7. Elements

Data is useless unless you can do something with said data. After all, what is the use of having a 3 and a 4 lying around if they can't be combined to get 7?

What other programming languages call built-in functions, operators, primitives, or (if you're J or K inclined) verbs, Valiance calls "elements". Specifically, an element is something that:

- Takes inputs from the stack
- Directly applies an operation
- Pushes its results to the stack

The second condition there is the key one. Elements perform their action as soon as they are used. This distinction will become important when considering function objects, which satisfy conditions 1 and 3, but do not necessarily execute as soon as they are on the stack. 

Some common elements include:

```
+ (Number, Number) = Add two numbers
- (Number, Number) = Subtract two numbers
* (Number, Number) = Multiply two numbers
/ (Number, Number) = Divide two numbers
sum (Number+) = Add all of the items of a list of numbers together
```

Some examples of these elements in practice include:

```
3 4 + #: 7
8 2 - #: 6
5 6 * #: 30
5 2 / #: 2.5

[3, 5, 2] sum #: 10
```

Note that the order stack items are passed to elements is reversed relative what is popped. That is, the top of the stack isn't always used as the "left most" argument. 

## 7.1. Element Overloads

Elements can do different things based on the types of the items on the stack. 

For example, in addition to performing addition when given two numbers, `+` will perform string concatenation when given two strings. 

That is:

```
3 4 + #: 7
"Hello" "World" + #: "HelloWorld"
```

Each definition of `+` is called an overload. Elements can have any non-zero number of overloads. 

Overloads are unique. More will be said about this in the section that talks about user defined elements.

## 7.2. Syntax

The syntax for an element is:

```
Element := ElementFirstChar {ElementChar}
ElementFirstChar := <A-Z>|<a-z>|"-"|"+"|"*"|"%"|"!"|"?"|"="|"/"|"&"|"<"|">"
ElementChar := ElementFirstChar | <0-9>
```

## 7.3. Terminology 

- The number of inputs an element takes is called its "arity".
- An element may be mixed arity, depending on the type signatures of its overloads.
- The number of outputs an element returns is called its "multiplicity".
- Like arity, multiplicity may vary between elements.
- It is recommended that element arity and multiplicity be consistent among overloads.

## 7.4. Element Call Syntax

While elements usually take their arguments from the stack, it is possible to use mainstream-style `()` to explicitly specify an argument. 

For example:

```
3 4 +
+(3, 4)
```

Are equivalent. Additionally:

```
[1,2,3] sum
sum([1,2,3])
```

Are also equivalent.

Arguments can be named:

```
"This is a string" " " split
"This is a string" split(" ")
split("This is a string", " ")
"This is a string" split(on = " ")
split(item = "This is a string", on = " ")
split(item = "This is a string", " ")
```

And more are all equivalent.

`_`

## 7.5 Overload Disambiguation 

If an element overload cannot be determined from the stack, a compile error will be raised. This will commonly arise from elements with overloads that have different arities. 

For example, say the following overloads of an element named `finger` exist:

```
finger (Number) -> (Number)
finger (Number, Number) -> Number
```

The following program would be problematic:

```
3 4 finger #: which element named finger should be called?
```

The ambiguity arises from both overloads being valid. 

And while `finger(3, 4)`  and `finger(_, _)` disambiguate to the two number overload, it doesn't give a way for the single number overload to be called when the stack contains two numbers. 

To this end, the exact overload can be specified by providing the types in square brackets after the element name:

```
3 4 finger[Number] #: Single number overload
3 4 finger[Number, Number]
3 4 finger[Number](5)
```

# 8. Functions

Functions are user-definable objects that take input values and transform them into other values. In this way, functions can be seen as a sort of element. Unlike elements, functions are not automatically applied to stack items, but instead reside on the stack until needed.

Dissimilar to (most - BQN acts as an outlier here) other Iversonian array languages, functions are first class citizens. This means that functions are just as much stack items as say numbers, strings, and lists.

Just like elements, functions have inputs, outputs, and optionally overloads. 

## 8.1. Syntax

The syntax for functions is as follows:

```
TypeWithRepeat := Type ["*" Number]

FunctionStructure := FUNCTION_DELIM [
  L_PAREN [
    [Name] COLON TypeWithRepeat {COMMA [Name] COLON TypeWithRepeat}
  ] R_PAREN
] [
  ARROW
    [ TypeWithRepeat {COMMA TypeWithRepeat} R_PAREN ]
  
] L_CURLY Program R_CURLY
```

## 8.2. Function Type Signature

The type of a function is specified as:

```
Function[input -> output]
```

The `[...]` can be omitted to represent a function with any inputs and outputs. Such a function cannot be called - only functions with input and output in the type can be called. 

Examples of function types include:

```
Function[Number, Number -> Number]
Function[Number+ -> Number]
Function[Number -> ]
Function[ -> String]
```

## 8.3. Calling a Function

A function can be called using `call`. It expects the function to be the top of the stack, followed by its arguments. Arguments can also be specified in element call syntax. 

## 8.4. Function Execution

When a function is called, it creates its own local stack and scope, separate from the calling context. The function's parameters are pushed onto this local stack as initial values.Argument Reuse: If a function's operations consume more items than are currently on the stack, the function's arguments are automatically reused in order. This eliminates the need for explicit duplication and stack shuffling in many common patterns.
For example, given arguments 3 and 4:

```
fn(:Number, :Number) { + + }
```

Execution proceeds as:
```
Stack: [3, 4]
+      → [7]        (consumed 3 and 4)
+      → [10]       (consumed 7 and 3 - first argument reused)
```

This function cycles through arguments as needed:

```fn(:Number, :Number) { + + + + + } call(3, 4)

Stack trace:
[3, 4]  +  → [7]
[7]     +  → [10]   (reuse 3)
[10]    +  → [14]   (reuse 4)  
[14]    +  → [17]   (reuse 3)
[17]    +  → [21]   (reuse 4)
Result: 21
```

This is useful because many operations naturally want to repeatedly combine a result with the same base values. Without reuse, you'd need explicit duplication (`^`) before each operation. Argument reuse makes these patterns concise and natural.

Whatever remains on the function's stack becomes the return value. If the stack is empty but the return type expects values, arguments are reused if type-compatible.

## 8.5. Function Input and Output Inference

If the input list is omitted from a function, the parameters will be inferred from the operations inside the function. 

If the return list is omitted from a function, the return will the top of the stack at the end of the function. Only a single item will be returned in this case. If the stack is empty, void of even the initial arguments, the return type will be inferred as empty.

## 8.6. Quick Functions

`fn {x}` is very long for when `x` is a single element. `'x` is shorthand for `fn {x}`:

```
[[1, 2, 3], [4, 5, 6], [7, 8, 9]] 'length map
#: Of course, equivalent to map: length
```

# 9. Vectorisation

A defining feature of array programming languages is the ability to automatically apply operations over a whole list without explicit iteration. 

For example, to add `4` to each number in the list `[1, 2, 3]` one might write one of the following approaches:

```
[1, 2, 3] map: {4+}
[1, 2, 3] 4 zipwith: +
[1, 2, 3] 4 '+ bind map
```

However, Valiance allows for:

```
[1, 2, 3] 4 +
```

To accomplish the same result without needing extra elements and functions. 

This behaviour is called "vectorisation". Vectorisation works by repeating a lower rank argument for every item in a higher rank list and applying the operation pairwise. This repeating behaviour is called "broadcasting".

Where other array languages utilise the shape of arguments to determine how to vectorise, Valiance utilises the types of arguments. The highest ranked argument defines how lower ranked arguments should be broadcast. 

For example, in this snippet:

```
[[1, 2], [3, 4]] [5, 6] +
```

`[5, 6]` will be broadcasted as `[[5, 6], [5, 6]]`, meaning the result will be:

```
[[1, 2] + [5, 6], [3, 4] + [5, 6]]
= [[1 + 5, 2 + 6], [3 + 5, 4 + 6]]
= [[6, 8], [8, 10]]
```

Monadic functions, functions that only take one argument, do not need to worry about broadcasting. Single-argument operations recursively apply to nested structures until reaching the expected type.

Dyadic functions will broadcast the lower ranked argument to the higher ranked argument. If there is a mismatch in length of any paired lists, then whatever is present in the longer list is kept as-is. For example:

```
[1, 2, 3] [4, 5] +
#: [1 + 4, 2 + 5, 3]
#: [5, 7, 3]

[[1, 2], [3, 4, 5]] [10, 20] +
#: [[1, 2] + [10, 20], [3, 4, 5] + [10, 20]]
#: [[1 + 10, 2 + 20], [3 + 10, 4 + 20, 5]]
#: [[11, 22], [13, 24, 5]]
```

For functions taking 3 or more arguments, the same broadcasting rules apply, but an error is thrown if there is length mismatch - the reasoning being that it is hard to definitively know which arguments should be kept as default. This is why dyadic vectorisation works just fine with mismatching shapes, as it is reasonable to keep unpaired values unchanged, preserving all information from both inputs

However, if a function being vectorised takes arguments of optional types, then length mismatches will not error if all non optional arguments are present. Missing arguments will be treated as None. Such a function will even take priority over dyadic vectorisation.

```
fn(x: Number, y: Number?, z: Number) { ... }

[1, 2, 3] [4, 5] [6, 7, 8] call
#: [fn(1,4,6), fn(2,5,7), fn(3,None,8)]
#: No error because y is optional
```

## 9.1. Preventing Vectorisation

There is an exception to the vectorisation rule. An element will not vectorise if a higher-ranked argument is given where a `!` type is expected. For example, if addition was instead defined on `Number!, Number!`, calling addition with `Number+, Number` would result in a type error. This allows elements to explicitly _not_ vectorise if it wouldn't make sense to do so.

## 9.2. Fine-grained Vectorisation Control 

_It's recommended you come back to this section after reading about generics_

Say you have `Number+++` on the stack, and an element named `finger` that is defined for a generic `T+`. And say you want to vectorise that element at a `Number+` level. 

Just calling the element won't trigger the dig down effect, because `T = Number++` in this case. 

And while you can `map: map: finger`, that's horribly long and doesn't scale well to higher ranked lists. 

Instead, you can use the same type specification syntax that disambiguates overloads to control what rank is passed to the element:

```
finger[Number+]
```

This will case `T = Number`, meaning `finger` will dig down to the `Number+` level as desired. 

# 10. Modifiers

## 10.1. The `:` Modifier

Passing functions to other functions is a common pattern in Valiance. For example, `map` is an element that takes a function and a list, and applies that function to every item in the list.

However, this requires wrapping code in a function:

```
fn {...} map
```

When mapping a single element over a list, this adds extra ceremony:

```
fn {length} map
```

And when mapping a long function over a list, by the time you see that you're mapping a function, there's a good chance you'll forget the purpose of the function:

```
fn {
  ...
} map #: Wait, what was the function doing again?
#: How is it supposed to map?
```


- Most important modifier
- Has several meanings, depending on syntax context

- Element context = specify function arguments inline. Useful for readability (eg. `reduce: +` instead of `fn {+} reduce`.
	- All function arguments must be specified.
	- If overloads have a different number of function arguments each, then:

```
 CompileError: Cannot freeform modify element `Name` with inconsistent function parameters. Try specifying the overload. 
```

So:

```
elem: a b    #: Fine if all overloads have 2 function args
elem[A, B]: a b #: needed if different number
```

This is because there would be parsing ambiguities otherwise - how would the difference between `(Function[x -> y], Number)` and `(Function[x -> y], Number, Function[x -> y])` be determined from `10 elem: a b`.

- Variable context = augmented assignment. `$name: elem` is the same as `$name = fn {$name elem}`.

- Example:

```
$x = 10
$x: {5 +}
println($x) #: 15
```

## 10.2. The `~` Modifier

- Infix fork.
- `elem1 elem2~ elem3` == `fork: elem1 elem3 elem2`
- Useless on monads
- Extends to n-adic functions by:

```
E1 nadic~ E2 E3 ... En
#: same as
fork: fork: fork: ...: E1 E2 E3 ... En nadic
```

```
[1, 4, 6, 12] sum /~ length
#: same as
[1, 4, 6, 12] sum /` {[1, 4, 6, 12] length}
#: same as
fork: sum length /
```

## 10.3. The `^` Modifier 

- Not strictly a modifier like the other three
- But instead, the duplicate modifier
- `^` by itself == `dup`

```
3 ^ #: [3 3]
1 2 ^ #: [1 2 2]
```

- Can also have labels:

```
^[current stack pattern -> things to copy to top]
```

For example:

```
1 2 3 ^[a b c -> a c c b a] #: [1 2 3 1 3 3 2 1]
```

`_` can be included as a "ignore this item on the stack":

```
1 2 3 ^[a _ b -> a b a b] #: [1 2 3 1 3 1 3]
```

## 10.4. The `\` Modifier

- Also not strictly a modifier like `:`, `` ` ``, or `~`.
- More like `^`.
- Instead of `dup`, `swap`.
- `\` by itself == `swap`

```
3 4 \ #: [4 3]
1 2 3 \ #: [1 3 2]
```

- Can also have labels:

```
\[current stack pattern -> things to move to top]
```

For example:

```
1 2 3 \[a b c -> a c c b a] #: 1 3 3 2 1
```

Note that it removes the initial copies of the stack pattern. This makes the `_` idea even more powerful:

```
1 2 3 \[a _ b -> a b a b] #: [2 1 3 1 3]
```

# 11. Partial Application

- Consider a function to keep numbers in a list smaller than a target number.
- Conventionally:

```
fn (ns: Number+, target: Number) -> :Number+ {
  $ns filter: {$target <}
}
```

- However, that's a little verbose. And also doesn't suit auto-inference.
- One might try:

```
fn {^[ns, _ -> ns] < keep}
```

- Better, but requires a little bit of stack shuffling. Also, surely functional programming can be used here.
- What if original idea, but implicit:

```
fn {<(_, #) filter}
```

- The `#` in `<(_, #)` means "fill this argument in `<` to be whatever is on the stack". Basically, `fn {# <}`.
- It'll push a function object of the partially applied function.
- Very useful for functional programming without verbosity.

# 12. Control Flow Structures
## 12.1. `match`

- Pop stack value and test against several branches. Execute code of first matching branch
- Branches start with the branch type. Branch type is one of:
	- `exactly`
	- `if`
	- `pattern`
	- `as`
	- `default`
 
- `exactly` branch matches if top of stack exactly matches case.
- `if` branch matches if top of stack, after case, is truthy
- `pattern` is like scala pattern matching.
	- String exactly like scala
	- List -> `_` = single item placeholder, `...` = greedy placeholder, `$name = _` = capture placeholder, `$name = ...` = capture greedy placeholder.
	- Same business with tuples.
- `as` is both match on type, and match into variable
	- `as :Type` -> just the type
	- `as $name: Type` -> match into name if type
	- `as $name` -> named catchall
- `default` is just the default case.

- Branch = `type ... -> code,`. `->` separates, branch ends on `,`.

- Here are some defining examples:

```
stdin.readLine parseInt
assert {^ nonNull}
match {
  exactly 10 -> "Number was 10",
  if 20 < -> "Number was less than 20",
  default -> "I don't know that number"
} println

#: Note that only the first branch will run
#: But that all patterns here would match
[1, 2, 3, 4] match {
  pattern [1, _, 3, 4] -> "Match!",
  pattern [1, $middle = ..., 4] -> "Match!", #: $middle = [2, 3]
  pattern [..., 4] -> "Match!",
  pattern [...] -> "Match!", #: Basically a catchall list
  pattern [1, 2, 3, 4] -> "Match!", #: Equal to:
  exactly [1, 2, 3, 4] -> "Match!" 
}

#: Imagine some union type is on the stack
match {
  as :Number -> "Got a Number",
  as $str: String -> $"The string is $str",
  as $def -> "The default case"
}
```

## 12.2. `assert`

- Basically like assert in any programming language
- `assert {cond}` - throw exception if cond gives falsey result.
- But wait there's more.
- `assert {cond} else {errorValue}` - if cond gives falsey result, immediately return `Error(errorValue)`.
- Note that `assert {cond} else {value}` in a function automatically promotes that function's return type to a `Result[T, E]`.
- `assert {cond}` without `else` doesn't promote the type.
- `assert ... else ...` great for validation.

Consider:

```
fn validateNumberFromString(num: String) {
  assert {$num notEmpty} else {"Input was empty"}
  $num parseInt
  assert {^ notNone} else {"Input not numeric"}
  $parsed = unwrap #: Number, but safe
  assert {$parsed 0 >} else {"Negative number"}
  $parsed
}
```

## 12.3. `if`

- It's an if statement, but only one branch.
- Execute the branch if the top of the stack is truthy.
- `if (cond) {code}`
- Return type is the top of the stack type of `code` but optionalised. `None` is returned if not executed.
- `code` is executed with stack function semantics
	- variables can be changed
	- but everything in the stack created by `code` deleted after code finishes.

```
if (2 2 + 5 ==) {"Uh oh"} #: String? - Will most likely be None
```

## 12.4. `branch`

- `if`, but with a second branch.
- execute first if truthy, second otherwise.
- return type = union of two branches

```
branch (3 4 <) {
  "3 is smaller than 4. The world is as it should."
} {
  "Mathematics has gone very severely wrong."
} #: Should return the first string.
```

## 12.5. `foreach`

- Eager stack-semantic-enabled map
- realistically, don't use this, unless really needing the eager eval
- `foreach (name) {code}`

```
$sum = 0
range(1, 10) foreach ($n) {$sum: +}
#: Don't do that in practice
```

## 12.6. `while`

- `while (cond) {code}`
- Another stack-semantic structure. Repeat code while cond is truthy. Condition creates its own stack, filled with previous tops of stack.
- First iteration = take args from stack.
- Return = last top of stack of code.

```
10 while (0 >) {
  println(^) decrement
} #: prints 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
#: returns 0
```

## 12.7. `at`

- A way to control vectorisation, applying a function `at` certain depths
- `at (levels) {code}`
- `levels`  is a list of names (i.e. variable identifiers), followed by an optional arbitrary number of `+`s
- Each name corresponds to an argument, and specifies when to stop digging down when vectorising.
- For example:

```
[[1, 2], [3, 4]] [5, 6]
at (list+, item) {append}
#: Gives
#: [[1, 2, 5], [3, 4, 6]]
```

- In the example, `append` is applied for every list in `[[1, 2], [3, 4]]` zipped with every item in `[5, 6]`
- While `append[Number+, Number]` would work, what if it weren't as easy to specify the type?
- `at` makes it so that you do not have to worry about the type.
- Another example:

```
[[[1, None, "s"], ["h", 5, None]]] #: {String|Number}?+3
#: You _could_ write
getOrElse[{String|Number}?](0)
#: Or, simply
at (_) {getOrElse(0)}
```


# 13. The `define` structure

- Important enough to have its own section.
- Adds an overload to an element
- Very similar to `fn`, but `define` instead.
- Doesn't push a function, writes to element.
- Can be used just like any other element, no `$` needed.
- Elements names can't be reserved words.
- Element name can be any valid element name.
```
define[Generics] name(args) -> returnType {
  ...
}
```

- Redefining an overload overwrites it within module scope. This is fine because you're either knowingly overwriting it yourself, or you're intentionally importing an overwrite from another file. Confusion only happens on purpose
- For example

```
define x(:Number) {3}
define x(:Number) {4}
5 x #: 4
#: Not 3.
```


# 14. Objects

- Structs like C or Rust, rather than classes 

```
object[Generics] Name implements [Traits] {
  ...
}
```

- Objects have associated members, but don't own any methods.
- 3 levels of member visibility:
1. Public (open write, open read)
2. Readable (internal write, open read)
3. Private (internal write, internal read)
- Members are set like

```
public $name = value
readable $name = value
private $name = value
```

- Elements defined inside the object are called "object friendly elements". These elements can read and write all members.
- Elements outside can read and write public members, but can only read readable members and have no access to private members.
- `define ObjectName` inside an element defines an overload for the constructor
- Constructor parameters can specify members inline
- All constructors must set all members from all other constructors. This avoids null items. Members declared outside a constructor don't need to be set.
- The above requirement can either be in parameters or in the constructor body.
- Inline style members are like `define Name(access name: Type)`. Parameters without an access level are just normal parameters.
- Object friendly elements do not receive a copy of the object in the stack, but can retrieve the object in its current state with `self`. That'll push an object with all the current values for each member.
- The `@self` annotation can be used to make an object friendly element automatically add `self` as a returned value. It'll be on the top of the stack after any other returned value
- Members can be accessed in 2 ways
1. From a variable using `$name.member`
2. From the top of the stack using `$.member`
- Some examples
```
object Counter {
  readable $count = 0
  define Counter() {}
  define Counter(initial: Number) {$count = $initial}
  define @self increment() {
    $count: {1+}
  }
  define decrement() {
    $count: {1-}
    self
  }
  define @self reset() {$count = 0}
  define toString() {$"Counter(count=$count)"}
  define +(:Number) -> Counter {
    
  }
}

define CounterFrom0() {
  Counter[]()
}
define doubleCounter(:Counter) {
  Counter($.count 2 *) 
}

Counter(5) increment increment
$c = ^
$c.count println
```

# 15. Traits

Valiance has no object inheritance, meaning that subtyping is mostly impossible (lists can be considered a subtype of a base type, but that's more vectorising than subtyping).

However, allowing one type to be accepted where another is expected is a desirable feature of OOP. Therefore, Valiance includes a "trait" system, allowing objects to declare that they implement a specific set of methods. This enables any object that implements a trait to be passed where that trait is expected, granting access to all trait-defined methods and members.

A trait is defined with the `trait` keyword. The syntax is otherwise (mostly) the same as an object definition:

```
trait Name[Generics] implements Traits {
  #: Members and required extensions go here
}
```

Notably, the trait body does not have a constructor.

Only extensions defined within the body of the trait need to be implemented by objects implenting the trait. Extensions outside of the trait body will be considered to apply to any object implementing the trait.

Within the trait body, extensions may have a non-empty function body to provide a default implementation. However, all extensions must declare a set of function parameters and return types.

To declare an extension that needs to be implemented:

```
define @required Name(parameters) -> returns {...}
```
A default implementation needs no #required.

To provide a concrete example of traits:

```
trait Comparable[T] {
  define @required compareTo(other: T) -> Number {}

  define ===(other: T) {
    self compareTo($other)
    0 ===
  }

  define <(other: T) {
    self compareTo($other)
    -1 ===
  }

  define >(other: T) {
    self compareTo($other)
    1 ===
  }
}

object Person implements Comparable[Person] {
  define Person(
    readable name: String,
    readable age: Number
  ) {}

  define compareTo(other: Person) {
    $age $other.age compareTo
  }
}
```

When an object implements multiple traits, there may be function signature conflicts between trait extension methods with the same name.

For example:

```
trait A: {
  define foo(:Number) -> Number {10}
}

trait B: {
  define foo(:Number) -> Number {20}
}
```

An object implementing both `A` and `B `will have two clashing definitions of `foo`. To resolve this conflict, an object has to specify an overload for each non-default-implementation extension method. The syntax for doing so is:

```
define TraitName.methodName(...){...}
```

For example:

```
trait A: {
  define @required foo() -> Number {} 
}

trait B: {
  define @required foo() -> String {}
}

object MultiTrait implements A, B {
  define A.foo {30}
  define B.foo {20}
}

$baz = MultiTrait()

$f1 = fn (:A) {foo}
$f2 = fn (:B) {foo}

$baz $f1() #: Returns 30 - `baz` is passed in an `A` context
$baz $f2() #: Returns 20 - `baz` is passed in a `B` context
```

If default implementations are provided, they will be automatically added to the object.

# 16. Variants

Objects and traits provide enough object-oriented support for comfortable OOPing. However, OOP support can be taken one step further with variants (what might be called `enum`s, `sealed` classes, or sum types in other programming languages). 

Variants allow for subtyping without losing guarantees of exhaustive pattern matching. In other words, a variant is like a trait which has a finite, non-extendable, number of objects implementing the trait.

Variants are defined with the `variant` keyword, and behave almost exactly the same as `trait`s. The key difference is that `object`s defined inside the `#variant` block will be considered subtypes of the variant.

To best illustrate the benefit of variants, compare a trait-based system for describing `Shape`s to a variant-based system:

```
trait Shape {
  define @required area() -> Number {}
}

object Circle implements Shape {
  define Circle(readable radius: Number) {}
  define area {$radius square 3.14 *}
}

object Rectangle implements Shape: {
  define Rectangle(
    readable width: Number,
    readable height: Number
  ) {}
  define area {$width $height *}
}
```

vs

```
variant Shape {
  define @required area() -> Number {}

  object Circle {
    define Circle(readable radius: Number) {}
    define area {$radius square 3.14 *}
  }

  object Rectangle {
    define Rectangle(
      readable width: Number,
      readable height: Number
    ) {}
    define area {$width $height *}
  }
}
```

While there may not seem like much difference, the variant can be pattern matched without a default case:

```
#: Assuming the trait definition

define typeOf(:Shape) {
  match {
    as :Rectangle -> "Got a Rectangle",
    as :Circle    -> "Got a Circle",
    default       -> "Huh"??? 
  }
  #: If a Triangle object were defined, there
  #: would be no compiler error to indicate a
  #: change is needed.
}
```

vs

```
#: Assuming the variant definition

#define typeOf(:Shape) {
  match {
    as :Rectangle -> "Got a Rectangle",
    as :Circle    -> "Got a Circle",
  }
  #: No need for default case
  #: Adding a Triangle object to the variant
  #: will raise an exhausivity error, indicating
  #: changes are needed
}
```

# 17. Generics

Consider a `find` element that returns the first index of a certain `Number` in a list of `Number`s:

```
define find(haystack: Number+, needle: Number) {
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

This works fine. But what if you wanted `find` to work with `String+` and `String`? You'd need to add a `(String+, String)` overload:

```
define find(haystack: String+, needle: String){
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

Note that the entire definition is the same, except for the parameter types. Also note that this apporach to extending `find` would lead to an unruly number of lines of code.

Generic types act as a way to define an algorithm for "some type" to be specified later. Think of it like algebra but instead of substituting numbers, you substitute types.

Functions, element definitions, objects, traits, and variants can use generic types. The generic types that can be used by a generic-usable context typically come after the keyword:

```
fn[Types] (params) -> returns {}
define[Types] name(params) -> returns {}
object[Types] Name implements Traits {}
trait[Types] Name implements Traits {}
variant[Types] Name implements Traits {}
```

The `find` example from earlier would become:

```
define[T] find(haystack: T+, needle: T) {
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

While only the types have changed, this definition of find works for any type of list and compatible needle type.

## 17.1. Generics and List Types

The type represented by `T` will be one rank lower than the input type.

For example, given the following function:

```
$uniquify = fn[T] (list: T+) -> T+ {
  $seen = [] as T+
  $list foreach ($item) {
    if ($seen contains($item)) {
      $seen: append($item)
    }
  }
  $seen
}
```

If `uniquify` is passed `Number+`, then `T` will be `Number`. However, if it is passed `Number++`, then `T` will be `Number+`.

## 17.2. Indexed Generics

In the parameter list of a function, numbers can be used to specify taking a certain number of items from the stack. Under the hood, the popped items are automatically assigned generic types to allow for this generic behaviour. However, it may be desirable to explicitly reference the generic type of an automatically assigned generic. Therefore, `^n` will refer to the type of argument `n`. 

## 17.3. Other Notes

- There is no type erasure with generics. If something is passed an object with a generic, both object and generic types are available.
- For now, generics are invariant. This is to keep the initial design simple. Covariance and contravariance may be added at a later date.
- When they are added, `define [above T]` will be contravariance (any type above or equal to T) and `define [any T]` will be covariance (any type of T). 

# 18. The `where` clause

The `where` part of functions and element definitions allows for type constraints to be placed on input parameters. This is useful for cases like:

- Ensuring function arities are the same while supporting variable arities
- Specifying that a minimum rank list is `n` ranks lower than another minimum rank list
- Calculating return types based on numerical properties of inputs

If present, the `where` must come after the return list. Each condition is separated by a comma (`,`). All conditions must be true for the function to be called. 

For example:

```
define @stack ternary(
  condition: Number,
  onTrue: Function,
  onFalse: Function
) -> ($onTrue.out | $onFalse.out) where (
  $onTrue.arity $onFalse.arity ==,
  $onTrue.multy $onFalse.multy ==
) {
  [$onTrue, $onFalse]#[condition] call
}
```

In this example, the arity of `onTrue` and `onFalse` are guaranteed to be the same. This guarantee cannot be easily made with generics or other data types.

Constraints can also specify properties of types. For example:

```
define[T] reshape(
  xs: T~,
  shape: (Number...)
) -> T+$n where (
  $n = $shape length
) {
  #: reshape implementation here
}
```

In this example the return type, an exact-rank list, is set based upon how many arguments are in the `shape` argument. As a tuple will always have a fixed length at compile time, this constraint can be checked and utilised at compile time. These conditions will always return true.

Operations allowed in the `where` clause are:

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

## 18.1. Dynamic Types

In the above examples, there were some unusal return types:

- `$onTrue.out | $onFalse.out`
- `T+$n`

These types are dynamic in that they are not known when writing the types. They are in fact known at compile time.

`$` followed by a variable name and potentially a member access will make the variable value part of the type. The value must fit in the context of the type: `T+$true.out` would cause a compile error, because a function's outputs are not a number. `$n | $false.out` would cause a compile error, because a number is not a type.

## 18.2. A Note on Variadic  Tuples

In the `reshape` example, the `shape` parameter has type `(Number...)`. This accepts a tuple of any length to be passed to `shape`.

Generally speaking, `(T...)` is a tuple of any number of `T`s, and is called a 'varadaic tuple'.

A variadic  tuple will always contain a finite number of items, but that number will be unknown to most compile time contexts. The only exception is the `where` clause, which can determine properties like tuple length from the functions arguments. However, a `where` clause, when given a variadic tuple where a variadic tuple is expected, will not be able to determine the length of the tuple, and will return a compiler error.

# 19.  Annotations
## 19.1. `@recursive`

The `@recursive` annotation allows for easier recursion within a function. The `this` element will call the nearest scoped function with a `@recursive` annotation. For example, this is a recursive factorial program:

```
$factorial = fn @recursive (:Number) -> Number {
  match {
    exactly 0 -> 1,
    default   -> this(1 -) *
  }
}
```

This is a recursive fibonacci element:

```
define @recursive fib(:Number) -> Number {
  match {
    if [0 1] contains -> 1,
    default -> fork: decrement {2-}
               both: this()
               +
  }
}
```

Note that using `this` outside of a `@recursive` function/element is a compile error.

If you need to recurse to a function outside the current recursive scope, you'll need to capture it by quoting `this` and storing it in a variable:

```
fn @recursive (:Number) {
  $outer = 'this
  fn @recursive (:Number) {
    $outer()
  }
}
```

However, such recursion is usually an indicator that something has gone wrong.

## 19.2. `@stack`

Sometimes, an element cannot be expressed in terms of a function with fixed inputs and outputs. For example, higher-order functions requiring variadic stack manipulation are impossible to represent, with function overloads only able to cover a finite subset of use-cases.

Take for example the `dip` higher-order function. `dip` takes a function, stashes the top of the stack, performs that function, and then pushes the stashed top back to the stack.

Consider first an implementation of `dip` for monads:

```
define[T, U, V] dip(
  :T,
  top: V,
  fn: Function[T -> U]
) -> U, V {
  $fn() $top
}
```

This could be extended to dyads as:

```
define[T, U, V, W] dip(
  :T, :U,
  top: W,
  fn: Function[T, U -> V],
) -> V, W {
  $fn() $top
}
```

And triads as:

```
define[T, U, V, W, X] dip(
  :T, :U, :V,
  top: X,
  fn: Function[T, U, V-> W]  
) -> W, X {
  $fn() $top
}
```

Evidently, this pattern quickly grows unruly. Additionally, these definitions only work for input functions with multiplicity 1 - different multiplicities would require even more overloads.

One solution might be to use a `where` clause:

```
define[T] dip(
  args: $in,
  ignore: T,
  func: Function
) -> T, $func.out
) where (
  $in = $func.in
) {
  $top = \
  $func()
  $top \
}
```

But that's horribly verbose, and requires a lot of forethought, more so than explicit ceremony makes useful. 

To this end, elements can have a `@stack` annotation added to indicate that the element definition will operate on whatever is the stack when the element is called. For example, `dip` becomes:

```
define @stack dip(fn: Function) {
  $temp = ^
  $fn()
  $temp
}
```

When a stack element is called, the element code is type checked against the current stack state. In this way, stack elements are kind of like macros. However, variables defined within a stack element are local to that element, and do not persist after the element is finished.

Some important notes:

- Unlike normal functions and elements, `@stack` functions/elements do _not_ push named arguments to the stack. This design decision reduces the number of `pop`s needed in stack functions/elements.
- The return of a `@stack` function/element is the state of the stack.
- A `@stack` function/element is type-checked at call site, rather than at definition site.
- When an argument is a `Function`, it need not have its type parameters specified.

Some other examples of potential `@stack` elements include:

```
#:{
  x y both: F --> F(x) F(y)
}:#
define @stack both(fn: Function) {
  $temp = @tupled $fn() #: Store results of fn in tuple instead of pushing all to stack
  $fn() $temp detuple
}

#:{
  x y fork: F G --> F(...) G(...)
}:#
define @stack fork(f: Function, g: Function){
  $res1 = peek: @tupled $f()
  $res2 = @tupled $second()
  merge($res1, $res2)
  detuple
}

#:{
  x y correspond: F G --> F(x) G(y)
}:#
define correspond(f: Function, g: Function) {
  $temp = @tupled $f()
  @tupled $g()
  $temp \
  both: detuple
}
```

## 19.3. `@tupled`

In the `@stack` annotation examples, there was a new annotation: `@tupled`.

This annotation makes the next operation return its results in a tuple, rather than on the stack. This is primarily useful for operations that may return more than 1 value.

For example:

```
define foo() -> Number, Number {
  6 7
}

foo #: Just pushes 6 7 to the stack
@tupled foo #: Pushes (6, 7)
```

The neat thing is that the length of the tuple is known at compile time because it's just what would have been pushed to the stack, something which is _always_ known.

`@tupled` on an element that does not return anything pushes an empty tuple (`()`).

# 20. Modules

An important tenet of modern software engineering is code reuse. Write an element once, use it everywhere. Valiance's module system enables organising code across multiple files while maintaining clarity and type safety.

## 20.1. Basic Example

Consider a simple greeting module:

```valiance
#: in file "greetings.vlnc"

define greet(name: String) {
  println($"Hello, $name!")
}
```

To use this module in another file:

```valiance
#: in file "main.vlnc"

import greetings

greetings.greet("Joe") #: Prints "Hello, Joe!"
```

The module name is derived directly from the filename. The file `greetings.vlnc` becomes the module `greetings`.

## 20.2. Import Types

Valiance supports four distinct import styles, each serving different organisational needs.

### 20.2.1. Namespace Import

The most straightforward import style brings an entire module into scope. All items from the module must be accessed through the module's namespace:

```valiance
import collections

collections.Stack()
collections.HashMap()
collections.find([1, 2, 3], 2)
```

This approach keeps the origin of each element clear and avoids naming conflicts.

**Note:** If `find` were a `Stack`-friendly element (defined within the `Stack` object's scope), it would be available without the namespace prefix after importing. Object-friendly elements automatically follow their objects into scope. See section 20.4 for details.

### 20.2.2. Aliased Namespace Import

When a module name is long or conflicts with existing names, an alias provides a shorter reference:

```valiance
import andesite as ands

ands.Router()
ands.serve(8080)
```

The alias replaces the module name entirely — the original name becomes unavailable.

### 20.2.3. Specific Import

For frequently-used elements, specific imports eliminate the need for namespace prefixes:

```valiance
import collections: Stack, find, contains

Stack()                           #: No prefix needed
find([1, 2, 3], 2)               #: No prefix needed
collections.other()              #: Other items still namespaced
```

Multiple items can be imported by separating them with commas. Items not listed in the import must still use the namespace prefix.

### 20.2.4. Parsed Import

_This feature will be a long-term goal. It needs more planning and idea-testing. It's listed here for completness and conceptual brainstorming._

Valiance extends imports beyond `.vlnc` files through parsed imports. A parsed import statically loads and transforms a file at compile time using a specified parser module:

```valiance
import "config.json" as Config using json
import "words.txt" as WORDS using files.textlines
import "layout.gnite" as layout using granite
```

The `using` clause specifies a module that implements the parsing logic. The parser transforms the file's contents into typed Valiance values during compilation, providing full type safety without runtime parsing overhead.

For example, `using json` might transform a JSON file into a `Dictionary`, while `using files.textlines` reads a text file as `String+`. The exact type depends on the parser's implementation.

Parsed imports enable embedding configuration, data, and even domain-specific languages directly into Valiance programs with compile-time validation.

## 20.3. Import Syntax

The formal syntax for imports is:

```ebnf
ImportStatement = "import" (ModuleImport | ParserImport)
ModuleImport = Name [("as" Name) | (":" Name {COMMA Name})]
ParserImport = StringLiteral "as" Name "using" Name
```

Import statements occupy a single line and must appear before any other code in the file.

Examples:

```valiance
import random
import andesite as ands
import collections: Stack, find
import json
import "config.json" as Config using json
import "data.csv" as DATA using csv.parse
```

## 20.4. Object Imports and Automatic Element Inclusion

When importing an object, all object-friendly elements (those defined within the object's scope) are automatically included in the importing file's overload table. This happens regardless of import style — namespace, aliased, or specific imports all trigger this behavior.

```valiance
import collections

collections.Stack()      #: Constructor needs namespace
$stack = collections.Stack()
push($stack, 5)         #: Object-friendly element - no namespace!
pop($stack)             #: Also no namespace needed

collections.find([1, 2, 3], 2)  #: Not Stack-friendly, needs namespace
```

The key distinction: object-friendly elements are those defined *within* the object's definition block. Regular module elements remain namespaced.

```valiance
#: In collections.vlnc
object Stack {
  define push(s: Stack, item: T) { ... }  #: Object-friendly
  define pop(s: Stack) { ... }            #: Object-friendly
}

define find(list: T+, item: T) { ... }    #: Not object-friendly, just in module
```

This behavior keeps object methods and the objects themselves conceptually unified. There's no need to separately import each method — they follow the object naturally, while unrelated module elements stay namespaced.

## 20.5. Restrictions

**Circular Imports:** Valiance does not support circular imports. If module A imports module B, module B cannot import module A. This restriction encourages better module design and clearer dependency hierarchies.

**No Wildcard Imports:** Valiance intentionally omits an "import all" feature. Every import must be explicit — either through namespace imports or specific element lists. This prevents namespace pollution and keeps dependencies clear.

**Module Names from Filenames:** A module's name is always its filename (without the `.vlnc` extension). There is no mechanism to override this within the file. To change a module name, rename the file. This constraint ensures file structure and import statements stay synchronized.

## 20.6. Practical Guidelines

When organising a project:
- Use namespace imports by default to keep origins clear
- Use specific imports for frequently-used utilities
- Use aliased imports when module names are unwieldy
- Use parsed imports for embedding configuration and data files
- Structure directories to reflect logical module groupings

For example, a project might have:
```
src/
  main.vlnc
  utils/
    math.vlnc
    string.vlnc
  data/
    models.vlnc
  config.json
```

And `main.vlnc` might import:
```valiance
import utils.math: sin, cos
import utils.string as str
import data.models
import "config.json" as Config using json
```

The module system balances explicitness with convenience, ensuring that code reuse never comes at the cost of clarity.

# 21. Named Dimensions

_For justification of why this exists, https://nlp.seas.harvard.edu/NamedTensor.html and https://math.tali.link/rainbow-array-algebra/ serve as good reading. After all, the ideas presented in both are the foundation for this concept_

_Also, this will probably be implemented a long way down the line. It'll need a lot of refinement. It's presented here to give an idea of direction._

When working with multidimensional data — images, time series, or higher-rank arrays — it’s helpful to label each dimension by name.

Valiance lets you do this with named dimensions.

## 21.1. Syntax

You can give names to dimensions using this type syntax:

```
T@[dimension]
T@[dimension: [subcomponent1, subcomponent2]]
```

For example:

```
Number@[x, y]
```

Creates a rank-2 list with dimensions `x` and `y`.

You can type-cast to named dimensions:

```
random.sample(size = (3, 100, 100))
$image = ^ as Number@[channel: [R, G, B], height, width]
```

## 21.2. Destructured Dimensions

You can destructure a dimension to give names to its parts:

```
fn (image: Number@[channel: [R, G, B], width, height]) {
}
```

Here:

- `channel` is a dimension of size 3
- The parts of channel are named R, G, B

Now you can refer to these parts by name in your code:

```
$R  #: equivalent to $image.channel.R
$G
$B
```

Accessing a dimension will push a reference to that dimension.

## 21.3. Working with Dimensions

Named dimensions are first-class properties of the value — you can access them:

```
$image.channel
$image.width
```

You can also perform dimension-aware operations:

```
import dimensions

fn (image: Number@[channel: [R, G, B], width, height]) {
  $image dimensions.over: {$image.channel} {max}
  #: returns a [width, height] list of max value per channel
}
```

Or:

```
import dimensions

fn (data: Number@[location, time]) {
  $data dimensions.over: {$data.time} {avg}
  #: returns average per location
}
```

## 21.4.  Rank and Compatibility

Using named dimensions is equivalent to specifying an exact rank:

```
Number@[x, y]
```

is exactly like `Number++`.

If you pass a higher-rank array, the function will vectorize over the extra dimensions.

When passing an a value with already named dimensions to a function specifying dimension names, it will match the dimensions by structure.

```
import dimensions

#: Imagine there's something pushing data to the stack here
$image = ^ as Number@[ch: [R, G, B], h, w]

define grayscale(img: Number@[channel: [R, G, B], height, width]) -> Number@[height, width] {
  dimensions.over($channel): {
    [0.2989, 0.5870, 0.1140] dotProduct
  }
}

grayscale($image) #: channel = ch, height = h, width = w
```

# 22. Conclusion

Valiance, as outlined in this language overview, shows how array languages can be presented as mainstream software. By striving to look like normal every-day production code, Valiance positions itself for integration into codebases of all kinds.

While this overview is not complete - sections need to be exapnded, the grammar needs to be formalised, and the implementation details are non-existant - it gives a pretty good insight into the design direction and planned features of Valiance.

Some day soon, this document will need to be rewritten to account for the finished state of the language. See you then :)

# Appendix A. Epilogue - Design Philosophy

_But wait...there's more!_

As mentioned in the introduction, the fundamental tenet of Valiance is that it should be a tool of *doing* rather than a tool of *thought*.

A long time ago, a man named Kenneth Iverson laid the foundations for modern-day array programming. Seeing that programming languages of his time were "decidedly inferior" to mathematical notation in providing clarity of thought, he devised a new programming notation. A programming notation that encompassed the expressiveness and economy of mathematics while still serving as an unambiguous and precise means of computing.

Thus, array programming, and APL were created. The primary idea was to forgo the ceremony of programming boilerplate in favour of expressing programs in their rawest form - as if they were mathematical formulas. Where a conventional programming language might take ~6-7 _lines_ of code to express a function, APL could do it in ~6-7 _characters_ of code. 

This new style of programming allowed thoughts to be expressed without the fuss of pleasing language compilers and interpreters with needless syntax constructs. The ability to communicate complex concepts in an ultra-minimalistic manner was revolutionary.

Yet this revolution never seeped into mainstream software development. Certainly, it found an outlet in array programming libraries like NumPy and programming languags with excellent array support like Julia. But the world is not using dedicated array languages for critical software applications.

Iverson's vision succeeded brilliantly at its intended purpose: making computational thinking clearer and more concise. But it prioritised exploration over execution, elegance over engineering. Array languages became temples of thought rather than tools of work.

Indeed, what Iverson — and much of academia — overlooked is that software isn’t just _programs_. It’s systems, users, integrations, and change. It lives in deployment pipelines and user interfaces, not just in proofs and REPLs. Mathematicians and computer scientists may have treated programs as abstract artefacts of reasoning; the rest of us have to ship them, maintain them, and share them with other software developers. Realisitically, software requires more than the thought of a program — it requires a notation that supports _doing_.

That's where Valiance steps in. It relaxes some of the thought-centric language design features of traditional array languages and reintroduces mainstream programming constructs familiar to the average software developer.

## A.1. Specific Design Rationales

### A.1.1. Words Instead of Glyphs

A common outsider critique of array languages is that they are "line noise" languages, write-only and terribly unreadable. One look at a typical array language program should reveal from where this complaint stems: the multitude of squiggles and glyphs comprising the primitives of the language. It would not be unreasonable for, say, an APL program to be mistaken for a malformed hex dump. 

Of course, as any array language user will correctly tell you, this critique is completely ignorant of the fact that readability is fully subjective. Over time, the random squiggles become just as meaningful as words. 

Yet dismissing such critiques as wholly ignorant is itself an act of ignorance. While they may be based in a refusal to explore new concepts at a greater depth, syntax based exclusively on glyphs (the non-word kind) isn't necessarily a good thing. 

For example, almost any software engineer who's ever studied the tenets of maintainability knows that single-letter variable names are a major code smell. The moment the context of each variable is forgotten, understanding the true meaning of a greater program becomes a time-sinking puzzle. 

Admittedly, primitives have an automatic external context rarely granted to variables. There is a single unified reference for what each glyph means, reducing the amount of time needed to figure out what each symbol does. But why make things more difficult than they need to be. Sacrificing total brevity for a little more readability isn't a totally bad thing. 

### A.1.2. List Model Instead of Rectangular Array Model 

I'm not going to sugarcoat the real reason Valiance uses a list model: lists are easy.

Easy to work with, easy to conceptualise, and easy for people coming from mainstream programming languages.

Fun fact: a large fraction of developers report using JavaScript, which defaults to lists. While not perfectly representative of all developers, it’s a strong indicator that lists are familiar to many programmers

People know lists. People know the fundamentals of append, remove, and index. That's it. There's no worrying about a mapped operation returning arrays of different lengths, no need to have weird overlap between true rectangular arrays and rugged arrays, and no need to be concerned about the otherwise hidden shape-type system.

That last point is an interesting one. What a lot of people probably don't realise is that array shape is a (commonly de facto) type system. Much like a type system, operations error if the input shapes are not compatible. And like a normal type system, static annotations greatly increases software quality by decreasing the chances for unexpected type bugs, and by increasing the maintainability of the software.

However, shape is hard to statically annotate - dynamic shape is immensely useful but impossible to specify at compile time. Languages like Futhark, Remora, and Dex all focus on shape as a compile-time type, but they all decrease the ease of writing versatile functions.

A list model avoids the shape problem by just, well, _not_ having shape. Lists don't care if all items have different lengths. They only care about rank. 

And in a way, that's more array-programming-esque than arrays. The major draw of array programming is its heavy emphasis on rank-polymorphism. With arrays, one has to juggle both rank and shape, detracting from a rank-only experience. Lists inherently simplify the whole process.

Need I _list_ any more reasons why Valiance is a list-model language?

# Appendix B - Reserved Keywords 

```
above
any
as
at
call
define
fn
foreach
if
implements
import
match
object
private
public
readable
self
this
trait
variant
where
while
spawn
async
await
parallel
concurrent
```

Note: the last 5 are reserved for any potential future threading or concurrent features. They do not have any active design plans yet. 