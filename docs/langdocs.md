_Note, this is NOT a tutorial, nor a presentation of any language design philosophy. If you want that, check out the (outdated) overview.md document._

This is a document outlining the key features of the Valiance programming language as a series of dot points, brief explanations, and code examples. It is not intended as a teaching resource, but rather an easy-to-write way of documenting language features.

By the way, `${...}` in an example means "not actually part of the syntax, but to be replaced"

# 0. Overarching Design Directions

- Array programming language
	- List model rather than rectangular array model
	- Iversonian-style, rather than language with good array support.
 - Stack-based
	 - Unashamedly so, although with some mitigations to make the stack experience easier. Yes, stacks can be hard to learn, but they are hardly the enemy if they are designed ergonomically.
  - Statically typed.
	  - But flexible with type inference and carefully constructed end-user facing conveniences.
- Design for usage within large-scale codebases
	- Code that can be read from 10ft away (metaphorically of course).
	- Suitable for sharing with team members.
	- Writeable in such a way that coming back to it 6 months later isn't a challenge.
 - Practical over elegant
	 - Elegance isn't fully mutually exclusive with practicality, but it shouldn't get in the way of people wanting something that just works
- Object-oriented by design
	- No inheritance though - only composition and traits
	- Intentional OO rather than an afterthought, or rather than something designed to not give the OO experience of other big languages.
- Functional programming
	- First class functions, and first-class functions that are actually ergonomic to work with.
- Memory safe without garbage collection nor manual memory management.
	- While this sounds pretentious at first, there's some language restrictions that makes this easier than it sounds.
- Extensibility and modularity
	- The ability to add function overloads, and even multiple dispatch.
- Built-in concurrency features, in the form of coroutines
	- No async/await
	- Concurrency intentionally designed,rather than tacked on afterwards.
- Expressiveness and conceptual brevity without needing symbol soup.
- Modern error handling/optional type handling.
- Everything immutable by default. Even lists.
- Performance
	- At this stage, left as an exercise for people interested in implementing language optimisations.
- Tooling
	- Good tooling is very important, but at this stage, given the language is still in planning, and that no one is even able to use it yet, tooling is left as an exercise for the community. One day though. Again, tooling = very important.
- Lazy Evaluation by Default
  - This one is more a nicety, as lazy evaluation for everything isn't strictly necessary (although, it is needed for infinite lists). However, making everything lazy with an opt-in system for forcing eager evaluation provides a nice balance of composability and practicality. 

# 1. The Stack

- Unbounded stack length (as much as the computer can handle)
- Can have mixed types.
- Stack underflow is a compile error - stack size and contents known at all times.
	- Well, the types of its contents. Not the exact values at compile time - obviously.
 - Programs all execute on a single top-level stack.
	 - Functions can create their own stacks, but control-flow always returns to the top-level stack.
  
# 2. Comments

- Single line comment = `#?` to newline
- Multiline comment = `#{` until `}#`

# 3. Literals and Fundamental Data Types
## 3.1. Numbers
- Unlimited size, unlimited precision.
	- As much as the computer can handle of course
	- Exact numbers. No `0.1 + 0.2 != 0.3` shenanigans.
	- Able to store multiples of Pi, e, surds, etc.
- Imaginary parts supported too.
- Can also have `${x}e{$y}` for `x * 10 ** y`
- One single number type - `Number`.
	- Can be pattern matched for more specific traits, but stored as just `Number`.
- Some example numbers:

```
69
420.69
69.0
-69
-420.69
-69.0
69i420
-69i-420
-420.69i-69
6e7
```
 
## 3.2. Strings

- Objects, not lists of characters
	- More convenient for string-focused operations
	- No weird indexing problems arising from treating strings as a list of characters
	- No concern about string shape either.
- UTF-8 encoded
- Support for string interpolation
  - `$` followed by either an identifier or `{expression}` inside a double-quoted string replaces that part of the string with the string representation of the value.
  - Example:

```
$brainrot = "6 7"
"The 2025 word of the year was $brainrot"
```

- Double quotes - `"Hello, World!"`
- Can contain literal newlines = no need for `\n`. Only quotes and backslashes need to be escaped.
- Unterminated string = lexer error.
- Type = `String`

## 3.3. Tuples

- Fixed length collections.
- Data need not be of the same type.
- Can contain other tuples.
- Finite length, known at compile time.
- Type expressed as `(${types})`
- Example tuples:

```
(1, 2, 3) #? (Number, Number, Number)
("Hello", 5) #? (String, Number)
```

### 3.3.1. Variadic Tuple Types

- Sometimes, it's useful to accept an arbitrary length tuple as a parameter.
- `(${type}...)` will accept any tuple with that type repeated 1 or more times.
- Can have multiple patterns.
- Some examples:

```
(Number) -> A tuple of 1 Number
(Number...) -> A tuple of 1 or more Numbers
(Number..., String) -> A tuple of 1 or more Numbers, followed by a String
(Number..., Number) -> A tuple of at least 2 Numbers (one or more Numbers, followed by a guaranteed Number).
(Number..., String...) -> A tuple of 1 or more Numbers, followed by 1 or more Strings
```

## 3.4. Dictionaries

  - Stores of `key->value` pairs.
  - Items can be retrieved, if they are in the dictionary, by indexing by key.
  - Basically hashmaps.
  - Keys can be any value though.
 - Type = `Dictionary[<KeyType> -> <ValueType>]`
- Syntax = `[key = value]`

## 3.5. None
- A value representing the absence of any other values.
- Always has the type `None`
- Can be used where an optional type is expected.

# 4. Lists

- Core data type
	- Especially given this is an array programming language.
- "But lists aren't arrays!"
	- They can generally do everything an array can do
- "That's not true, arrays have shape and rank"
	- Yes, they can't express shape, but they sure can express rank.
	- The usage of generics to represent lists already provides a neat way to express rank.
		- Number of `List<...>` wrapping before first non `List<...>` type encountered.
		- `List<List<Int>>` - rank 2 list
		- `List<List<Int>|Int` - rank 1 list
	- "But arrays are richer than lists. You can express a 0-size dimension that isn't at the end of the shape"
		- That's correct, yes. It is true that lists can't 100% emulate arrays in terms of mathematical structure. But I raise this counterpoint: where arrays are more rich, lists are more ergonomic.
	    	- Ruggedness is natural to represent as a list. No need for boxes, dual representations of data structures, nor weird nestedness. Everything is unified under the one data structure in the same way.
			- The familiarity with lists to users of other programming languages is unparalleled. The major mainstream languages of our time all use lists or non-rectangular data structures.
			- The lack of shape removes a major source of implicit mental complexity. Very rarely is shape explicitly specified in array programming languages (outside of futhark or remora). Without shape, there's one less aspect to manage. 
- "But but arrays good lists bad! You can't have an array language with lists! They're unelegant! They're not rectangular! You lose shape guarantees!"
	- Thank you, "random" array enthusiast, but those claims are either baggage from a blind adherence to the dogma of Iversonian array programming, or ignorant of the fact that rectangularity can be tracked at runtime. Yes, it may be slightly slower, but it's still possible. Go back to your precious APL if this bothers you.
- With the common objections out of the way, lists are homogenous, arbitrary (and potentially infinite) length collections of data.
	- But do note that `[1, 2, "3"]` is a completely valid list. Even though the individual item types are different, it is a homogenous list of `Number|String`. Union types to the rescue!
- The type representation of lists will be outlined in the section on types, because there's a few different ways of typing a list.
- `[]` syntax btw. Comma separated items.
- List items will pop from the stack if there are any stack underflows
	- `[1 +, 2 +]` will be a list of `[top of stack + 1, second item on stack + 2]`
- An empty list must be accompanied by a type cast to specify what type of list it is.
  - No `Any` type, so list base type must be specified. Compile error to not do so. 

# 5. Types

- Every stack item in Valiance has a type.
- Some types have already been presented
	- `Number`
	- `String`
	- `Dictionary`
	- Tuple types

## 5.1. Type Operations

- Composition of types
- `T|U` = union type. Either type `T` or type `U`
- `T&U` = intersection type. Something that is both type `T` *and* type `U`. One or both of `T` or `U` are going to be traits.
- `T?` = optional `T`. Effectively equal to `T|None`.
- `T!` = `T` that *cannot* be used as a vectorisation target. This will be explained later, but basically, it's a way of saying "this cannot be used as an overload" during overload resolution if a list is present where `T!` is expected.
- `T_` = The absolute base type of a list. This is mostly for generics unification purposes, and when you want to extract the base type of a list.

## 5.2. List Types

- Traditionally, lists are expressed as a composition of generics.
	- `List<Int>` or `List<List<String>>`
- In Valiance, given the fundamentalness of lists, a list type is expressed as a function of the "base" type of the list
- A list is a type, followed by the rank of the list.
	- This makes the list type a baked-in feature, rather than an otherwise after-thought construct.
- `+` after a type represents 1 level of rank
	- `Number+` is a rank-1 (flat) list of `Number`s.
	- `Number++` is a rank-2 (list of lists) list of `Number`s
	- `Number+++` is a rank-3 (list of lists of lists) list of `Number`s.
	- This pattern gets unruly quick, so `Type+n`, where `n` is a positive non-0 integer, is the rank.
		- `Number+3` == `Number+++`
- Notably, `+` is the _exact_ rank of the list.
	- Sometimes, the exact rank of a list is unknowable at compile time.
	- However, a _minimum_ rank can be known at runtime. You can safely say "I don't know exactly what rank this is, but I know for a fact it's a list of at least a certain rank. May be more, but that's okay"
- `*` after a type represents 1 level of minimum rank.
	- `Number*` has a minimum rank of 1. It may end up being a `Number+5` at runtime, but `5 > 1`, so that's okay.
	- `Number**` has a minimum rank of 2. It will never be a `Number+` at runtime, because `1 < 2`
	- `Number*n`, where `n` is a positive non-0 integer, has a minimum rank of `n`. Like the exact rank type, `Number*3` == `Number***`
- A list with exact rank `n` can be passed where a list with minimum rank `m` is expected if `n >= m`.
	- The opposite (passing minimum rank `m` where exact rank `n` is expected) is only true IF `m > n` AND the exact rank argument is not modified with `!`.
- Notably, `+` and `*` both imply a homogenous structure.
	- A list can have any structure it wants at runtime, but it'll always be expressed as some ranked-list of either a single base type or a union type.
	- This is inconvenient for wildly ragged lists.
		- `[1, [[2, 3], 4], [[[5]]]` can be expressed as an exact rank type, but it's going to be annoying to type.
- `~` after a type represents 1 level of minimum rugged rank
	- "Rugged rank? What's that"
	- It's basically saying "It's a list. It's completely arbitrarily recursive. We have no idea where it ends, but we do know that it's at least _a list_,"
	- Rugged rank only exists as a compile-time construct.
		- `[1, [[2, 3], 4], [[[5]]]` at runtime is always `{Number|{Number+|Number}+|Number+++}+`, but can be considered `Number~` for type checking purposes.
- A list with exact rank `n` or minimum rank `m` can be passed where rugged rank `x` is expected, if `n >= x` (or `m >= x`).

## 5.3. Type Casting
- A stack item with type `X` can be treated as type `Y` if and only if `X` makes sense as `Y`.
	- That is, if `Y` is a trait implemented by `X` OR
	- If `X` is a list type that could be flattened to `Y` (e.g. a `{Number|Number+}+` could be a `Number++` if there's no `Number`s, only `Number+`s).
- Two types of type casting:
	- Safe - the conversion is checked at runtime. Only list casting will be checked - trait upcasting doesn't need to be checked.
	- Unsafe - the conversion is not checked at runtime. This also only really applies to list casting. This is good for performance, but be careful that it is actually treatable as the intended type.
- Safe = `as Type`
	- `[[1, 2, 3], [4, 5, 6]] as Number*`
	- `Circle as Shape` (assuming trait `Shape` and `Circle` implements `Shape`)
- Unsafe = `as! Type`
	- `[[1, 2, 3], [4, 5, 6]] as! Number*`
	- Unsafe cast that is otherwise safe is a compile error (don't use `as!` where it isn't needed.)
 
## 5.4. Truthiness Rules
- Couldn't think of where else to put this
- `Number`: 0 = false, anything else = true.
	- Typically though, conditionals should expect `#boolean Number`
- `String`: `""` = false, anything else = true
- `T+`: `[]` = false, anything else = true
- `Dictionary` = `[]` = false, anything else = true
- `Function` = Error. You should not be using function objects _as_ the thing to check. Call them first
- `None` = always false
- `T?` = None = false, present = true

# 6. Variables
- Stores of values. Useful for temporarily storing stack items without needing weird stack shuffling.
- Variable assignment:

```
$name = value
```

- Notes:
	- `name` has to be a valid identifier. Identifier is `(<any letter> | "_") {<any letter> | "_" | <any digit>}`.
		- Any letter here means any unicode character matching `\p{L}`.
		- Any digit here means any unicode character matching `\p{Nd}`
	- The `value` section runs until the next newline. Whatever is on the top of the stack at the end of the line will be used. The remaining stack items will be left on the stack.
		- Rule of thumb: don't be a dingus and push more new things in variable setting.
- Variables, once initalised, always have the same type. The type of a variable is inferred from the item assigned to the variable. To control the inferred type, use `as Type`.
- `value` can also compute stack items:

```
69
$nice = id #? Just capture top
6 7
$brainrot = + #? 6 + 7 = 13
```
  
- Variables are retrieved with `$name`. Note that this does not conflict with `$name =`, as it is the presence of `=` that triggers variable assignment.
- `$name = $name ${operation}` is an annoying pattern, so you can write: `$name: operation` for arbitrary augmented assignment.
	- Where some languages only define a small set of augmented assignment ops (like `+=`, `-=`, etc), Valiance allows any function.
	- Only the next element is used as the operation. To group multiple things, use `{}`
	- The result of augmented assignment must be type compatible with the variable.

```
$name: {1+} #? name += 1
1 $name: +  #? equivalent
```

- All variables are local. There are no global variables.
- Writing to a variable defined in an outer scope will "shadow" that variable

```
$myvar = 5
println($myvar) #? 5
fn {
  $myvar = 6
  println($myvar)
} call #? 6
println($myvar) #? 5
#? The function did not change the value of myvar
#? in the outer scope.
```

- Variables can also be declared as "constant". That means they cannot be written to again.

```
const $name = value
```

- Only change to variable assignment syntax is the `const`.

## 6.1. Setting Multiple Variables

- Like how Python allows `a, b, c = 1, 2, 3`, Valiance allows:

```
$(a, b, c) = 1 2 3
```

- `$(${names}) = ...` will pop as many values as there are names and then

# 7. Elements
- Elements are what Valiance calls "primitives"/"verbs"/"operators".
- Every element:
	- Takes 0 or more inputs from the stack
	- Performs an operation on those inputs
	- Pushes 0 or more outputs back to the stack
- Valiance comes with a vast set of "built-in" elements that do not need to be imported. For example:

```
+ (Number, Number) -> Number   | Addition
+ (String, String) -> String   | Concatenation
- (Number, Number) -> Number   | Subtraction
length [T](T+) -> Number       | Length
sum (Number+) -> Number        | Summate numeric list
/ (Number, Number) -> Number   | Division
/ [T](T+, Function[T, T -> T]) | Reduce list by function
wrap [T] (T) -> T+             | Put item in a list (like wrap in [])
```

- Note that the order stack items are passed to elements is reversed relative what is popped. That is, the top of the stack isn't always used as the "left most" argument. 
- Instead, look at the top (arity) items.
- The number of inputs an element uses is called its "arity"
- The number of items an element returns is called its "multiplicity".
- Elements have fixed arity and multiplicity.
	- That means an element will always pop the same number of items and push the same number of items.
	- This is cruical for making element overloads consistent
- The syntax for an element is:

```
Element := ElementFirstChar {ElementChar}
ElementFirstChar := <A-Z>|<a-z>|"-"|"+"|"*"|"%"|"!"|"?"|"="|"/"|"<"|">"
ElementChar := ElementFirstChar | <0-9>
```

- Examples:

```
6 7 + #? 13
[1, 2, 3] length #? 3
[1, 2, 3] fn {+} / #? 6
```

## 7.1. Element Overloads

- Elements can do multiple things based on the types of items on the stack.
	- Like how `+` can be "add 2 numbers" if given numbers, but also "concatenate two strings" if given strings.
- An element can have as many overloads as it likes.
	- However, just because it can, doesn't mean it necessarily _should_.
	- In practice, try to keep overloads as few as possible, and as related as possible (either consistency between overloads, or consistency with the meaning of a symbol).
	- For example, `/` is division because it's a commonly used symbol in mainstream programming languages. `/` is also reduce because it's commonly used in array programming languages.

## 7.2. Element Call Syntax (ECS)

- Elements can always be called as-is in a postfix manner.
- However, this isn't always the most readable thing
	- `"This is a long string of things" println` kind of starts to lose focus.
- This isn't a problem in mainstream programming languages where the majority of "things that do things" are functions. `()` usually wraps function arguments.
	- `println("This is a long string of things")`.
- However, as already stated, elements are _not_ functions.
	- BUT. That doesn't mean `()` can't be applied as a language design concept.
- Therefore, `()` with no spaces after an element allows for arguments to be listed in a more familiar way.
	- `elementName(args)`
	- Generally equivalent to `args elementName`

```
length([1, 2, 3]) #? 3
reduce([1, 2, 3], fn {+}) #? 6
+(6, 7) #? 13
#? The above is valid, but is goofy-ahh
```

- Note that not all arguments to an element have to be specified in ECS
	- Arguments in element call syntax are pushed to the stack left-to-right before the element is called

```
[1, 2, 3] reduce(fn {+})
#? Equivalent to
[1, 2, 3] fn {+} reduce
```

- `_` can be used in ECS to indicate the argument is not being filled right now.

```
5 2 -     #? 3
5 -(2)    #? Also 3
5 -(_, 2) #? Also also 3
5 -(2, _) #? -3
#? Equivalent to
2 5 -
```

- This is helpful for when you want to specify an argument in a position that is in the middle of the function call
- ECS arguments can also be named. Note that the name must correspond to the parameter name.
	- `name = ...`
	- No spaces between `=` needed
	- Very useful for optional arguments

```
"Hello World" split(on=" ")
#? Same as
"Hello World" split(" ")
#? Which is just
"Hello World" " " split
```

- ECS arguments can consume stack items as needed.
	- When an argument in () needs to pop from the stack, and multiple expressions are provided, those expressions partition the stack right-to-left: the rightmost expression pops its values from the top of the stack first, then the next expression pops from what remains, and so on. Each expression pops exactly as many values as it requires.

```
6 7 +(double, halve)
#? Same as
6 double 7 halve +
#? Equals
12 3.5 +
15.5
```

## 7.3. Overload Resolution and Disambiguation

- When picking an overload to execute, the "most specific" overload is chosen.
	- That is, the overload that has the most specific matches to the element arguments is chosen.
 
Consider:

```
F (Number) -> Number  #? Overload 1
F (Number|String) -> Number #? Overload 2
```

- If `F` is given `Number`, then overload 1 is chosen. Although both overloads match, the first is more specific, as `Number` is a narrower match than `Number|String`.
- Order of narrowness (or specificness):

```md
1. exact match
2. exact generic-equivalent match
3. optional substitution (T where T? expected)
4. vectorising match
5. intersection type match
6. trait implmentation match
7. rank match
8. union type match
```

- Note that tagged versions of matches take priority over untagged matches.
	- A tag match is narrower than an untagged value
 
- Overload X is more specific than overload Y if and only if:

```
For all parameter pairs (Px, Py) in zip(X.params, Y.params):
  specificity(Px) > specificity(Py) in the specificity chain

(All parameters must be strictly more specific)
```

- If multiple overloads are just as specific, that's a compile error
- Overloads can be disambiguated by specifying how to treat types.
  - `[]` before `()`

Say:

```
F Overload 1: (T) -> Number
F Overload 2: (U) -> Number
$n = Type X implements T and U
```

```
$n F #? Compile error: ambiguous whether overload 1 or 2 desired
$n F[T] #? Use overload 1
$n F[U] #? Use overload 2
```

# 8. Stack Shuffling

- Three key stack shuffling elements: `^` (`dup`), `\` (`swap`), and `_` (`pop`)
- `dup` pops the top of the stack and pushes two copies back

```
1 2 3 dup #? 1 2 3 3
```

- `swap` pops two items and pushes them back in the other order

```
1 2 3 swap #? 1 3 2
```

- `pop` discards the top of the stack

```
1 2 3 pop #? 1 2
```

- "So then if `dup`, `swap`, and `pop` exist, why have the symbol forms? Doesn't that conflict with your philosophy of not doing symbol soup?"
- The symbol versions have extended functionality not possible with normal elements.
	- On their own, `^`, `\` and `_` act as their word counterparts
	- But when given stack labels, they can do a lot more.
- Stack labels are in the form `[pre-state -> post-state]`
	- Pre-state is the stack state _before_ the operation.
	- Post-state is the the stack state _after_ the operation.
- Both states are represented as a comma-separated sequence of words (defined as sequences of lowercase and uppercase letters) and `_`s. For example:
	- `a, b, c`
	- `a, _, b`
- The state represents the top of the stack up until the left-most label
	- `a, b, c` represents the top 3 items
- A `_` label simply means "unnamed stack item"
- `^` when given stack labels copies the post-state items up to the top
	- `^[a, b, c -> b]` copies `b` to the top while leaving `a, b, c` in place.
- `\` when given stack labels moves the post-state items up to the top
	- Whereas `^` leaves the original items in place, `\` pops the original copy.
	- All named labels will be popped if they aren't included in the post-state. Use `_` to skip items that won't be moved.
- `_` when given stack labels pops all post-stack items. It's like `\` but without putting anything on the top
	- No post-state is given with `_`, only pre-state
- Note that with `^` and `\`, multiple copies of the same label can be in the post-state
	- `[a, b, c -> a, a, b, b, c, c]` is perfectly valid.
- Pre-state labels must be unique (aside from `_`s)
- Pre-state labels need not be in any order. I use ascending alphabet merely because I find it the clearest. You might use words like `top`, `under`, or any names you want.
- `^`, `\`, and `_` are generalisations of their word counterparts
	- `dup` =  `^[a -> a]` (or even `\[a -> a, a]` if you're feeling spicy)
	- `swap` = `\[a, b -> b, a]`
	- `pop` = `_[a]`
- Some examples:

```
#? `^` post-state need not be in the same order as pre-state
1 2 3 ^[a, _, b -> b, a] #? -> 1, 2, 3, 3, 1
#? Multiple copies of labels in post-state just fine
1 2 3 \[a, b, c -> c, b, a, a, b, c] #? -> 3, 2, 1, 1, 2, 3
#? Deep popping
1 2 3 4 _[a, b, _, _] #? -> 3, 4
```

## 8.1. Numbered Labels

- `_n` can be used in labels as a shorthand for `n` repeated `_`s. For example `\[a, _3 -> a]` == `\[a, _, _, _ -> a]`.

# 9. Functions

- Whereas elements are called immediately, functions can live on the stack and in variables without being called.
  - Functions are only executed when explicitly called
- Functions do not execute on the global stack. Instead, they each have their own internal "function stack"
	- The only interaction a function has with the global stack (or any outer stack for that matter) is when it pops its arguments.
- The structure of a function is:

```
fn[${generics}] (${params}) -> ${returns} {${code}}
```

- `generics` is any generic type variable that the function needs.
- `params` define the parameters of the function. They can be:
	- named and typed (`name: T`). This stores the parameter in a variable, and ensures that it is of type `T`.
	- named with no type (`name`). This will cause the parameter type to be inferred from its usage. If it is not used in the function body, then that's a compiler error.
	- typed with no name (`:T`). This is simply pushed to the function's stack without being stored in a variable.
- All function parameters, regardless of whether they are named, unnamed, typed, or untyped, are pushed to the function stack at the beginning of the function.
- `params` can be empty (i.e. `()`) to indicate that the function takes no parameters (has an arity of 0).
- `params` can also be omitted. In such a case, the input types will be inferred based on what is used in the function. Note that this may result in the function having multiple different overloads.
- `returns` define the output types of the function.
	- `returns` is 0 or more types, separated by a `,`.
	- No `:` prefix is needed, as it's obviously a types list.
- `returns` can be empty to indicate that nothing is returned (has a multiplicity of 0). Note that the `->` needs to be present to indicate no return.
- `returns` can also be omitted. In such a case, the output type is inferred to be the top of the stack at the end of the function.
	- Only 1 item is returned from an inferred function. This ensures that extra stack values do not get returned on accident. Explicitly declaring multiple things need to be returned is a good idea.
- The body can span as many lines as it needs to.
- The body can contain any expression (i.e. things that aren't `define`s, `object`s, or structures, etc.)
- Some examples of functions:

```
#? A fully specified function that adds two numbers
#? Type: Function[Number, Number -> Number]
fn (lhs: Number, rhs: Number) -> Number {
  $lhs $rhs +
}

#? The same function, but a little more tacit.
#? Type: Function[Number, Number -> Number]
fn (:Number, :Number) -> Number {+}

#? You can even drop the return type
#? Type: Function[Number, Number -> Number]
fn (:Number, :Number) {+}

#? Mostly equivalent, but inferred to be an overloaded function
#? That's because `+` has multiple definitions
#? So this would be (assuming no extra overloads of `+`)
#? Type: OverloadSet[Function[Number, Number -> Number], Function[String, String -> String]]
fn {+}

#? If you prefer feeling like you're using a dynamic but
#? not tacit language
#? Type: OverloadSet[Function[Number, Number -> Number], Function[String, String -> String]]
fn (lhs, rhs) {$lhs $rhs +}

#? A simple function that takes a string, reverses it,
#? prints it, and doesn't return anything.
#? Type: Function[String -> ]
fn (:String) -> {reverse println}

#? A function that always returns the number 8, without
#? taking any arguments

fn () -> Number {8}

#? A function that take a string, and returns the string + its reverse
fn (:String) -> String, String {^ reverse}
```

- Functions can be called in a few ways:
	- Using the `call` element. This takes a function, and calls it. Note that ECS on `call` will set the arguments passed to the function.
	- Using ECS on a variable storing a function:

```
$myfun = fn (:Number, :Number) {+}
$myfun(6, 7) #? 13
6 7 $myfun() #? Takes args from stack
```

## 9.1. Argument Cycling
- If a function's parameters are specified, then the function will re-use its arguments if it tries to pop from an empty stack.
	- This reduces the number of `^`s and `\`s needed in a function
	- It's surprisingly effective - Vyxal 2 and 3 have shown it to be really useful.
- This can be thought of as having an infinite cycle of inputs on the stack, but without actually having the values on the stack.
- Examples:

```
$singleArg = fn (:Number) {println println}
$singleArg(5) #? Prints "5" twice

$doubleArg = fn (:Number, :Number) {println println println}
$doubleArg(6, 7) #? prints "6", "7", "6"
```

## 9.2. Multiple Argument Shorthand

- `fn (:Number, :Number)` is kind of verbose
- `fn (:Number * 2)` can be written instead
	- Space between `*` and type is important, otherwise it'll be seen as a minimum rank list
- `fn (:Type * n)` is `n` args of that type.
- Repetition cannot be a named argument

## 9.3. Quick Functions

- `fn {+}` is verbose for when you just want to wrap a single element in a function.
- `'element` is shorthand for `fn {element}`
- `fn {+}` becomes `'+`
- Compare:

```
[1, 2, 3] reduce(fn {+})
[1, 2, 3] reduce('+)
```

## 9.4. Stack Function Semantics

- Although the concept of a stack function is yet to be introduced, it is important to note the distinction between normal function execution and stack function execution.
- A normal function cannot write to any variables in outer scopes. All variables are local to that function.
- A stack function is able to write to variables in the calling scope, but variables defined within the stack function will be out of scope at the end of the stack function.

## 9.5. Variable Capturing 

- Say you have the following:

```
fn {
  $x = 5
  fn { $x 1 + }
}()
$wrapped = ^
```

- The inner function refers to the `x` declared inside the function.
- But `x` goes out of scope when the outer function ends
- Therefore, the inner function is said to "capture" the value of `x` held by the outer function.
  - Calling `$wrapped` would use its stored value of `x`. This is in contrast to using any `x` defined in the current scope

```
$x = 10
$wrapped() #? 6
#? It used its stored value rather than the scope's value
```

## 9.6. Call Site Type Checking (CSTC) 

- Sometimes it may be desirable to have a function accept any function as input, rather than a fixed function.
	- For example, `fn (f: Function)` to work for any arity/multiplicity
- However, executing such a function isn't type safe, because it could pop and push any number of things. This would make type checking impossible.
- But what if instead of trying to type check an unspecified function call, the type checking was deferred until the exact function substitution was known?
	- In other words, once you have a specified function being passed to an unspecified function, substitute and type check.
- Therefore, functions with unspecified function arguments will be type checked at call site - as if they were written inline.
- This process is called "Call Site Type Checking" (CSTC)
- For example:

```
$x = fn (f: Function) {5 $f()} #? Function not type checked yet
#? Signature of $x is `Function[Function -> ?]`

$x(fn {2 *}) #? $x is type checked now. It's checked as if it were originally defined as Function[Function[Number -> Number] -> Number]
```

- This may sound like it'll make compile times slower, but alternatives like constraint analysis would require just as much type checking (every time an unspecified function is used, that's a new point in the function to check for safety). Plus, it'd add a whole bunch of compiler complexity. CSTC is simpler without any extra overhead.
- This also doesn't add any runtime overhead, because CSTC is only at compile time. Runtime sees a function call just like any other normal function call.
- Motivating example to show that this is actually desirable: consider a function `dip` which applies a function to under the stack. Basically `$temp  = top; $f(); $temp`.
- With normal functions and generics, that'd be impossible to specify for all functions
- With CSTC, it becomes:

```
@returnAll define[T] dip(fn: Function, keep: T) {
  $fn() $keep
}
```

- Note that a CSTC function pops as many extra arguments as needed from the outer stack.. It's kind of like if function parameters were inferred, but with some extra specified parameters.
- CSTC is also triggered when varadaic tuples are in a function's parameters.
- If creating a function that will be CSTC'd, make sure to document the expected behaviour.
- NOTE: CSTC is only triggered when parameters include either an unspecified function, or a varadaic tuple.

## 9.7. `call` and Function Unions

- For normal `Function` types, `call` behaves without any extra details. Just pop the arguments and push the results.
- However, if `call` is given a union of functions (eg `Function[T -> U] | Function[X -> Y]`), it behaves a little differently.
- `call` will pop a number of items corresponding to the maximal arity between functions in the union. For example, `call`ing a `Function[T -> U] | Function[T, U -> V]` will pop 2 items, even if the function is actually a `Function[T -> U]`
  - This ensures that all possible outcomes of calling the function have enough arguments at compile time
- `call` will then push a number of items corresponding to the minimum multiplicity between functions in the union. For example, `Function[ -> X] | Function[ -> X, Y]` would only return 1 item.
- "But how is the function call resolved?"
- As if it were a `match`. `call`, when given `FunctionA | FunctionB | ... | FunctionN` is roughly equivalent to automatically generating:

```
match {
  as :...FunctionA.args, :FunctionA -> call,
  as :...FunctionB.args, :FunctionB -> call,
  ...,
  as :...FunctionN.args, :FunctionN -> call
}
```

- Concrete example:

```
#? Say there's a Function[Number -> Number] | Function[String, String -> String, String]
#? `call`ing it would be equivalent to

match {
  default, as :Number, as :Function[Number -> Number] -> call,
  as: String, as :String, as Function[String, String -> String, String] -> call dip: pop
}
```

# 10. Vectorisation
- A cruical part of any array language is the ability for elements to automatically apply to every list item without extra ceremony.
- Consider:

```
[1, 2, 3] map(fn {4 +})
```

- That's rather ceremonious, and not very conceptually concise. Yes, it's shorter than most mainstream programming languages, but you have the concepts of:
	- Wrapping addition in a function
	- Using map to call that function
	- The layer of indirection between adding and mapping
- Instead of going through all these layers, you can just add the number directly to the list:

```
[1, 2, 3] 4 +
```

- No map, functions, nor indirection needed.
- The vectorisation rule can be informally stated as:

> When one or more arguments to a function are of a higher rank than expected, arguments that are still above their expected rank are zipped together, and the function applied to each combination. Arguments that have reached their expected rank are reused across all combinations. This process is repeated until all arguments reach their expected ranks.

- Examples of re-use:

```py
zip([1, 2, 3], 4) == [[1, 4], [2, 4], [3, 4]]
zip([[1], [2], [3]], [1]) == [[[1], [1]], [[2], [1]], [[3], [1]]]
```

- As a high-level algorithm, roughly:

```py
def vectorized_apply(func, expected_ranks, actual_args):
    """
    func: the base function to apply
    expected_ranks: list of expected ranks for each argument [r1, r2, ...]
    actual_args: list of actual arguments with their current ranks
    """
    current_ranks = [rank_of(arg) for arg in actual_args]
    
    # Base case: all arguments at expected rank
    if current_ranks == expected_ranks:
        return func(*actual_args)
    
    # Determine which arguments need unwrapping
    needs_unwrap = [current > expected 
                    for current, expected in zip(current_ranks, expected_ranks)]
    
    # Zip arguments that need unwrapping, keep others as-is
    if any(needs_unwrap):
        # Get the lists that need zipping
        to_zip = [arg for arg, unwrap in zip(actual_args, needs_unwrap) if unwrap]
        
        # Zip them together
        zipped = zip(*to_zip)
        
        results = []
        for combo in zipped:
            # Reconstruct argument list: unwrapped args from combo, others unchanged
            new_args = []
            combo_iter = iter(combo)
            for arg, unwrap in zip(actual_args, needs_unwrap):
                if unwrap:
                    new_args.append(next(combo_iter))
                else:
                    new_args.append(arg)  # Reuse/broadcast
            
            # Recurse
            results.append(vectorized_apply(func, expected_ranks, new_args))
        
        return results
```

- When an element is applied to multiple array arguments, all arrays must have equal length at each corresponding dimension.
- For example, `[1, 2, 3] [4, 5] +` is an error, because the `3` is unpaired.
  - While it would be possible to have a trimming/re-use/universal default fill option, these can lead to surprising results.
- `[[1, 2], [3, 4, 5]] [[6, 7], [8, 9]] +` also raises a runtime error
  - The `[3, 4, 5]` does not have the same length as the `[8, 9]`
- Length mismatch errors are raised as `Panic[String]`s.
- 	Bet you can't do that in your fancy APLs. 

## 10.1. Fine Grained Vectorisation Control

- Pairwise behaviour may not always be useful.
- Consider:

```
[[1, 2], [3, 4]] [10, 20] +
```

- Pairwise results in:

```
[[1 + 10, 2 + 10], [3 + 20, 4 + 20]]
[[11, 12], [23, 24]]
```

But what if you want:

```
[
  [1, 2] + [10, 20],
  [3, 4] + [10, 20]
]
```

- You might think to wrap `+` in a function with parameters:

```
fn (:Number+, :Number+) {+}
```

- But you can also specify how to treat a higher-ranked argument using element overload disambiguation syntax:

```
+[Number+, _]
```

## 10.2. Preventing Vectorisation in an Overload

- Sometimes, automatic vectorisation may not be desirable. Especially when an atomic value in a function is _meant_ to be atomic.
- While vectorisation cannot be disabled, you can make parameters in an overload register that they are not open to being vectorised.
- `!` after a parameter type indicates that it cannot be considered as a vectorisation target.
- For example:

```
$myfun = fn (:Number!) {double}
$myfun(10) #? 20
$myfun([1, 2, 3]) #? Compile error: No overload found
double([1, 2, 3]) #? [2, 4, 6]
```

## 10.3. Vectorisation of `T~` and `T~`-able Types

- `T~` can only be safely vectorised where an atomic value is expected.
	- The only structural guarantee of a `T~` of any rugged rank is that there's atomic types present at different depths.
	- Because items can be `T | T~`, `T` is the base case
- However, `T~n` can be vectorised where `T+m` expected granted `n > m`
	- A function expecting `T+m` can safely be given `T~(n - m)`, as there'll be `> 1` level of uniform nesting
- Vectorisation behaviours of `T~` also extend to union types that are expansions of `T~`
	- For example, `T | T+` can vectorise where a `T~` can, because a `T | T+` _is_ a `T~`.
	- `{T | T+}+3` can vectorise where a `T~3` can, because it's still a `T~3`.

# 11. The `:` Modifier
- A common pattern is to pass functions to other functions. Basically higher order functions.
- For example:

```
[1, 2, 3, 4] '+ reduce 
```

- That can get majorly inconvenient and also has readability problems
  - Say you're at the end of a function and _then_ you find out you're reducing a list by it. You now have to go all the way back to the start of the function to verify it's actually reducing and to see what the list contains.

- You _could_ write:

```
[1, 2, 3, 4] reduce('+)
#? or
[1, 2, 3, 4] reduce(fn {+})
```

- But that, even by Valiance philosophical standards, is rather ceremonious.
- `:` after an element allows you to specify that the next element should be automatically wrapped as a function argument.
- For example:

```
[1, 2, 3, 4] reduce: +
#? No need for `fn {+}`, `'+` or E.C.S or postfix application
```

- If an element takes multiple function arguments, elements must be wrapped in `()` and separated by `,`.
	- This ensure that the language grammar is not context-sensitive

```
fork: (sum, length) /
```

- If `:` is used, then _all_ function arguments must be specified. This ensures 0 ambiguity as to which function-typed parameters are being filled.


# 11a. Indexing

- Indexing a list can always be done with the `get` element

```
[4, 6, 1, 3, 9, 2] get(2) #? 1
```

- But you can also do `$.[${index}]`:

```
[4, 6, 1, 3, 9, 2] $.[2] #?1
```

- The benefit of using `$.[]` over `get` is that `$.[]` allows for slicing:

```
[4, 6, 1, 3, 9, 2] $.[2:4] #? [1, 3, 9]
#? Instead of:
[4, 6, 1, 3, 9, 2] range(2, 4) get

[1, 2, 3, 4, 5, 6] $.[::2] #? [1, 3, 5]
#? Equal to
skip-every-nth(2)
```

- Slicing includes the start and stop indices
    -  For consistency with how `range` includes both start and stop
- Multiple slices too

```
[4, 6, 1, 3, 9, 2] $.[1:2, 3:4] #? [[6, 1], [3, 9]]
```

- Multidimensional indicies too

```
[[9, 2, 5], [1, 4, 2]] $.[[1, 2]] #? 4
#? equal to
$.[1] $.[2]
#? or
get(1) get(2)
```

- Multidimensional slices too

```
[[9, 2, 5], [1, 4, 2]] $.[[0, 0]:[1, 1]]
#? [[9, 2], [1, 4]]
```

- Dictionary access too

```
["name" = "Jeff", "age" = 12] $.["name"] #? "Jeff"
```

- Variable indexing too

```
$x[10] #? No need for `$.` nor `.` because it's already part of the variable
```

- Direct assignment too

```
[1, 2, 3, 4, 5]
$.[2] = 5
#? [1, 2, 5, 4, 5]

["name" = "Jeff", "age" = 12]
$.["age"] = 13
```

- Augmented assignment too

```
[1, 2, 3, 4, 5] $.[2]: double #? [1, 2, 6, 4, 5]
```

## 11a.1. Dump Indexing

- If the number of indices are known at compile time, they can be indexed to the stack
- `~[]`

```
[5, 1, 6, 2, 7] ~[3, 4] #? Pushes 2 and 7
```

- This is useful for when you have multiple things to push individually.

# 12. Partial Application

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

```rust
fn {<(_, #) filter}
```

- The `_` means "ignore filling this argument until the element is fully called"
- The `#` in `<(_, #)` means "fill this argument in `<` to be whatever is on the stack". Basically, `fn {# <}`.
- It'll push a function object of the partially applied function.
- Very useful for functional programming without verbosity.

# 13. Control Flow Structures
## 13.1. `match`

- Pop stack value and test against several branches. Execute code of first matching branch
- Branches start with the branch type. Branch type is one of:
	- `exactly`
	- `if`
	- `pattern`
	- `as`
	- `default`
 
- `exactly` branch matches if top of stack exactly matches case.
	- Multiple values can be matched in an `exactly` branch.
	- For example `exactly 6 | 7 | 8`
- `if` branch matches if top of stack, after case, is truthy
	- Note that `if` code must work for the whole type of the matched argument. If `if` recieves a `Number|String`, then all operations must be defined for that union.
- `pattern` is like scala pattern matching.
	- String exactly like scala
	- List -> `_` = single item placeholder, `...` = greedy placeholder, `$name = _` = capture placeholder, `$name = ...` = capture greedy placeholder.
	- Same business with tuples.
	- `pattern` can be followed by an `if` to match only if certain properties apply.
	- e.g. `pattern [1, ..., 3] if length 5 <=` - match if length of matched list <= 5.
- `as` is both match on type, and match into variable
	- `as :Type` -> just the type
	- `as $name: Type` -> match into name if type
	- `as $name` -> named catchall
	- `as` can be followed by an `if` to match only if certain properties are true.
	- e.g. `as :Number if 5 >`
	- The type-casted value is available.
- `default` is just the default case.

- Branch = `(type ...), (type ...) ... -> code,`. `->` separates, branch ends on `,`.
	- One item = `type ... -> code,`
	- Two items = `type ..., type ... -> code,`
	- And so on
 
- The branch body is given the matched arguments.
	- Branch bodies do not pop from the outer stack. This is to ensure consistent static typing
	- All match branches return 1 value

- Here are some defining examples:

```
stdin.readLine parseInt
match {
  exactly 10 -> "Number was 10",
  if 20 < -> "Number was less than 20",
  as :None -> "Invalid input"
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
  as $str: String -> "The string is $str",
  as $def -> "The default case"
}

match {
  exactly 6, exactly 7 -> "2025 moment"
}
```

- Each match case much match the same number of values

## 13.2. `assert` / `assert ... else`

- Basically like assert in any programming language
- `assert {cond}: "msg"` - throw exception if cond gives falsey result.
- But wait there's more.
- `assert {cond} else {errorValue}` - if cond gives falsey result, immediately return `Error(errorValue)`.
- `assert {cond}` without `else` doesn't promote the type.
- `assert ... else ...` great for validation.

Consider:

```
define validateNumberFromString(num: String) {
  assert {$num notEmpty} else {"Input was empty"}
  $num parseInt
  assert {^ notNone} else {"Input not numeric"}
  $parsed = unwrap #: Number, but safe
  assert {$parsed 0 >} else {"Negative number"}
  $parsed
}
```

```
define[T] itemAt(xs: T+, ind: Number) {
  assert {length($xs) $ind <}: "Index $ind not in bounds for list ${$xs errorFormat}"
  $xs[$ind]
}
```

## 13.3 `if`/`else if`/`else`
### 13.3. `if`

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

- Condition is evaluated according to truthiness rules.
- Inferred as

```
(arguments: $T, condition: Function, body: Function) -> $U?
where (
  $T = $condition.inputs,
  $body.inputs.startswith($condition.inputs),
  $U = $body.outputs
)
```

### 13.2. `if`/`else`

- Extension of `if` to allow for an `else` block

```
if (2 2 + 5 ==) {
  println("Math is broken")
} else {
  println("Math is fine") #? This will hopefully be printed
}
```

- Note that the `if` and `else` blocks must take the exact same parameters.
	- If the `if` block takes `Number, Number`, then the `else` block must also take `Number, Number` (or have an overload set option)
	- This restriction is for static analysis to be possible - just the number of arguments doesn't suffice. It can't be a union type nor a overload set either. `"boom" if (0) {halve} {length}`. `halve` not defined on string, but type of `length` _is_
- However, if one block were `OverloadSet[(Number, Number) -> ..., (String, String) -> ...]` and the other were `Number, Number`, that would be fine.
	- The `OverloadSet` would be inferred to be always resolved as `Number, Number`
	- Two overload sets will be the intersection of the two. BUT the `OverloadSet` will then be used as the inferred type of the if statement.

```
if (1) {+} else {/}
```

- Type of `if` block = `OverloadSet[(...)]`, type of else block = `OverloadSet[(...)]`. Type of overall if statement = intersection of the two sets.
	- Generics will be considered the same as a well specified overload, and the well-specified overload will be kept.
- Return type of `if/else` = union of return stacks. Missing values across branches are unioned with None
    - Only the input needs to be consistent (multiple points of divergence vs one uniform merging point)
- Inferred as

```
(arguments: $T, condition: Function, trueBody: Function, elseBody: Function) -> $U|$V
where (
  $T = $condition.inputs,
  $trueBody.inputs.startswith($condition.inputs),
  $trueBody.inputs $elseBody.inputs ==, 
  $U = $trueBody.outputs,
  $V = $elseBody.outputs
)
```
 
 
### 13.2.3. `if`/`else if`/`else`

```
#? In practice, use a match statement
if ($name ==("Bob")) {
  println("You're Bob!")
} else if ($name ==("Jeff")) {
  println("You're Jeff!")
} else {
  println("No match")
}
```

- All conditions must take the same number and types of parameters
- Each condition is checked against the same values
	- Conceptually as if it were a fork
- `else` must be last part of the chain
	- `if/else/else if` is invalid

## 13.3. `foreach`
- `map` and vectorisation work good for 99% of cases
	- But they don't allow for convenient access to shared state between iterations.
- `foreach` is an eager-evaluated loop that runs with stack semantics for each item in a list
- A loop body is executed for each item in the list as if it were a function that was able to write to local variables.
	- Only the last item on the stack is returned
- The return of a `foreach` is a list of all returned values

```
$sum = 0
range(1, 10) foreach ($n) {
  $sum = $sum $n +
}
```

- In practice, you should use `reduce` or `map`. Only use `foreach` if you really need the state modification.
- Inferred as

```
[T, U] (iterable: T+, body: Function[T -> U]) -> U+
```

## 13.4. `while`

- So far all looping has either been recursion-bound, or fixed length over a collection.
- `while` loops allow for arbitrary looping without recursion
- Of the form:

```
while (${condition}) {${body}}
```

- `condition` must take the same arguments (or a prefix of arguments) as `body`
- `body` is executed if `condition` is truthy.
- `body` is given the same argument(s) as `condition`
- The result of `body` must be exactly the same as the inputs
	- This allows the results to be neatly re-used for the next iteration without weird state encoding
- Initial value taken from stack
- Stack semantics enabled, so it can write to variables.
- Examples:

```
10
while (0 >) {
 ^ println("Counting down: ${id}")
 1 -
}

#? Prints for 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
```

```
$count = 10
while ($count 0 >) {
  println($count)
  $count: --
}
#? Same as the other example, but with variables and no stack inputs/outputs
```

- Notably, the parameters to `body` and `condition` are inferred. This might not always be desirable
	- Extra time needed for inference. Inference might not be what you want. No room for input cycling.
- Parameters to `while` loop can be specified as:

```
while (${params}) -> (${condition}) {${body}}
```

- For example:

```
while (:Number) -> (0 >) {println --} #? No `^` needed, because input cycling
while (n: Number) -> ($n 0 >) {println($n) $n --}
```

- While loops will return the top of the stack of the last iteration
	- Note that this means some loops may never return if they are infinite.
	- Goes without saying, be careful not to make infinite loops.
- Inferred as

```
(init: $T, condition: Function, body: Function) -> $U where (
  $T = $body.inputs,
  $U = $body.outputs,
  $body.inputs $body.outputs ==, 
  $condition.inputs.startswith($body.inputs)
  $condition.outputs [#boolean Number] ==
)
```

## 13.5. `unfold`

- Sometimes, it is desirable to collect all the results of a while loop.
- It is also desirable to be able to maintain state in a clean way between iterations
	- While loops can write to local variables, but that isn't the purest way to maintain state
- `unfold` allows for state to be maintained between iterations in a functional programming manner.
- At each iteration, `unfold` checks to see if it should continue iterating
	- Does so by evaluating `condition` on the last generated state
	- Truthy = continue, false = stop
- If it should continue, it executes the `body` using the last generated state as its input
- The value(s) returned by `body` determine the value of the iteration, and the state for the next iteration.
	- If only 1 item is on the stack, it is used as both value and state
	- Otherwise, the top two items are value and state respectively.
- The resulting list is tagged as `#infinite`
    - Although unfold can generate finite lists,  it isn't always possible to tell whether it's actually finite. Therefore, all lists are marked infinite for safety, and you can always `#-infinite` if needed.
- Syntax:

```
unfold (${condition}) {${body}}
```

- Inferred as

```
[T, U] (init: T, condition: Function[T -> #boolean Number], next: Function[T -> T, U]) -> #infinite U+
```

- Example:

```
#? Generate all fibonacci numbers < 50
(0, 1) unfold (last 50 <) { #? Stop when state[-1] > 50
  fork: last detuple + #? Construct next value
  peek: pair           #? Construct next state
  swap  #? Leave stack as [state, value]
}
```
  
- Like `while`, the exact parameter for `unfold` can be specified:

```
unfold (${params}) -> (${condition}) {${body}}
```

- Example:

```
(0, 1) unfold (state: (Number, last: Number)) -> ($last 50 <) {
  $next = $state sum
  ($last, $next) $next  
}
```

## 13.6. `at`

- A way to control vectorisation, applying a function `at` certain depths
- `at (${levels}) {${code}}`
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

# 14. The `define` structure

- Functions need to be called, whereas elements are called immediately
- `define` allows for custom elements to be defined, ready to be used just like any other element.
- If an element already exists, `define` adds a new module-scoped overload to the element. Note that module-scope overloads overwrite imported and built-in element overloads.
  - Otherwise, a new element is created.
- Syntax:

```
define[generics] name(parameters) -> returns {body}
```

- Notably, a `define` is almost the exact same as a `fn`, except with a name.
    - Outside of calling semantics, that's the only difference.
- That's the intent.
- Good practice is to define multiple overloads rather than pattern matching on types.

## 14.1. Optional Parameters

- Sometimes, it is helpful to have "configuration" style parameters.
	- For example, you might want `sort(list)` to do normal sorting, and `sort(list, key=function)` to sort by a function
- Problem is that the fixed arity requirement of overloads means you can't have `sort[T] (T+) -> T+` and `sort[T, U impl Comparable] (T+, Function[T, U]) -> T+` on the same element.
	- Fine for sorting, but sometimes it can get complicated
- Additionally, specifying when to take optional parameters from the stack can be a little unruly
	- When do values get considered part of the function call.
- However: there is one way to unambiguously specify the arguments to a element: ECS.
- Using that, `define` allows for parameters at the end of an element definition to be given a default value. This makes those parameters optional
	- They can then only be specified using ECS.
	- Function arguments can be specified with `:` syntax though.
		- _ALL_ function arguments must be specified though
- `= ${value}` after a parameter declares the default value
- Example:

```
define[T, U impl Comparable] sort(:T+, key: Function[T -> U] = fn {^}) -> T+ {...}

[4, 1, 3] sort #? Calls with default key
fn {negate} [4, 1, 3] sort #? Still calls with default key
[4, 1, 3] sort: negate #? Overwrite key
[4, 1, 3] sort(_, 'negate) #? Overwrite key
[4, 1, 3] sort(key = 'negate) #? Explicit name
```

- Note that with ECS, not all optional args must be specified
- A named argument does not need to account for the position of other non-optional args
- Passing an optional as an unnamed arg _must_ account for non-optional args
	- Like with `sort(_, 'negate)`
	- Otherwise, `'negate` is treated as the thing to sort, which is a compile error.

 ## 14.2. Overloads and Arity Consistency

- All overloads of an element must have the same arity and multiplicity
	- Compile error if there are overloads with different arities and/or multiplicities
- While mixed arity is possible in Valiance's type system, mixed-arity overloads are typically indicative of elements that should have different names.
	- Instead of `sort(T+)` and `sort(T+, Function[T -> U])`, consider `sort(T+)` and `sortBy(T+, Function[T -> U])`
	- Alternatively, `sort(T+, Function[T -> U] = fn {^}`


# 15. Objects

- Objects are comparable to `structs` or `records`. Structural key-value pairs with all members known at compile time.
- Objects have associated members, but do not own any methods
	- Rather, elements are defined on object types.
- Syntax:

```
object[generics] Name {
 ...
}
```

- `generics` is any generic type variables the object needs
- `Name` is the name of the object

## 15.1. Object Members
- Members are declared within an object body as:

```
${accessModifier} $name = value
```

- There are three levels of member visibility:
	- `public` (public read, public write)
	- `readable` (public read, private write)
	- `private` (private read, private write)
- Note that members are `readable` by default, so `readable` can be omitted:

```
readable $name = "Jeff"
#? Equivalent to
$name = "Jeff"
```

### 15.1.1. Uninitialised Object Members

- The above object member syntax requires all members to have an initial value at object definition time
- This is great for safety, but horrible for convenience/ergonomics.
- Therefore, members can be declared using:

```
${accessModifier} field ${name}: ${type}
```

- Like with normal members, the default visibilty is `readable`, so

```
readable field $name: String
#? Equivalent to
field $name: String
```

- Note that all fields _must_ be set within _all_ constructors. Failure to do so will result in a compile error
	- In this way, fields defer initalisation to the constructor. An object on the stack never has uninitialised fields.

## 15.2. Constructors

- The constructor is really just an element with the same name as the object.
- For example:

```
object Person {
  field $name: String
  define Person(name: String) {
    $name = $name
  }
}
```

- As displayed, setting a member inside a constructor will write that value.
- Temporary variables/variables not corresponding to a member will not be kept as a member.

```
define Person(name: String){
   $reversed = $name reverse #? temp variable
   #? reversed is not a member
   $name = id
}
```

### 15.2.1. Constructors Defined Members

- The person example showed the line `$name = $name`. This is very ceremonious, and rather silly.
	- `$name` is already a parameter to the constructor, why should it be repeated?
	- And yeah, you can do `$name = id` but that's still a whole extra assignment.
- Therefore, constructors are allowed to declare object members.
	- `$` before a name in an object constructor declares a field
	- Visiblity modifiers can still be applied

```
object Person {
  define Person($name: String, private $age: Number) {}
}
```

- Is the same as:

```
object Person {
  field $name: String
  private field $age: Number

  define Person(name: String, age: Number){
    $(name, age) = $name $age
  }
}
```

## 15.3. Creating Instances of Objects

- Objects are created by calling the object name just like an element.
	- ECS and everything applies
	- This has the (horrifying?) implication you can partially apply object creation
		- Sure.

```
object Person {
  field $name: String
  private field $age: Number

  define Person(name: String, age: Number){
    $(name, age) = $name $age
  }
}

Person("Joe", 69)
"Obamna" 67 Person
```

## 15.4. Accessing Object Members

- Object members can be accessed using `$.` followed by the member name.
- If an object is stored in a variable, `$name.member`.
- Note that object members can only be accessed if the space visibilty allows it.

```
Person("Joe", 69) $.name #? "Joe"
$sussy = "Obamna" 67 Person
$sussy.name #? "Obamna"
```

- If applicable, members can also be updated in the same way as you would  a variable.
- Note that this does not mutate all instances of the object (e.g. if it's been copied with `^`). It only writes it to the object on the top of the stack.

```
$person1 = Person("First Last", 1)
$person1.name = "First NewLast"
Person("Ingle Bingle", 420)
$.name = "Ingus."
```

## 15.5. Object-Friendly Elements

- Remember, objects do not own any methods.
- So then how are `readable` and `private` supposed to work if all element overloads are in `public` space?
- Solution: element definitions _inside_ the object are considered to have access to `readable` and `private`.
- These are called "object-friendly elements", as they are friendly with the object's `readable` and `private` members.
	- You will be bonked if you read that any way other than the literal, PL-specific manner.
- Object friendly elements automatically have the object type injected as a parameter
	- It's unnamed though.
	- It can be retrieved using `self`
- Object friendly elements do not automatically return the object they operate upon
	- The `@self` annotation can be used to implicitly add the object as a return value.
- For example:

```
object Label {
  define Label($text: String){}
  define updateLabel($newText: String){
    $text = $newText #? Updates self without having to access self.
    self #? Because this isn't marked @self
  }
  @self define reverseLabel() {
    $text: reverse #? The modified object is automatically returned.
  }
}

$mylabel = Label("This is a label")
println($mylable.text) #? "This is a label"
$mylabel.text = "New label text" #? Compile Error! Can't write to private member "text"
$mylabel updateLabel("New label text") #? Allowed
#? Note that the value in $mylabel has NOT been updated
println($.text) #? "New label text"
println($mylable.text) #? "This is a label"

#? You can use augmented assignment to update the variable inline without needing to do a whole reassignment
$mylabel: updateLabel("More new text")
```

## 15.6. An Example - A `Counter` Object

```
object Counter {
  $value = 0
  private $timesIncremented = 0

  define Counter(initialValue: Number){$value = id}

  @self define increment() {
    $value: ++
    $timesIncremented: ++
  }

  @self define +(:Number) {
    $value: +
    $timesIncremented: ++
  }

  define incCount() -> Number {$timesIncremented}
}

Counter(0) #? value = 0
increment increment increment #? value = 3
5 + #? value = 8
^ $.value println #? 8
incCount println #? 4
```

# 16. Traits
- No object inheritance -> Reliance upon composition.
- But! Sometimes, subtyping is very helpful
	- You might want an `Animal+` represent `{Dog|Cat}+`
- Valiance allows for the definition of traits:

```
trait ${name} {
  ${body}
}
```

- `body` contains all the required object-friendly elements an objecting implementing the trait must implement.
- An OFE is considered required if it has a body with no code
	- Comments are not considered code. Nor is whitespace
- An example trait:

```
trait Shape {
  define getArea() -> Number {}
}
```

- An object implements a trait like:

```
object ${Name} as ${TraitName} {
  ${Impls}
}
```

- Extending the `Shape` example:

```
object Rectangle {
  define Rectangle($width: Number, $height: Number) {}
}

object Circle {
  define Circle($radius: Number) {}
}

trait Shape {
  define getArea() -> Number {}
}

object Rectangle as Shape {
  define getArea() {$width $height *}
}

object Circle as Shape {
  define getArea() {$radius 2 ** 3.14 *}
}

Rectangle(6, 7) getArea #? 42
Circle(10) getArea #? 314
```

## 16.1. Traits Implementing other Traits

- Traits can implement other traits too

```
trait[T] Comparable {
  define compareTo(other: T) -> Number {}
}

trait[T] Equatable as Comparable[T] {
  define ===(other: T) -> #boolean Number {
    self compareTo($other) 0 ==
  }
  
  define !==(other: Self) -> #boolean Number {
    self ===($other) not
  }
}

trait[T] Sortable as Equatable[T] {
  define <(other: Self) -> #boolean Number {
    self compareTo($other) -1 ==
  }
  
  define >(other: Self) -> #boolean Number {
    self compareTo($other) 1 ==
  }
  
  define <=(other: Self) -> #boolean Number {
    self <($other) self ===($other) or
  }
  
  define >=(other: Self) -> #boolean Number {
    self >($other) self ===($other) or
  }
}

object Person {
  define Person($name: String, $age: Number) {}
}

object Person as Sortable[Person] {
  define compareTo(other: Person) {
    $age $other.age -
  }
}

#? Now Person automatically has ===, !==, <, >, <=, >= 
#? Just by implementing compareTo!

Person("Alice", 30) Person("Bob", 25) >  #? true
Person("Alice", 30) Person("Bob", 30) === #? true
```

# 17. Variants

- Objects and traits provide enough object-oriented support for comfortable OOPing. However, OOP support can be taken one step further with variants (what might be called `enums`, `sealed classes`, or `sum types` in other programming languages).
- Variants allow for subtyping without losing guarantees of exhaustive pattern matching. In other words, a variant is like a trait which has a finite, non-extendable, number of objects implementing the trait.
- Variants are defined with the variant keyword, and behave almost exactly the same as traits. The key difference is that objects defined inside the `variant` block will be considered subtypes of the variant.
- Syntax:

```
variant[${Generics}] ${Name} {
  ${Objects}
}
```

- An example:

```
variant Shape {
  define getArea() -> Number {}
  object Rectangle { ... }
  object Circle { ... }
}
```

- Key benefit is in pattern matching

```
#? Assuming the trait definition

define typeOf(:Shape) {
  match {
    as :Rectangle -> "Got a Rectangle",
    as :Circle    -> "Got a Circle",
    default       -> "Huh"??? 
  }
  #? If a Triangle object were defined, there
  #? would be no compiler error to indicate a
  #? change is needed.
}
```

vs

```
#? Assuming the variant definition

#define typeOf(:Shape) {
  match {
    as :Rectangle -> "Got a Rectangle",
    as :Circle    -> "Got a Circle",
  }
  #? No need for default case
  #? Adding a Triangle object to the variant
  #? will raise an exhausivity error, indicating
  #? changes are needed
}
```

# 17.a. Enumerations

- Sometimes, you may want a variant-esque structure without the ceremony of creating objects and traits
- The `enum` keyword is basically a lightweight `variant`
- Syntax:

```
enum[${generics}] ${name} {
  ${memberName} = ${memberValue}
}
```

- Note that generics is optional. If no generic is provided, the enum is considered to just be names. Note that if no generics are provided, then members cannot have corresponding values. Note that if a generic is provided, all members must have a corresponding value 

- For example:

```
enum Colour {
  RED,
  GREEN,
  BLUE
}

enum[String] TokenType {
  NUMBER = "Number",
  STRING = "String",
  L_PAREN = "(",
  R_PAREN = ")"
}
```

- Member access with `enumName.member`
- Value access with `enumName.member.value`
- Example:

```
Colour.RED
TokenType.NUMBER.value
```

- The enum name can be used as a type, just like a trait or a variant.
- Enums are closed world, meaning that, like variants, you can have exhaustive checking.
  
# 18. Generics
- Consider a `find` element that returns the first index of a certain `Number` in a list of `Number`s:

```
define find(haystack: Number+, needle: Number) {
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

- This works fine. But what if you wanted `find` to work with `String+` and `String`? You'd need to add a `(String+, String)` overload:

```
define find(haystack: String+, needle: String){
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

- Note that the entire definition is the same, except for the parameter types. Also note that this apporach to extending `find` would lead to an unruly number of lines of code.
- Generic types act as a way to define an algorithm for "some type" to be specified later. Think of it like algebra but instead of substituting numbers, you substitute types.
- Functions, element definitions, objects, traits, and variants can use generic types. The generic types that can be used by a generic-usable context typically come after the keyword, as has been displayed throughout.
- The `find` example from earlier would become:

```
define[T] find(haystack: T+, needle: T) {
  $haystack $needle ==
  truthyIndices
  first getOrElse: -1 
}
```

- While only the types have changed, this definition of find works for any type of list and compatible needle type.
  
## 18.1. Unification Algorithm:
- When a generic function is called, each parameter determines what the generic type variable must be based on its argument.
- Unification succeeds only if all parameters agree on the same type.
- Example:

```
define[T] append(xs: T+, item: T) -> T+

append([1, 2], 3)
# xs is Number+, so T must be Number
# item is Number, so T must be Number  
# Both agree → T = Number ✓

append([1, 2], "hello")
# xs is Number+, so T must be Number
# item is String, so T must be String
# Conflict → Compile error
```

- If any parameter's constraint on T conflicts with another's, the call fails to type check. 

## 18.2. Indexed Generics

- In the parameter list of a function, numbers can be used to specify taking a certain number of items from the stack. Under the hood, the popped items are automatically assigned generic types to allow for this generic behaviour. However, it may be desirable to explicitly reference the generic type of an automatically assigned generic. Therefore, `^n` will refer to the type of argument `n`. 

## 18.3. Other Notes

- There is no type erasure with generics. If something is passed an object with a generic, both object and generic types are available.
- For now, generics are invariant. This is to keep the initial design simple. Covariance and contravariance may be added at a later date.
- When they are added, `define [above T]` will be contravariance (any type above or equal to T) and `define [any T]` will be covariance (any type of T).

# 19. Tags
- By far one of the spiciest features of Valiance.
- Tags are compile-time metadata attached to values that represent properties about those values. They enable type-safe tracking of properties like sortedness, finiteness, or structural constraints without requiring explicit type hierarchies.
	- It also does so without having to have a billion specialised runtime flags.
		- Other array languages stored sortedness/finiteness/etc as runtime properties. But that means that the VM/interpreter must have each tag
			- Not very extensible
	- Tags are runtime flags but done at compile time (with some runtime tags allowed)
- There are 3 categories of tags:
	- Constructed
	- Computed
	- Variant
- Each category is handled differently throughout program flow
- Tags can only add or remove themselves. They can poll to see if other tags are in on the act, but they can only decide if they're in or out. 
 
## 19.1. Constructed Tags
- The first category is constructed tags. These represent properties that are inherent to a stack item. Such properties mostly result from how the stack item is constructed. Hence the name.
- For example, `infinite` is a constructed property of a list. Making a list infinite usually requires intent in how the list is made.
	- Like you don't (really) accidentally make a list infinite just by applying operations to it. You have to construct its infiniteness through some stream-like sequence
- Such a property is usually hard to remove too. It's best described as sticky.
	- In the example of `infinite`, most list operations do not change the finiteness of a list
		- Addition, subtraction, prefixes, etc, do not suddenly make a list finite.
		- Neither does doing something like appending an item.
		- Taking the first `n` items of an infinite list, on the other hand, does make it finite.
- Therefore, constructed tags are retained between elements _unless explicitly removed_
- This is done using a "one in all in" rule. The output of an element at call site has all the constructed tags of the input unless explicitly removed by the output or tag overlays.
- From there, you can do backwards inference on the absence of computed tags by saying "well if it's a requirement that the output not have a tag, then all inputs must not have the tag either UNLESS the output of the previous function explicitly removes the tag" 
  - Does also require checking the tag overlays 
## 19.2. Computed Tags
- Where constructed tags represent inherent properties stemming from how the stack item is created, computed tags represent properties that are picked up along the way. Such properties are computed as the result of an operation. Hence the name.
- For example, `sorted` is a computed property of a list. While sortedness can be constructed, it is very easy to make a list suddenly _not_ sorted.
	- The moment the order of items in the list change, sortedness is no longer guaranteed.
	- It must be recomputed to see if it still applies
- Such a property, therefore, is very easy to remove. It's best described as fragile.
- Therefore, computed tags are automatically removed between elements, _unless explicitly retained/added_.

## 19.3. Variant Tags
- Sometimes, computed tags may have certain sub-categories of the overall property that cannot be reliably inferred at compile time. Instead, they are variants that can be computed at runtime. Hence the name. (Continuity!)
- For example, a `sorted` list may be sorted in `ascending` or `descending` order. Problem is that determining exactly which way a list is sorted at compile time isn't always possible. Plus, having `ascending` and `descending` as individual tags adds a lot of bloat.
	- Basically tag subtyping.
- Tag variants don't get a say in when they are removed or added at compile time
- Adding a tag variant to a stack item automatically adds that variant's parent computed tag.

## 19.4. Using Tags
- "But how to use these tags?"
- First you need to define the tag:

```
tag ${category} #${tagName}
```
- `category` is one of `constructed`, `computed`, `variant`.
- `variant` tags need:

```
tag variant #${parentName} #${tagName}
```

- For example:

```
tag constructed #infinite
tag computed #sorted
tag variant #sorted #ascending
tag variant #sorted #descending
```

- You add a tag to a value in three ways:
	- `#${tagName}` after a stack item
	- Expecting the tag as part of a type parameter
	- Adding the tag as part of a function return
- For example:

```
[1, 2, 3, 4, 5] #sorted
```

- To explicitly remove a tag: `#-${tagName}`.
- For example, to remove `#infinite`, `#-infinite` (good for when you know an operation returns a finite list from an infinite list).
- Some more tag examples:

```
define[T] sort(xs: T+) -> #sorted T+ {...}

#? Optimisation
define[T] sort(xs: #sorted T+) -> #sorted T+ {id}

define[T] min(xs: #sorted T+) -> T {
  match {
    as :#descending -> last,
    default -> first
  }
}

define[T] min(xs: T+) -> T {sort min}

```

- Note that in the implementation of `min(#sorted T+)`, pattern matching is required to ensure that the tag variants of `#sorted` are considered. If it were just `first`, it would return an incorrect result for `#descending` lists.
	- Exhaustivity error if all tag variants are not considered.

## 19.5. Tag Overlays

- Defining new tag-respecting overloads for all elements is very verbose
	- Especially if the tags do not change the behaviour of the element at all.
- Consider:

```
define +(:#sorted Number, Number){
  dip: #-sorted #? Needed to avoid infinite recursion
  +
}
```

- Tags can specify "overlays" that describe how tags should be added/removed if an element is given tagged inputs
- No change in behaviour, the element is performed exactly as normal, tags stripped and all.
- Overlays are specified at tag 
- Syntax:

```
tag ${category} ${name} {
  ${overlay rules}
}

#? Single Rule
${element}[${generics}]: (${parameters}) -> ${output}

#? Multiple Rules
${element}[${generics}]: {
  (${parameters}) -> ${output},
  (${parameters}) -> ${output}
}

#? Multiple Elements at Once
(${elements})[${generics}]: ${rules}
```

- `element` is just the element
- `generics` is optional, and allows for generic type variables to be expressed
- `parameters` is the overload parameters. No names are needed, just the types.
- `output` is the return types
- The tag being defined can be represented as `#`
	- Saves repeating tag name
	- Other tags need to be spelled out
- The `+` example becomes:

```
tag computed #sorted {
  +: (# Number, Number) -> # Number
}
```

- Some more examples:

```
tag computed #sorted {
  #? Cover the basic math ops that do not change sortedness
  (+, -, /, *): {
    (# Number, Number) -> # Number,
    (Number, # Number) -> # Number,
    (# Number, # Number) -> # Number
  }
  #? Filtering a sorted list does not change sortedness
  filter[T]: (# T+, Function[T -> #boolean Number]) -> # T+
}
```

- "But what if I need to add a new tag overlay rule to a tag already defined?"
- `tag extend #${tagName}`

```
tag extend #sorted {
  #? Taking the first n items from a sorted list returns a sorted list
  take[T]: (# T+, Number) -> # T+
}
```

## 19.6. Disjointed Tags

- Sometimes, tags are incompatible
	- For example, consider two tags `#nonempty` (intention of describing a non-empty list of items) and `#empty` (intention of describing an empty-list of items)
	- A list can obviously not be `#nonempty` and `#empty` at the same time.
- You can specify that a tag is incompatible with another tag using `tag disjoint ${parentTag} ${otherTag}`
	- This will make it so that `parentTag` registers an incompatibility with `otherTag`.
- The disjoint rule is only known to `parentTag`
	- `otherTag` knows nothing about being disjoint with `parentTag`
	- This means that `parentTag` has full control over when it should be removed and when it should remove other tags.
- Attempting to add `#otherTag` when `#parentTag` is present will remove `#parentTag`. Attempting to add `#parentTag` when `#otherTag` is present will remove `#otherTag`
	- `tag disjoint` basically is `parentTag` saying "if `otherTag` is present, then I'm out."
- Example:

```
tag computed #empty {...}
tag computed #nonempty {...}

tag disjoin #empty #nonempty

[] #empty
#nonempty #? The #empty is removed because it sees that #nonempty is added, and dips.

[1, 2, 3] #nonempty
#empty #? #nonempty is removed, #empty is added.
```

## 19.7. Importing Tags

- Imported as if they were normal parts of a module
- `import ${libName}.#{$tagName}`
- Some tags are part of the core library
	- `#sorted`
	- `#infinite`

### 19.7.1. The `@tagdef` Annotation
- Adds a new definition, but care must be taken to ensure the tag is gone
- The annotation makes it so that importing the tag imports the overload
	- Otherwise, things might not get imported
	- Say you import `#sorted`, it'll also import the overloads marked `@tagdef(#sorted)`.
		- Normal importing might miss overloads that are supposed to be included.

```
@tagdef(#sorted) define[T, U] map(xs: #sorted T+, fn: Function[T -> U]) {
  xs #-sorted map($fn)
  assert {sorted?}
  #sorted
}
```

# 20. Annotations

- In the section on tags, `@tagdef` was introduced.
- It's an annotation.
- Where `:` modifies elements, annotations modify syntax structures
- There are 4 types of annotations:
	- Binding Conventions
		- These add additional bindings to the current scope. For example `@recursive` adds `this`.
	- Resolution Conventions
		- These change how certain compile time evaluations are resolved. For example, `@tagdef` changes how imports are resolved. 
	- Return Conventions
		- These change how items from an element are returned. For example `@tupled` wraps returns in a tuple. Note that such annotations are usually for things that are otherwise impractical to do from "first principles"
	- Invocation Conventions
		- These change how an element can be called. For example, `@error` makes calling an overload a compile error.
- Current planned annotations:

## 20.1. `@recursive`
- `@recursive` is a binding convention annotation. It allows for tacit recursion by making the `this` element call the outer-most `@recursive` annotated function/element.
- Very useful for functions

```
$factorial = @recursive fn (:Number) {
  match {
    exactly 0 -> 1,
    default   -> -- this *
    #? `this` calls the fn
  }
}

fn { #? Call this function A
  @recursive fn { #? Call this function B
    fn { #? Call this function C
      this #? Calls function B - it's the outer most recursive function
    }
  }
}
```

- Note that nested `@recursive` functions cannot call above the outer-most recursive function
	- `this` must be captured instead

```
#? Ignore the fact that this never terminates.
@recursive fn { #? Call this function A
  $outer = 'this
  @recursive fn { #? Call this function B
    this #? Calls function B
    $outer() #? Calls function A
  }
}
```

## 20.2. `@self`
- A return convention annotation
- As mentioned in objects, `@self` inserts the object into the return type.

## 20.3. `@tagdef`
- A resolution convention annotation
- As mentioned in tags, specifies that when resolving a tag import, all methods annotated `@tagdef` must be imported.
- Can only be used on `define`
- `@tagdef(#${tagname})`

## 20.4. `@multi`
- A resolution convention annotation
- Will be explained more in the section on multimethods

## 20.5. `@tupled`
- A return convention annotation
- Wraps the entire function return in a fixed-length tuple
- Useful for when you want to capture the whole output into a tuple, but you don't know how many items will be returned
- Tuple is determined by the function outputs.
	- If a function returns `Number, Number`, then `@tupled` will return `(Number, Number)`

```
define foo() -> Number, Number {
  6 7
}
foo #? Pushes 6, 7
@tupled foo #? Pushes (6, 7)
```

- "Why not wrap the function call in `()` then?"
	- Because that only takes the last returned item
	- `(foo)` would return `(7)`

## 20.6. `@error`
- An invocation convention annotation
- Only usable on `define`
- Marks an overload as a compile time error
	- Element must return a string
	- That string is the error message
- Primarily useful for tag overlays
	- Consider: extending `length` to be a compile time error when given `#infinite T+`
	- Just using exceptions won't cause compile-time error

```
@tagdef(#infinite) @error("Cannot get the length of an infinite list.") define[T] length(:#infinite T+) {} 
```

## 20.7. `@warn`
- Also an invocation convention annotation
- Similar to `@error`, but generates a warning instead of an error.
- Useful for when something isn't an error, but also isn't the best.
	- Or, anything where you want to warn the user (perhaps performance etc)
	- Basically a lot more applicable than `@error`
- Only usable on `define`

```
@warn("This function is experimental. Use with caution") define foo() {...}
```

## 20.8. `@deprecated`

- A more specific `@warn` that doesn't require a full message.
- Only requires the name of what should be used instead
- Can also take `since` and `why` as parameters
- Only usable on `define`

```
@deprecated("bar") define foo() {...}
```

## 20.9. `@returnAll`

- Make a function return everything on its stack instead of just returning 1 item.

# 21. Multimethods
- Standard overload resolution is static dispatch.
- The chosen overload is selected solely based on statically known types.
- But, what if arguments have been upcast to a trait?
  - `Animal+` says nothing of what animals are there
  - Mapping over an `Animal+` will apply the function defined for `Animal`.
- Executing on specialised types would otherwise require pattern matching
  - Not very extensible though, as the match statement would need to be updated every time a new subtype is added
- The `multi define` keyword allows a method to be executed at runtime based on the exact runtime type.
  - Even if static dispatch would choose the supertype overload, a `multi` annotated element would be chosen.
- A `multi` element must have a "fallback" element defined - one where all parameters are of either the same type or a supertype.
  - More specifically, if a `multi` element has parameters `(T1, T2, T3, ...)`, then there must be a non-`multi` element with parameters `(U1, U2, U3, ...)` where `T1 <= U1, T2 <= U2, T3 <= U3, ...`
- Additionally, a `multi` method must return the same type(s) as its fallback element. 
  - This restriction is what makes this system of multiple dispatch ergonomic. Otherwise the return type of the fallback element would need to be the union of all multimethods, which really isn't practical, and breaks extensibility.
  - Plus, chances are that if your runtime specialisation needs to return something different to if you just did pattern matching, then you're probably doing something wrong.
- Which element is considered the fallback is automatically handled by normal overload resolution.
  - Multimethods are only used at compile time if there is an exact type match.
  - This should not be surprising, because it's compile time resolution like there wasn't a `multi` to begin with.
- Canonical example of collisions between asteroids and spaceships
  - Note that the two objects have been made subtypes of a trait to actually show the multiple dispatch. Otherwise it'd just be normal overload resolution
  
```
trait Collidable {}
object Spaceship {}
object Spaceship as Collidable {}
object Asteroid {}
object Asteroid as Collidable {}

define collide(:Collidable * 2) {
  "Default collision"
}

multi define collide(:Asteroid, :Spaceship) {
  "a/s" 
}

multi define collide(:Spaceship, :Asteroid) {
  "s/a"
} 

multi define collide(:Spaceship * 2) {
  "s/s"
}

multi define collide(:Asteroid * 2){
  "a/a"
}
```

- Better example is Hutton's razor

```
trait Expr {}
object Val implements Expr {
  define Val(readable n: Number) {}
}
object Add implements Expr {
  define Add(readable left: Expr, readable right: Expr) {}
}

define eval(:Expr) {
  match {
    as :Val -> $.n,
    as :Add -> [$.left, $.right] eval sum
  }
}

#? Now say later you want to add multiplication

object Mul implements Expr {
  define Mul(readable left: Expr, readable right: Expr) {}
}


multi define eval(:Mul) {
  [$.left, $.right] eval product
}
```

# 22. Error Handling 

- Already seen `assert {}: ""` and `assert {} else {}`
- Two common ways of doing input validation
	- `assert {}: ""` for unrecoverable state
	- `assert {} else {}` for recoverable error

- However, sometimes unconditional exception needed. Or an exception not expressible as a condition.
- `panic(${arg})` throws an unconditional exception, with the value `arg` attached.
	- `panic` inside a function/element attaches that panic to the function type
	- `assert` also attaches `Panic`, but will always be `Panic[String]`

```
define Foo() {
  panic("Uh oh!")
}
#? Function[ -> ] + {Panic[String]}

define Bar(x: Number) {
  if ($x 0.5 >) {panic("Uh oh!")}
  if ($x 0.25 <) {panic(200)}
  $x
}
#? Function[Number -> Number] + {Panic[String] | Panic[Number]}
```

- Note that types with `Panic`s attached do _not_ need the `Panic`s handled
	- Java checked exceptions are painful
	- Handling is optional
	- Being part of the type increases transparency

- Exceptions from `panic`/`assert` can be caught using `try/handle`
	- `try` block executes code
	- `handle` block called if exception encountered
	- `handle` must name the error and specify the type
		- A default `handle` can be used to catch all cases.
- The return of a `try/handle` is `Result[T, E]` where `T` is the top of the stack at the end of the `try`, and `E` is a union of all returns from the `handles`
	- If nothing is on the stack at the end of `try`, `None` is returned.
	- Unhandled error types propagate as panics.
- All `try` _must_ have a handle
	- Otherwise there's no point. There's no silent panics
- Example:
- 
```
#? Returns Result[None, String]
try {
  Foo
} handle (err) {
  "Error occured"
}

#? Returns Result[Number, String|Number]
try {
  Bar
} handle (err) {
  $err
}

#? Returns Result[String, String]
try {
  Bar
} handle (err: String) {
  "Failed with a string"
} handle (err: Number) {
  "The number was $err"
}
```

## 22.1. `Error`/`None` Chaining

- `?` as an element is an alias for `andThen`
- `? [T, U] (Result[T, E], Function[T -> U]) -> Result[U, E] `
	- Apply the function to the `Ok` value if not error, else keep `Error`
- `? [T, U] (T?, Function[T -> U]) -> U?`
	- Apply the function if not `None`, else keep `None`
- `?!` as an element is an alias for `unwrap`
	- Given a `Result[T, E]`, return `T` if `Ok`, otherwise early return with `E`
	- Given a `T?`, return `T` if present, else early return with `None`.
 
```
#? validate (String) -> Result[String, String]
define validate(:String) {
  assert {length 0 >} else {"String was empty"}
  ^
}

#? foo () -> Result[Number, String]
define foo() {
  validate("H") ?: println
  validate("") ?! #? Exit early if it's an Error
  10
}
```

## 22.2. The `Result` Type

- A `Result[T, E]` is a value that indicates either success (`OK(T)`) or failure (`Error(E)`).
- If a `Result` is set as the explicit return type of a function, then the function must return either an `Error` or a non-`Error` value.
- If the return type of a function is being inferred, then a function returning `T | Error[E]` is inferred to return `Result[T, E]`
- This inference pattern is based on the following rules:

1. `Error[X] | Error[Y]` = `Error[X | Y]`
2. `T | Error[X]` = `Result[T, X]`
3. `T|U|...|Error[X]|Error[Y]|...` = `Result[T|U|..., X|Y|...]`

- `Result` inference only applies when an explicit type hasn't been specified
  - `fn (...) -> Error[X] | T {...}` is _not_ considered to return a Result type.
  - This allows user freedom while also reducing ceremony.

# 23. The `where` Clause

- Sometimes, interactions between parameters and returns can be difficult, even impossible, to express using the base type system.
  - Sometimes, output may depend on runtime properties of the input.
- For example, the `reshape` element can only be approximated as

```
reshape [T] (xs: T~, shape: Number+) -> T | T*
```

- This loses all rank guarantees, except for the return maybe being an atomic value or maybe being a list of some sort.
- The major problem is that list length (at least with Valiance's lack of dependent types) is unknowable at compile time.
- One idea might be to use a variadic tuple for the shape and try and get the length
  - An improvement, but still no way to attach the property to the output.
- That's where the `where` clause comes in. It is an optional component of `fn`s and `define`s.
- It allows for parameters and outputs to be specified and constrained in terms of compile time known information.
- Syntax:

```
${define/fn} where (${conds}) {...}
```

- `conds` is a coma separated list of conditions.
- Conditions can:
  - Set return information from parameters
  - Ensuring function properties match (very useful when CSTC is involved)
  - More items may be added as the design space of the `where` clause is explored by practical usage.
- Things that can happen when using a where clause:
  - The rank of a list can be extracted like `T+$n` and `$n` will be set to the rank of the list. Note that only `T+` can have their rank extracted like this.
  - Operations on rank variables include: `+`, `-`, `==`, and more to come.
  - Rank variables can be set using `$name =`
  - Function arity can be retrieved using `$name.arity`. Function parameters can be retrieved using `$name.in`
  - Function multiplicity can be retrieved using `$name.mult`. Function returns can be retrieved using `$name.out`
    - `$.in` and `$.out` return tuples
  - Tuple length can be calculated using `length`
  - Numbers can be compared using `>`, `<`, `<=` and `>=`. Also, `max` and `min` can be used on Numbers.
  - `if else` can be used to do conditional assignment of variables based on compile time information.
    - For example, `$(first, second) = if ($f.in $g.in >) {$f $g} else {$g $f}`
	- Note that the else must be present and must return exactly the same as the if branch.
  - This list will be probably extended as more things are discovered
- Note that bindings in where are usable as normal variables. But retain their compile time known values. 
- The `reshape` element becomes:

```
define[T] reshape(xs: T~, shape: (Number...) -> T+$n where ($n = $shape length) {
  reshape as T+$n
}
```

- Another example is using `where` to make `fork` pop the maximal number of arguments from the stack

```
@returnAll define fork(f: Function, g: Function) where (
  $maxArity = $f.arity $g.arity max
) {
  $first = @tupled peek: $f()
  $second = @tupled peek: $g()
  static_pop($maxArity) #? Allowed because maxArity is compile time known
  $first detuple $second detuple
}
```

- `where` clauses are validated and evaluated at call site
  - Like CSTC but without type checking the whole function. Unless of course the function is already CSTC. In which case it's CSTC'd as normal.
- The overall purpose of `where` is to allow a sort of lightweight dependent type system.
- It's very useful for providing specialisations when relevant information is compile time known.
- Another example is:

```
#? General, dynamic version
define[T] flattenByDepth(xs: T*, depth: Number) -> T* {...}

#? Specialised, compile time known version
define[T] flattenByDepth(xs: T+$n, depth: Number) -> T+$m where (
  $n $depth >, 
  $m = $n $depth -
) {flattenByDepth as T+$m}
```
 

# 24. Concurrency

- Where other languages use `async`/`await`, `fiber`s, or direct threading, Valiance uses a green threads system with channels for cross-thread communication
- `spawn { ${code} }` creates a new `Task[T]` that will execute `code` alongside the main program.
	- The `[T]` in `Task[T]` is the return type of `code`
- `wait`, when given a `Task[T]`, will block until the `Task` completes, and then return the result `T`
	- Think of it like `unwrap` for `Task`s.
- A `Task` cannot be `wait`ed more than once
	- Tracked by each `Task` storing a reference to an internal thread handle
	- So like `spawn {...}` creates thread with internal id `x`, and the returned `Task` object stores `x`. You can copy `x` as much as you like, but there's only ever 1 true value of `x`.

- But `wait`s can get ceremonious, especially if you have a lot of them
- That's why there's two ways to automatically `wait`:
1. un`wait`ed tasks are automatically `wait`ed at the end of a function if they aren't returned
2. All un`wait`ed tasks are `wait`ed at the end of a `concurrent` block

- A `concurrent` block is just a labelled wrapper around a bunch of code
- `concurrent { ${code} }`
- Serves to provide a scoped completion point without the ceremony of creating a new function.

- `wait` is defined as `[T] (Task[T]) -> T`
	- Meaning vectorisation kicks-in when given a `Task[T]+` or any list of `Task`s

- Putting this altogether:

```
spawn { println("Hello from a thread!") }
println("Hello from main thread!")
```

- The exact order is of course runtime sensitive, but it'll most likely be:

```
Hello from main thread!
Hello from a thread!
```

- Note that auto-`wait` also applies to the main program.
	- No need to sleep a little to give the `Task` time to complete

## 24.1. Channels

- What if `Task`s need to communicate with each other, as well as the outside world?
- The built-in `Channel` object serves as a communication medium
- `Channel` is defined roughly as

```
object[T] Channel {
  #? No buffer size = no bounding
  define Channel($bufferSize: Number? = None) {...}
  define write(value: T) -> {...}
  define read() -> T? {...}
  define close() -> {...}
  define hasNext() -> #boolean Number {...}
}
```

- Like `Task`s, `Channel` holds a reference to an actual channel identifier.
	- Allows `Channel`s to be `^`'d and `\`'d

- `write` will write a value to the channel. Blocks if no `Task`s are using `read` or if there's a buffer size and the channel is full. Panics if `Channel` is closed.
- `read` will "pop" and return the last written value. Blocks if `Channel` is empty. Returns `None` if `Channel` is closed or is empty. Note that `read` on a closed channel will read any remaining buffered values.
- `close` closes the channel, allowing no more `write`s.
- `hasNext` returns whether a `read` would return `None`. This allows for iterating on a `Channel` in a while loop without consuming the value.

- An example

```
$ch = Channel[String]
concurrent {
  #? Producer
  spawn {
    ["a", "b", "c"] eagermap: spawn {send($ch, _)}
    #? Close the channel once everything is sent
    close($ch)
  }
  #? Consumer
  spawn {
    #? Consume until $ch is closed/empty
    while ($ch hasNext) {println(read($ch))}
  }
  #? Concurrent block will wait until both Tasks have finished
}
```

## 24.2. `match channels`

- You thought that was it?
- Say you want to wait on multiple channels, and capture the first channel to produce a value.
- `match channels { ${channels} }` does just that.
- `channels` contains `from` branches
	- `from ${channelVar} -> ${code}`
	- `channelVar` is the channel to watch
	- `code` gets the returned value from the channel
- Blocks until a channel produces a value
- Example:

```
import time

define fetchTimeout(url: String, ms: Number) -> Result[String, String] {
  $data = Channel[String]
  $timeout = Channel[()] #? Empty tuple channel

  spawn {$data send(fetch($url))}
  spawn {time.sleep($ms) $timeout send(())}

  match channels {
    from $data    -> id, #? Just return fetch result
    from $timeout -> Error("Request timed out.") 
  }
}
```

# 25. Imports and Modules

- An important tenet of modern software engineering is code reuse. Write an element once, use it everywhere. Valiance's module system enables organising code across multiple files while maintaining clarity and type safety.
- Typically, file = module
- `import ${moduleName}` brings `moduleName` into the namespace.
- Elements, objects, traits, variants, enums, and tags can be accessed from a namespace
  - Note: if something is marked `private`, then it can't be imported
- Code inside an imported module is not executed. Only the bindings are made available.
  - No need for `if __name__ == "__main__"` because there's no execution unless the file is run directly.
- `import ${moduleName} as ${alias}` makes it so that `alias` is what's used instead.
- `import ${name}: ${components}` allows `components` to be accessed without namespace. 
- Example:

```
#? In file: greeting.vlnc
define greet(name: String) {
  println("Hello, $name!")
}

define goodbye(name: String) {
  println("Bye for now, $name!")
}
```

```
#? In file: main.vlnc
import greeting
import greeting: goodbye
greeting.greet("Joe") #? Hello, Joe!
goodbye("Joe")
```

- Circular imports are not allowed and will result in a compile error.

## 25.1. Importing an Object as a Component

- If an object is imported as a component, then all object friendly elements are automatically imported too.
- OFEs are _not_ automatically imported if the object is namespace accessed.

```
import X
X.Y X.foo
```

vs

```
import X: Y
Y foo
```

## 25.2. Tag Importing

- Importing a tag will import all overlay rules and any elements associated via `@tagdef`

```
tag computed #sorted {...}
@tagdef(#sorted) define[T] min(:#sorted T+) {$.[0]}
define[T] max(:#sorted T+) {$.[-1]}
```

```
import sorted: #sorted
#? #sorted overlay rules imported
#? min [T] (#sorted T+) -> T imported
#? max not imported
```

## 25.3. Import Visibility

- `private` before a define, object, trait, variant, or enum, will make that thing unable to be imported.
- Tags cannot be made import private, because that doesn't make sense.

## 25.4. Importing and Arity Consistency
- When you import an element as a component from another module, you must make sure that any elements in your code with the same name have the same arity

```
#? File A.vlnc
define foo(:Number) {...}
```

```
#? File B.vlnc
import A: foo

#? This is a compile error
define foo(:Number, :Number) {...}
```

- If it can't be remedied, the element cannot be component imported. It has to be referred to by namespace (`A.foo`).
- This ensures fixed arity across modules. The core idea is that you're in control over what gets imported, so don't import arity conflicts.

# 26. Eager Evaluation 

- Sometimes, it's necessary to force evaluation of a list or other lazily evaluated object.
- For example, consider:

```
[1, 2, 3] map: println
```

- In theory, this example would not print each item.
- Instead, it would sit unevaluated until a forced evaluation context (like printing or a `foreach` loop) is encountered.
- That's not ideal, because all of a sudden, your side effects from earlier are being exposed during a separate calculation:

```
[1, 2, 3] map: println
#? Scenario 1: Printing that list
println
#{ Output = "[1
1, 2
2, 3
3]"
}#
#? Scenario 2: Using a foreach
foreach {...}
#? This has the surprise of all of a sudden printing during execution
```

- Except...this isn't what happens. (pretend with me for a second that everything is implemented). Running `map: println` immediately prints each number. Further operations do not trigger the printing behaviour.
- So then what's happening? Why isn't this mix of side effects and lazy evaluation ending in a mess?
- Under the hood, println was defined as:

```
eager define[T] println(:T) -> () {...}
```

- The `eager` keyword makes it so that anything calling `println` forces eager evaluation of all of its arguments.
- Eagerness propagates up. Anything calling an eager element becomes eager itself.
  - Otherwise, you just have the same problem as before.
- Thus, `map: println` itself is eager. The map, by process of calling an eager function, becomes eager.

# Appendix. Reserved Words

```
as
as!
assert
at
call
concurrent
define
eager
else
enum
fn
foreach
handle
if
import
match
multi
object
panic
private
public
readable
self
spawn
tag
this
trait
try
unfold
variant
wait
while
```
