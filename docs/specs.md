# Valiance Language Specification

## 1. Introduction

### Purpose

Valiance exists to provide an array programming language that bridges the gap between
traditional mainstream programming languages and the power of traditional array
languages.

Sometimes, the intersection of two products can lead to a product that has a
confusing identity (e.g. tablets in the age of laptops and smartphones). However,
there are other times when the intersection is a design space that for some
reason hasn't been explored.

Mainstream languages don't have the same powerful expressiveness that array
languages do.

Array languages often sacrifice otherwise universal programming concepts and
programmer conveniences for the sake of mathematical purity.

Therefore, the purpose of Valiance is to take advantage of the immense
power of array language, while not cheaping out on mainstream appeal.

### Guiding Principles

- **Mainstream appeal:** Valiance should pass for a mainstream language at first glance. Even if this means introducing "non-tacit" features.
- **Simplicity over Mathematical Rigidity:** While some array language features make mathematical sense, and can lead to some optimisations/elegant solutions, accessibility is more important. It's like that one "I just want to grill" meme.

![](https://i.kym-cdn.com/photos/images/newsfeed/001/556/116/4fb.png "Rectilinear arrays? I just want to list for goodness sake!")

- **Stack based:** Stacks are beautiful things. I've been using them for years now and I wouldn't reccomend any other data structure for an array language.
- **Readability:** Words over symbols. Combinations of functions that can read as a sentence. Humans are coding, not the machines.
- **Relative Simplicity:** (This is different to the earlier point on simplicity) The language should be simple in that the number of language concepts should be kept to a minimum. You could also call this modularity.
- **Flexibility:** Users should be able to express their solutions in the way they want. They shouldn't have to conform to some pre-determined way of thinking forced upon them by the language designer.

### Important Terms

- **Element**: A built-in function. It's what you might call a "primitive".

## 2. Syntax & Semantics

### 2.1 Variables, Types, and Objects

#### Variables

```valiance
5 ::= x ## Sets x to 5
10 ::= y ## Sets y to 10
$x $y + ## Adds x and y together

"Howdy" ::= greeting: String? ## Marks greeting as being an optional String
None ::= greeting ## Sets greeting to None, allowed because it's being assigned to a known optional
None ::= var ## Type error. What option is var?
56 ::= greeting ## Type error.
```

- Types of variables are inferred at assignment. If it can't be inferred, the type will need to be specified.
- Only local variables are allowed. There is no way to define a global variable.
- Variables are local to the scope in which they are defined. This means that if a variable is defined in a function, it cannot be accessed outside of that function.
- Variables from outer scopes can be read from inner scopes, but not written to.

#### Types

- Valiance is a statically typed language.
- Predefined types include:
  - `Number` (integers, floats, and complex numbers)
  - `String`
  - `Tuple`
  - `Function`
- Note that there is no `List` type. This is because list types are represented as an operation on a type.
- A list of type `T` is represented as `T+`. `T+` means that all items in the list are `T`. No nesting happening.
- This extends to multidimensional lists. `T++` is a list of lists of `T`. `T+++` is a list of lists of lists of `T`, and so on.
- This can be shortened to `T+n` where `n` is the number of dimensions (or rank of the list).
- A non-list type is called an "atomic type".
- However, lists may contain a blend of lists and atomic values. No number of `+`s can be used to represent this.
- Therefore, `T~` is used to indicate that a list has at least rank 1. It may be deeper, but you know for a fact that every item in the list is at least atomic `T`.
- Like `T+`, `T~` can be extended. `T~~` is at least a list of lists of `T`, and so on.
- `T~n` is used to indicate that the list is at least rank `n` (or has a minimum depth of `n`).
- `T+n` can always be considered `T~m` where `n <= m`. `T~n` can never be considered `T+m` for any `m`; it is unsafe to treat `T~` as `T+`, because it may be deeper than `T+`.
- Essentially, `T+` is exact rank, while `T~` is approximate rank.
- `T~` is also used in cases where the rank of a list can't be determined at compile time.

- There are other type operations:
  - `T?` means that a value is either `T` or `None`.
  - `T!` means that a value is guaranteed to be atomic `T`, not a list of any rank. This is useful for vectorisation as will be shown later.
  - `T/U` means that a value is either `T` or `U`. `/` is used instead of `|` because it's easier to parse.
  - `T&U` means that a value is both `T` and `U`. Realistically speaking, at least one of `T` and `U` will be a trait type, because something can't be two concrete types at once.

#### Objects

<!--Straight up ooping it-->
<!--Finna oop it-->
<!--My apologies.-->

- Objects in Valiance are more like records than classes as they can only have members.
- However, they can define extensions for elements, which effectively adds overloads to the element.
- Additionally, they can implement traits, which specify a set of members and extensions that the object must implement.
- Further, they can have generic types associated with the object.

- Objects can have either "readable" or "private" members. Readable members are publicly readable members that cannot be written to outside of the object. Think of them as members with automatically defined getters. Private members are the same as they are in traditional OOP.
- Extenions can either be object-bound or object-friendly.
- An object-bound extension is one that modifies the object itself and returns the modified object. It cannot return anything else other than the modified object. It also does not change an object in-place.
- In contrast, an object-friendly extension is one that _can_ modify an object in place, but only if it is stored in a variable. This is to provide a way for an extension to return an arbitrary value while still being able to modify an object.
- Object-bound and object-friendly extensions can write to readable members, and the only place where private members can be used at all.
- The body of an object definition acts as the constructor for the object.
- The constructor is called when the object is created, and takes its arguments from the stack.


##### Object Syntax

Note that this relies on syntax that will be defined later in this document.

```valiance
#object Name: {(constructor args) => 
    ::=readableMember
    ::=.privateMember

    #define .extensionName: {(args) => ... } ## Object-bound extension. Implicitly returns the object.
    #define otherExtension: {(args) => ... } ## Object-friendly extension. Can return anything.
}

#define someExtension: {(arg: Name) => ...} ## Extension that takes the object
                                            ## but can only read its readable members.


## An object with a generic type
#object ObjectWithGenerics[T]: {(args) => ...}

## An object implementing traits
#object ObjectImplementingTrait implements [Trait1]: {(args) => ...}

## Multiple traits can be implemented at once
#object ObjectImplementingTraits implements [Trait1, Trait2]: {(args) => ...}

## An object with a generic type and implementing traits
#object FullKitAndKaboodle[T] implements [Trait1]: {(args) => ...}
```

To create an object:

```valiance
$Name !() ## $Name pushes an instance of the object's constructor to the stack. !() calls it
`Name`    ## Syntax sugar for the above.
```

As you will see, this is the same syntax as calling a function.

### 2.2 Functions

- Functions are first-class citizens in Valiance. This means that they can exist on the stack, be passed to other functions, and be returned from functions.
- They have a fixed arity (number of inputs), and a fixed multiplicity (number of outputs).
- Functions on their own can't be overloaded, per se. However, function overloads can be simulated by putting multiple functions into a tuple and then using `call` on the tuple. It'll pick the best match for the arguments on the stack. Note that this requires all functions to have the same arity (although multiplicity can be different).
- There are no "named functions" - all functions are anonymous. However, they can be assigned to variables, which can be used to simulate named functions.

#### Function Syntax

```valiance
{(args) -> (returns) => ... }
```

- `args` is a list of arguments, separated by commas. Each argument can be:
  - A number, representing how many values to pop from the stack, or
  - A variable name, representing a single value to pop from the stack into that variable, or
  - A colon followed by a type, representing a type that the top of the stack must be, or
  - A variable name and a type, combining the two above.
- If a number or typeless variable name is used, the type(s) of the popped value(s) will be given implicit generics for type checking. This means that there will need to be some level of pattern matching in the function body.
- `returns` is a list of return values, separated by commas. Similar to `args`, each return value can be:
  - A number, representing how many values to push onto the stack, or
  - A type name.
- In both cases, arguments/returns can be a mix of any of the above.
- A number argument will automatically push its values onto the function's stack. As will a type argument.
- A variable argument will not push its value to the stack.
- A type argument can be followed by a `{n}` to represent popping `n` values of that type from the stack. This is useful for shortening things like `T, T, T` to `T{3}`. Note that `T{n}` is not a type.
- The `returns` section can be omitted to have the return type inferred. The inferred type will be whatever is on the top of the stack at the end of teh function. Note that doing this will set the number of items returned to 1.
- `args` and `returns` can be empty, indicating that the function takes no arguments and returns nothing, respectively. However, the braces must still be present, as must any arrows.
  - One might think `{...}` would imply arity=0 and multiplicity=0. However, as will be shown later, this makes the function infer its arguments to its best ability, and infer the return type from that.  
- If a function encounters a stack underflow, it will recycle its arguments, starting from the first argument.
Examples:

```valiance
{(:Number{2}) -> (Number) => +} ## Adds two numbers and returns a number.
{(:Number, :Number) -> (Number) => +} ## Same as above, but with explicit types.
{(:Number) => 2 *} ## Multiply a number by 2. Return inferred to be a number.
{(x: Number, y: Number) -> (Number, Number) => $x $y} ## Least useful identity function. 
{(:Number) => +} ## Adds a number to itself by recycling it once.
```

**TODOS:**

1. Document arity-dependent functions - functions allowed to calculate their arity based on function-type arguments. Useful for modifiers that need to take arguments based on the arity of an input function.
2. Document function generics.
3. Document how implicit generics work and are referenced.
4. Document how a function can infer its arguments if no arguments are specified. (Also, solidify the process on how this will happen.)

### 2.3 Control Flow

- **Conditionals:** `[Syntax Example]`
- **Loops & Iteration:** `[Syntax Example]`
- **Pattern Matching:** [If applicable]

### 2.4 Memory & Performance

- **Memory Model:** [Garbage Collection, Manual, Reference Counting?]
- **Performance Considerations:** [Optimizations, Compile-time checks]

### 2.5 Concurrency

- **Concurrency Model:** [Threads, Async/Await, Actors, CSP]
- **Example Usage:** `[Concurrency Example]`

---

## 3. Execution Model

- **Interpreted or Compiled?** [Just-in-time, ahead-of-time, bytecode?]
- **Compilation Targets:** [What platforms does it support?]

---

## 4. Standard Library

[List core features like I/O, networking, collections, etc.]

---

## 5. Error Handling & Debugging

- **Error Handling Model:** [Exceptions, Result Types, Error Codes?]
- **Debugging Support:** [Stack traces, Logging, Debugger Tools]

---

## 6. Example Programs

### Hello, World

```
[Example Code Here]
```

### Fibonacci Function

```
[Example Code Here]
```

### OOP Example

```

```

---

## 7. Future Considerations

- [Possible features to add in future versions]
- [Things still undecided]

---

### Notes

[Anything else that doesn’t fit above]
