# Valiance Language Specification

> [!NOTE]
> To view philosophy, design goals, and for a more narrative-style
> overview, check [the overview document](overview.md).

## Introduction

Valiance is a stack-based array-oriented programming language designed to make the
array programming paradigm accessible to mainstream programmers. It does
so by:

- Incorporating familiar programming constructs from traditional languages
- Providing a tacit and expressive programming environment
- De-emphasising pure mathematical elegance in favour of practicality
- Aiming to actually look like a programming language.

This document describes the language specification of Valiance, including its syntax,
semantics, and core features. It is intended to serve as a definitive reference for
language features.

## Document Semantics

- In EBNF blocks, `r` before `[...]` indicates a regular expression/character class.
- In EBNF blocks, `@` before a character is equivalent to wrapping that character in quotes and escaping it as needed. This is useful for characters that would otherwise be confusing to represent.

### Glossary

- **Atomic value** (_atomic_): A value that is not a list. 

## Lexical Structure

### Character Set and Encoding

Valiance files, ending with the `.vlnc` extension, are UTF-8 encoded files containing Valiance source code.

### Whitespace

Whitespace is considered insignificant in Valiance, except where it is used to separate tokens. Whitespace is not permitted within tokens.

Whitespace characters are:

- Space (` `) (U+0020)
- Tab (`\t`) (U+0009)
- Newline (`\n`) (U+000A)

### Code Lines

There is no concept of a "line" of code in Valiance. Code is split into tokens, and whitespace is used to separate these tokens. A line break does not imply the end of a statement or expression.

### Comments

Comments are used to annotate code and explain purpose, context, and meaning to other developers. They are ignored by the compiler and do not affect program execution. There are two types of comments:

- **Single-line comments**: Start with `##` and continue to the next newline character.
- **Multi-line comments**: Start with `#/` and end with `/#`. They can contain multiple newlines.

Multi-line comments cannot be nested; a `#/` inside an existing multi-line comment does not start a new comment.

### Elements

Elements are the basic building blocks of Valiance programs. They are the equivalent of keywords and operators in other languages.

**Syntax:**

```ebnf
DIGIT           = r[0-9]
ELEMENT_SYMBOL  = r[0-9a-zA-Z_\-?!*+=&%><]

Element = (ELEMENT_SYMBOL - DIGIT) { ELEMENT_SYMBOL }
          [ "[" Type { "," Type } "]" ]
```

**Notes:**

- There are no limitations on element names. Reserved element names begin with a #. These form system elements (see System Elements below), and are a separate syntactic construct.
- If present, the opening `[` must immediately follow the element name without any intervening whitespace.

More details about elements will be provided later in this specification.

### System Elements

System elements are predefined system constructs that are part of the Valiance language, and cannot be overridden or redefined. System elements encompass syntax constructs, compile-time versions of built-in elements, and other core language features.

**Syntax:**

```ebnf
SystemElement = '#' Element
```

More details about system elements will be provided later in this specification.

### Identifiers

Identifiers (also called "names" interchangeably) are similar to elements, but restricted to only letters, digits, and `_`. Identifiers must start with a letter or `_`. Identifiers are used with variables and types.

**Syntax:**

```ebnf
LETTER     = (* any character with Unicode general category Lu, Ll, Lt, Lm, Lo, or Nl *)
DIGIT      = (* any character with Unicode general category Nd *)
Identifier = (LETTER | '_') {LETTER | DIGIT | '_'}
```

**Notes:**

- Identifiers are used in contexts expecting only a user-defined name. There are no additional limitations on what can be used as an identifier.

### Literals

Literals are hardcoded values in the source code used to create some of the built-in data types.

#### Numeric Literals

Numbers can be whole numbers, decimal numbers, or complex numbers.

**Syntax:**

```ebnf
DIGIT          = r[0-9]

NumericLiteral = DecimalNumber ['i' DecimalNumber]
DecimalNumber  = '-'? Number ["." Number]
Number         = 0 | (r[1-9] {DIGIT})
```

**Notes:**

- Numbers can be arbitrarily large and arbitrarily exact. There's no maximum/minimum number size, nor is there a limit to the number of decimal places that can be stored. 
- All numbers fall under the `Number` (`ℕ`) type, with subtyping as needed (eg `Number.Whole`, `Number.Decimal`).
- Numbers can also have a complex part, written as `real_part i imaginary_part`. This represents the value `real_part + imaginary_part * i.`

#### String Literals

Strings can consist of any number of UTF-8 characters.

**Syntax**:

```ebnf
String = @" {r[^"]|@\ @"} @"
```

**Notes:**

- Strings are UTF-8 encoded.
- Strings are considered a single atomic value, rather than a list of characters.
- There is a whole system of string formatting and templating. This will be specified later in this specification.

#### List Literals

Lists can contain any valid expressionable constructs.

**Syntax:**

```ebnf
ListLiteral = "[" [ ListItem { "," ListItem } ] "]"

ListItem = Expressionable
```

**Notes:**

- Lists use square bracket notation
- Items are separated by commas
- Lists can be empty, nested, and heterogeneous
- List items can be any expressionable construct except variable assignments and object/trait definitions

#### Tuple Literals

Tuples are immutable, fixed-size collections with heterogeneous types.

**Syntax:**

```ebnf
TupleLiteral = "@(" [ TupleItem { "," TupleItem } ] ")"

TupleItem = [ Identifier ":" ] Expressionable
```

**Notes:**

- Tuples use `@(...)` notation
- Items can be named or unnamed
- Tuples are immutable after creation
- Tuple items have fixed types and positions

#### Dictionary Literals

Dictionaries are key-value mappings.

**Syntax:**

```ebnf
DictionaryLiteral = "#{" [ DictionaryItem { "," DictionaryItem } ] "}"

DictionaryItem = String ":" Expressionable
```

**Notes:**

- Dictionaries use `#{...}` notation
- Keys must be strings
- Values can be any expressionable construct
- Key-value pairs are separated by commas

#### String Formatting and Templates

Valiance supports string interpolation through formatting and template strings.

**Format Strings:**
```ebnf
FormatString = String
FormatOperation = FormatString Value "%"
```

**Template Strings:**
```ebnf
TemplateString = "#" String
```

Template strings immediately consume values from the stack to fill placeholders marked with `{}`.

**Placeholder Syntax:**
- `{}` - Simple value insertion
- `{operation}` - Apply operation to the value before insertion

**Examples:**
```
"Hello, {}" "World" %           ## "Hello, World"
"Count: {}" 42 %                ## "Count: 42"
"Upper: {upper}" "text" %       ## "Upper: TEXT"

"Bob" #"Hello, {}"              ## "Hello, Bob"
```

## Elements

Elements are the built-in functions and operators of Valiance. They are the fundamental building blocks that operate on stack values.

### Element Characteristics

- Elements have fixed arity (number of inputs) and multiplicity (number of outputs)
- Elements can be overloaded for different input types
- Elements may vectorise when given higher-rank inputs than expected
- Elements can be extended with user-defined overloads via `#define`

### Element Naming

Elements can have multiple names for the same functionality:
- Mathematical operators: `+`, `add`, `plus`
- Descriptive names: `length`, `count`, `size`
- Short aliases for commonly used operations

### Element Categories

Elements fall into several categories:

1. **Arithmetic**: `+`, `-`, `*`, `/`, `%`, `^` (power), `abs`, `negate`
2. **Comparison**: `==`, `===`, `<`, `>`, `<=`, `>=`, `!=`, `!==`
3. **Logic**: `and`, `or`, `not`, `xor`
4. **List operations**: `length`, `append`, `prepend`, `concat`, `transpose`
5. **Stack manipulation**: `dup`, `swap`, `pop`, `over`, `rot`
6. **Functional**: `map`, `filter`, `reduce`, `fold`, `zip`
7. **Type operations**: `as-type`, `type-of`, `assert`
8. **I/O**: `print`, `readline`, `file-read`, `file-write`

### Element Overloading

Elements can have multiple definitions for different input types:

```
## Addition works on numbers
1 2 +        ## 3

## Addition also works on strings (concatenation)
"Hello" " World" +    ## "Hello World"

## Addition works on lists (concatenation)
[1, 2] [3, 4] +      ## [1, 2, 3, 4]
```

### Built-in Element Reference

Access to original built-in definitions is preserved via `#@element`:

```
## Override addition
#define +: {(:Number, :Number) => -}

## Use original addition
2 3 #@+    ## 5 (uses original addition)
2 3 +      ## -1 (uses overridden version)
```

## Program Structure

A Valiance program consists of a sequence of statements that manipulate the stack and define program constructs.

**Syntax:**

```ebnf
Program = { Statement }

Statement = VariableAssignment
          | SystemKeyword  
          | Expressionable

Expressionable = Literal
               | Element [ Modifier ]
               | Variable_Get
               | FunctionCall
               | SystemKeyword

VariableAssignment = Variable_Set

```

### Complete Grammar Reference

For reference, here is the complete EBNF grammar for Valiance:

```ebnf
(* Core Program Structure *)
Program                = { Statement }
Statement             = VariableAssignment | ObjectDefinition | TraitDefinition 
                       | VariantDefinition | ExtensionDefinition | ModuleDeclaration
                       | ImportStatement | Expressionable

(* Expressions and Values *)
Expressionable        = Literal | Element [ Modifier ] | Variable_Get 
                       | FunctionCall | SystemKeyword

Literal               = NumericLiteral | String | ListLiteral 
                       | TupleLiteral | DictionaryLiteral | Function

(* Numeric Literals *)
NumericLiteral        = DecimalNumber [ "i" DecimalNumber ]
DecimalNumber         = [ "-" ] Number [ "." Number ]
Number                = "0" | ( r[1-9] { DIGIT } )
DIGIT                 = r[0-9]

(* String Literals *)
String                = @" { r[^"] | @\ @" } @"

(* Collection Literals *)
ListLiteral           = "[" [ Expressionable { "," Expressionable } ] "]"
TupleLiteral          = "@(" [ TupleItem { "," TupleItem } ] ")"
TupleItem             = [ Identifier ":" ] Expressionable
DictionaryLiteral     = "#{" [ DictionaryItem { "," DictionaryItem } ] "}"
DictionaryItem        = String ":" Expressionable

(* Functions *)
Function              = "{" [ FunctionSignature "=>" ] Program "}"
FunctionSignature     = [ "|" Generics "|" ] 
                       [ "(" FunctionParameters ")" ]
                       [ "->" "(" FunctionReturns ")" ]
                       [ FunctionAnnotations ]
FunctionParameters    = FunctionParameter { "," FunctionParameter }
FunctionParameter     = Identifier [ ":" Type ] | ":" Type | Number
                       | "@(" FunctionParameter { "," FunctionParameter } ")"
FunctionReturns       = FunctionReturn { "," FunctionReturn }
FunctionReturn        = ":" Type | Number
Generics              = Identifier { "," Identifier }
FunctionAnnotations   = { "#" Identifier }

(* Function Calls *)
FunctionCall          = "`" Identifier "`" | "`@" Identifier "`" 
                       | "!()" | "#>()"

(* Variables *)
Variable_Get          = "$" [ "." ] Identifier [ "." Identifier ]
Variable_Set          = "~>" [ "!" ] Identifier [ ":" Type ]
Variable_Augmented_Assignment = "$" Identifier ":" Element

(* Elements and Modifiers *)
Element               = ( ELEMENT_SYMBOL - DIGIT ) { ELEMENT_SYMBOL }
                       [ "[" Type { "," Type } "]" ]
ELEMENT_SYMBOL        = r[0-9a-zA-Z_\-?!*+=&%><]
Modifier              = Element ":" { Function | Variable_Get }

(* System Keywords *)
SystemKeyword         = "#" Identifier [ ":" "{" SystemKeywordBody "}" ]
SystemKeywordBody     = Program

(* Types *)
Type                  = UnionType
UnionType             = IntersectionType { "/" IntersectionType }
IntersectionType      = PrimaryType { "&" PrimaryType }
PrimaryType           = ( SimpleType | GenericType | TupleType )
                       [ TypeModifiers | NamedDimensionType ]
                      | "(" Type ")"
SimpleType            = Identifier
GenericType           = SimpleType "[" Type { "," Type } "]"
TupleType             = "@(" [ TupleTypeItem { "," TupleTypeItem } ] ")"
TupleTypeItem         = Identifier ":" Type | ":" Type
TypeModifiers         = { "+" | "~" | "?" } [ "!" | "_" ]
NamedDimensionType    = "@[" NamedDimensions "]"
NamedDimensions       = Identifier { "," Identifier }
                       [ ":" "[" Identifier { "," Identifier } "]"
                         { "," Identifier } ]

(* Object-Oriented Constructs *)
ObjectDefinition      = "#object" Identifier [ Generics ] 
                       [ "implements" "[" Type { "," Type } "]" ] 
                       ":" Function
TraitDefinition       = "#trait" Identifier [ Generics ]
                       [ "implements" "[" Type { "," Type } "]" ] 
                       ":" "{" TraitBody "}"
VariantDefinition     = "#variant" Identifier [ Generics ] ":" "{" VariantBody "}"
TraitBody             = { MemberDeclaration | ExtensionDeclaration }
VariantBody           = { ExtensionDeclaration | ObjectDefinition }

(* Extensions *)
ExtensionDefinition   = "#define" [ ExtensionAnnotations ] Identifier ":" Function
ExtensionAnnotations  = "#stack" | "#required"

(* Modules *)
ModuleDeclaration     = "#module" Identifier
ImportStatement       = "#import" ImportSpec
ImportSpec            = Identifier [ ":" Identifier ]
                       | Identifier "{" Identifier { "," Identifier } "}"
                       | RelativeImport
RelativeImport        = ( "./" | "../" ) { Identifier "/" } Identifier

(* Identifiers *)
Identifier            = ( LETTER | "_" ) { LETTER | DIGIT | "_" }
LETTER                = (* Unicode categories Lu, Ll, Lt, Lm, Lo, Nl *)
```

### Program Execution

1. Statements are executed sequentially
2. Each statement may modify the stack or define new constructs
3. The final stack state represents the program output
4. All elements and functions must be defined before use
5. Type checking ensures stack safety throughout execution

### File Structure

A typical Valiance file structure:

1. Optional `#module` declaration (must be first)
2. `#import` statements
3. Type, object, trait, and variant definitions
4. Extension method definitions
5. Main program logic

### Error Handling

Valiance performs extensive compile-time checking:

- **Stack underflow prevention**: Ensures sufficient stack items for operations
- **Type safety**: Verifies type compatibility for all operations  
- **Definedness checking**: Ensures all referenced elements/variables are defined
- **Pattern exhaustiveness**: Ensures variant pattern matches are exhaustive
- **Module dependency cycles**: Prevents circular import dependencies

Runtime errors are minimized through these compile-time guarantees.

## Types

Every value in Valiance has a type. Some built-in types are pre-provided. Types can be comprised of multiple different types, and can be modified to indicate the type is a list.

**Syntax:**

```ebnf
Type                   = UnionType

UnionType              = IntersectionType { "/" IntersectionType }

IntersectionType       = PrimaryType { "&" PrimaryType }

PrimaryType            = ( SimpleType | GenericType | TupleType )
                         [ TypeModifiers | NamedDimensionType ]
                       | "(" Type ")"

NamedDimensionType     = "@[" NamedDimensions "]"

NamedDimensions        = Identifier { "," Identifier }
                       [ ":" "[" Identifier { "," Identifier } "]"
                         { "," Identifier } ]

TupleType              = "@(" [ TupleTypeItem { "," TupleTypeItem } ] ")"

TupleTypeItem          = Identifier ":" Type
                       | ":" Type

SimpleType             = Identifier

GenericType            = SimpleType "[" Type { "," Type } "]"

TypeModifiers          = { "+" | "~" | "?" } [ "!" | "_" ]

```

### Built-in Types

Valiance provides several fundamental types:

| Type | Unicode Alias | Description | Examples |
|------|---------------|-------------|----------|
| `Number` | `ℕ` | A real number | `1`, `3.14`, `0.0` |
| `Number.Whole` | `ℤ` | An integer | `1`, `0`, `-1` |
| `Number.Rational` | `ℚ` | A rational number | `1/2`, `3/4`, `0/1` |
| `Number.Complex` | `ℂ` | A complex number | `1+2i`, `3.14-1.0i`, `0.0+0.0i` |
| `String` | `𝕊` | A string | `"hello"`, `"world"`, `""` |
| `None` | `∅` | A null value | `∅` |
| `Dictionary` | `§` | A dictionary | `["hello" = "world"]` |
| `Function` | `𝔽` | A function | `{(x) => $x 2 +}` |
| `OverloadedFunction` | `ℽ` | A function with multiple overloads | Multiple function definitions |
| `Tuple` | `@` | A tuple of multiple values | `@(12, "Hello")` |
| `Constructor` | `⨂` | A constructor for a type | Object constructors |

### Type Constraint Operators

Valiance does not have a dedicated list type. Instead, list types are expressed as "type operations" upon a base type.

| Operator | Description |
|----------|-------------|
| `+` | A rank 1 list of the type. Multiple `+` can be used for higher ranks. |
| `~` | A list of at least rank 1 of the type. Indicates minimum rank. |
| `/` | A union of types. |
| `&` | An intersection of types. |
| `?` | An optional type. Same as `T / None`|
| `!` | Exactly an atomic type, never a list. Prevents vectorisation. |

Any type that is not a list is termed "atomic".

### List Type Guarantees

The `+` and `~` operators provide different guarantees on the rank of the list:

- **Strong guarantee (`+`)**: The type `T+` guarantees a value will be exactly a rank 1 list of `T`. `T++` guarantees a rank 2 list, and so on.
- **Weak guarantee (`~`)**: The type `T~` guarantees a value will be a list of at least rank 1 with `T` elements, but could be arbitrarily nested.

Guarantees can be stacked. For example, `Number++` guarantees a rank 2 list of numbers, while `Number~~` guarantees at least a rank 2 list of numbers.

`+` and `~` operators cannot be mixed in a type, but a `+` list can be used where a `~` list is expected if the rank of the `+` list is greater than or equal to the rank of the `~` list.

### Rank Guards

A type `T` can be followed by `<m, n>` to indicate that the type must be a list with at least rank `m` and at most rank `n`. This is called a "rank guard". For example, `ℕ<2, 3>` is a list of numbers that is at least rank 2 and at most rank 3.

### Dynamic Types

Types can be dynamic when used with the `#where` annotation in functions, allowing type calculations based on runtime values known at compile time. For example, `T+$n` where `$n` is a compile-time known variable.

## The Stack

The stack is the fundamental execution model of Valiance. All operations are performed on the stack, with data being pushed to and popped from the stack as needed.

### Stack Operations

A stack is a last-in-first-out (LIFO) data structure that supports two primary operations:
- **Push**: Add an item to the top of the stack
- **Pop**: Remove and return the item from the top of the stack

Multiple values can be pushed or popped at once. The stack can contain any number of items, and the items need not be of the same type.

### Stack Safety

Attempting to pop from an empty stack will result in a compile-time error. Valiance performs static analysis to ensure stack underflow cannot occur.

### Stack Semantics

- Elements take their input from the stack and push their results back onto the stack
- Function calls operate on their own local stack, isolated from the calling context
- Variables provide a way to store values outside the stack temporarily

## Variables

Variables allow for values to be temporarily stored separately to the stack. Variables can be set and later pushed back to the stack.

**Syntax:**

```ebnf
Variable_Get = "$" Identifier
Variable_Set = "~>" [ "!" ] Identifier [":" Type]
Variable_Augmented_Assignment = "$" Identifier ":" Element
```

### Variable Semantics

- All variables are local to their scope. No global variables exist.
- A variable must be set before it can be used.
- Every variable has a type. The type is determined the first time the variable is set.
- Every subsequent assignment to the variable must be compatible with that type.
- Variables prefixed with `!` in their declaration (`~>!name`) are constants and cannot be reassigned.

### Variable Scoping

Variables follow lexical scoping rules:
- Variables defined in a function are local to that function
- Variables from outer scopes can be read but not modified within inner scopes
- Functions returned from other functions retain access to variables from their defining scope (closures)

### Augmented Assignment

Variables support augmented assignment operations using the syntax `$variable: operation`. This is equivalent to getting the variable, applying the operation with values from the stack, and storing the result back in the variable.

**Example:**
```
0 ~> counter
1 $counter: +  ## Equivalent to: $counter 1 + ~>counter
```

### Type Inference

If a type is not explicitly specified when setting a variable, the type is inferred from the value being stored. Explicit type annotations are useful for:
- Specifying more general types than would be inferred
- Documenting intent
- Enabling certain type compatibility checks

## Functions

Functions are user-definable objects that take input values and transform them into other values. Functions operate on their own local stack and have a fixed arity (number of inputs) and multiplicity (number of outputs).

**Syntax:**

```ebnf
Function = "{" [ FunctionSignature "=>" ] Program "}"

FunctionSignature = [ "|" Generics "|" ] 
                    [ "(" FunctionParameters ")" ]
                    [ "->" "(" FunctionReturns ")" ]
                    [ FunctionAnnotations ]

FunctionParameters = FunctionParameter { "," FunctionParameter }

FunctionParameter = Identifier [ ":" Type ]
                  | ":" Type
                  | Number
                  | "@(" FunctionParameter { "," FunctionParameter } ")"

FunctionReturns = FunctionReturn { "," FunctionReturn }

FunctionReturn = ":" Type
               | Number

Generics = Identifier { "," Identifier }

FunctionAnnotations = { "#" Identifier }

FunctionCall = "`" Identifier "`"
             | "`@" Identifier "`"
             | "!()"
             | "#>()"
```

### Function Types

The type of a function is `𝔽[<inputs> -> <outputs>]`. For example:
- `𝔽[Number, Number -> Number]` - Takes two numbers, returns one number
- `𝔽[String+ -> Number]` - Takes a list of strings, returns a number  
- `𝔽[]` - Takes no arguments, returns no values

### Function Parameters

Function parameters can be specified in several ways:

1. **Named parameters**: `x: Number` - Creates a variable `x` with the popped value
2. **Type-only parameters**: `:Number` - Pops a Number but doesn't create a variable
3. **Numeric parameters**: `2` - Pops two items, creating implicit generics
4. **Tuple destructuring**: `@(x: Number, y: Number)` - Destructures a tuple parameter

### Function Calling

Functions can be called in several ways:
- `!()` - Calls the function on top of the stack
- `` `name` `` - Calls a function stored in variable `name`
- `` `@name` `` - Calls a function and auto-tuples the results
- `#>()` - Calls a function and places results on the return stack

### Function Overloading

Functions can be overloaded using the `+` element to combine multiple function definitions:

```
{(:Number) => "Got a number"}
{(:String) => "Got a string"}
+ ~> overloaded
```

The resulting overloaded function has type `ℽ[𝔽1, 𝔽2, ..., 𝔽n]`.

### The Return Stack

Functions have access to a separate return stack for managing return values:
- `#>>` - Push a value onto the return stack
- `#>_` - Pop a value from the return stack
- `#>()` - Call a function with results going to the return stack

When a function returns, values are taken first from the return stack, then from the main stack if needed.

### Function Annotations

Functions support various annotations:
- `#recursive` - Enables `#this` for recursive calls
- `#where` - Specifies type constraints and relationships

## Vectorisation

Vectorisation is the automatic application of functions across all atomic items in a list structure. It is a fundamental feature of the array programming paradigm in Valiance.

### Vectorisation Rules

1. **Rank-based vectorisation**: An element vectorises when it expects an argument of a certain rank, but is given an argument with a higher rank.

2. **Atomic values**: Atomic values can be considered to have rank 0.

3. **Depth digging**: Elements "dig down" higher-rank arguments until the expected type is reached.

4. **Multi-argument vectorisation**: When multiple higher-ranked lists are given as inputs:
   - Items are zipped together at the appropriate depth
   - Vectorisation is recursively reapplied as needed
   - Arguments already matching expected types are kept as-is and repeated across tuples

### Vectorisation Algorithm

The vectorisation algorithm can be summarized as:

> If all arguments match the function overload, apply the function. Otherwise, zip, at the maximum shared depth, all arguments that do not match a function argument, keeping matching arguments as-is. To each item in the zip, try the vectorisation algorithm again.

### Examples

```
[1, 2, 3] [4, 5, 6] +
## Result: [5, 7, 9]

[[1, 2], [3, 4]] [[5, 6], [7, 8]] +
## Result: [[6, 8], [10, 12]]

[[1,2], [3,4]] [5,6] +
## Result: [[6, 7], [8, 9]]
```

### Preventing Vectorisation

The `!` type modifier prevents vectorisation. If a function parameter is declared with type `T!`, passing a higher-rank argument will result in a type error rather than vectorisation.

This allows functions to explicitly control when vectorisation should or should not occur.

## Modifiers

Modifiers provide syntactic sugar for passing function arguments to elements, improving code readability by keeping function definitions close to the elements that use them.

**Syntax:**

```ebnf
ModifiedElement = Element ":" { Function | Variable_Get }
```

### Modifier Semantics

When an element is followed by `:`, it reads its function arguments from the subsequent tokens instead of from the stack.

**Example:**
```
## Traditional syntax
[2, 4, 5] {(:Number) => 2 *} map

## Modifier syntax  
[2, 4, 5] map: {(:Number) => 2 *}
```

### Modifier Requirements

- An element can only be modified if it takes at least one function as an argument
- The element's function parameters are taken from the tokens following the `:`
- Non-function parameters are still taken from the stack

### Design Rationale

Modifiers are implemented as syntactic sugar rather than separate constructs to avoid duplication. This design choice:
- Maintains support for first-class functions
- Prevents redundancy between modifier and element versions
- Allows dynamic function application from the stack
- Provides syntactic convenience for static function application

The `:` symbol was chosen because:
1. It aligns with the type annotation syntax already used in Valiance (`variable: Type`)
2. It provides a clear visual separation between the element and its function arguments

## System Keywords

System keywords are core language constructs that provide functionality that cannot be expressed as regular elements or functions. They are prefixed with `#` to distinguish them from user-defined constructs.

**Syntax:**

```ebnf
SystemKeyword = "#" Identifier [ ":" "{" SystemKeywordBody "}" ]

SystemKeywordBody = Program
```

### Control Flow Keywords

#### `#if`

Conditional execution based on a numeric condition.

**Syntax:** `#if: {function}`

**Semantics:**
- Pops a number from the stack
- If the number is non-zero, calls the provided function
- If the number is zero, pushes `None` values for each value the function would have returned
- Returns optional types to maintain stack size consistency

#### `#branch`

Binary conditional execution (if/else equivalent).

**Syntax:** `#branch: {true_function} {false_function}`

**Semantics:**
- Pops a number from the stack
- If non-zero, calls the first function
- If zero, calls the second function
- Both functions must have the same multiplicity

#### `#match`

Pattern matching construct supporting multiple match types.

**Syntax:** `#match: {pattern1 => action1, pattern2 => action2, ...}`

**Pattern Types:**
- **Value matching**: Any expression, matched with `===`
- **Predicate matching**: `|expression`, matched if expression returns non-zero
- **Type matching**: `:Type`, matched if value satisfies the type
- **Variable binding**: `~>name: Type`, like type matching but stores the value
- **List destructuring**: `#[pattern, ...]`, matches list structure
- **Tuple destructuring**: `#(pattern, ...)`, matches tuple structure  
- **String patterns**: `#"pattern"`, supports string pattern matching
- **Default case**: `_`, matches anything

#### `#for`

Iteration construct for side effects (variable updates).

**Syntax:** `#for: {(:Type) => body}`

**Semantics:**
- Pops a list from the stack
- Executes the function body for each element
- Designed for updating variables in the current scope
- Does not modify the stack (side-effects only)

### Object-Oriented Keywords

#### `#object`

Defines a new object type with constructor and methods.

**Syntax:** `#object Name[Generics] implements [Traits]: {constructor}`

#### `#trait`

Defines a trait (interface) that objects can implement.

**Syntax:** `#trait Name[Generics] implements [OtherTraits]: {body}`

#### `#variant`

Defines a variant type (sealed class/enum equivalent).

**Syntax:** `#variant Name[Generics]: {body}`

### Extension Definition Keywords

#### `#define`

Defines extension methods for existing or new elements.

**Syntax:** `#define [#annotations] name: {function}`

**Annotations:**
- `#stack` - Operates on the entire stack state
- `#required` - Required implementation (for traits)

### Module Keywords

#### `#import`

Imports functionality from other modules.

**Syntax:**
- `#import ModuleName`
- `#import ModuleName: Alias`  
- `#import ModuleName{item1, item2, ...}`

#### `#module`

Declares the module name (must be first statement).

**Syntax:** `#module ModuleName`

### Stack Management Keywords

#### `#>>`

Pushes a value onto the return stack.

#### `#>_`

Pops a value from the return stack.

#### `#>()`

Calls a function with results going to the return stack.

### Recursion Keywords

#### `#this`

References the current recursive function (requires `#recursive` annotation).

**Syntax:**
- `#this` - Call current function
- `#this[n]` - Call function n levels up the call stack

## Object-Oriented Programming

Valiance integrates object-oriented programming through record-like objects with multiple dispatch and a trait system.

### Objects

Objects are defined with constructors and can have readable or private members. Methods are defined as extension methods rather than being owned by the object.

**Syntax:**

```ebnf
ObjectDefinition = "#object" Identifier [ Generics ] 
                   [ "implements" "[" Type { "," Type } "]" ] 
                   ":" Function

Generics = "[" Identifier { "," Identifier } "]"

ObjectConstruction = Identifier | Variable_Get
```

### Object Members

Object members are variables set in the constructor with specific visibility rules:

- **Readable members**: Created with `~>variable` or `$parameter` in constructor signature
- **Private members**: Created with `~>!variable` or `!parameter` in constructor signature

**Member Access:**
```ebnf
MemberAccess = "$" Identifier "." Identifier
             | "$" "." Identifier
```

### Object Constructors

The primary constructor is defined in the object declaration. Additional constructors can be defined using `#init`:

```ebnf
AdditionalConstructor = "#init" Identifier ":" Function
```

**Constructor Rules:**
- Function parameters prefixed with `$` become readable members
- Function parameters prefixed with `!` become private members  
- Variables set with `~>variable` become readable members
- Variables set with `~>!variable` become private members
- Additional constructors can only set members defined in the primary constructor
- Constructor overloads must follow function overload rules

### Extension Methods for Objects

Objects do not own their methods. Instead, extension methods can be "friendly" to objects by being defined within the object definition:

```ebnf
FriendlyExtension = "#define" [ "#" Identifier ] Identifier ":" Function
```

**Friendly Extension Privileges:**
- Can access private members
- Can read/write all object members without `$.` prefix
- Must return updated object if mutation is needed

### Object Instantiation

Objects are instantiated like function calls:
```
"Fido" "Joe" 5 `Dog`
"Name" "Owner" 3 Dog !()
```

## Generics

Generics allow functions and objects to work with any type, providing code reuse without duplication.

**Syntax:**

```ebnf
GenericDeclaration = "|" Identifier { "," Identifier } "|"
GenericConstraints = "#where" ":" "{" Constraint { "," Constraint } "}"
IndexedGeneric = "^" Number
```

### Generic Functions

Generics in functions are declared before the parameter list:

```
{|T| (haystack: T+, needle: T) -> (:Number?) => ...}
```

### Generic Objects

Generics in objects come after the object name:

```
#object List[T]: {() => [] ~> items: (T|T+)+}
```

### Generic Type Resolution

- The type `T` represents one rank lower than the input type
- Given `T+` input, `T` is the element type
- Given `T++` input, `T` is `T+` (one rank lower)

### Indexed Generics

Numeric parameters in functions create implicit generics accessible via `^n`:
- `^1` refers to the type of the first argument
- `^2` refers to the type of the second argument
- etc.

### Generic Invariance

Generics are currently invariant (no covariance/contravariance). This may be expanded in future versions.

## Traits

Traits provide interface-like functionality, allowing objects to declare they implement specific method sets without inheritance.

**Syntax:**

```ebnf
TraitDefinition = "#trait" Identifier [ Generics ]
                  [ "implements" "[" Type { "," Type } "]" ] 
                  ":" "{" TraitBody "}"

TraitBody = { MemberDeclaration | ExtensionDeclaration }

RequiredExtension = "#define" "#required" Identifier ":" FunctionSignature
DefaultExtension = "#define" Identifier ":" Function
```

### Trait Implementation

Objects implement traits by declaring them in the `implements` clause:

```
#object Person implements [Comparable[Person]]: {...}
```

### Required vs Default Implementations

- **Required**: Must be implemented by the object, declared with `#required`
- **Default**: Provided by the trait, automatically available to implementing objects

### Trait Method Conflicts

When implementing multiple traits with conflicting method names:

```ebnf
ConflictResolution = "#define" "~" Identifier "." Identifier ":" Function
```

Example:
```
#define ~TraitA.methodName: {...}
#define ~TraitB.methodName: {...}
```

## Variants

Variants provide sealed types with exhaustive pattern matching, similar to algebraic data types or enums in other languages.

**Syntax:**

```ebnf
VariantDefinition = "#variant" Identifier [ Generics ] ":" "{" VariantBody "}"

VariantBody = { ExtensionDeclaration | ObjectDefinition }
```

### Variant Semantics

- Objects defined within a variant block are subtypes of the variant
- The set of subtypes is closed (no external objects can implement the variant)
- Pattern matching on variants can omit default cases
- Adding new subtypes requires updating all pattern matches (exhaustivity checking)

### Exhaustive Pattern Matching

Variants enable exhaustive pattern matching without default cases:

```
shape #match: {
  :Rectangle => "Rectangle",
  :Circle => "Circle"
  ## No default case needed - compiler ensures exhaustivity
}
```

## Modules

Modules provide code organization and reuse capabilities, allowing code to be packaged and imported across files.

**Syntax:**

```ebnf
ModuleDeclaration = "#module" Identifier

ImportStatement = "#import" ImportSpec

ImportSpec = Identifier [ ":" Identifier ]
           | Identifier "{" Identifier { "," Identifier } "}"
           | RelativeImport

RelativeImport = ( "./" | "../" ) { Identifier "/" } Identifier
```

### Module Structure

- Each `.vlnc` file is a module by default
- Module name defaults to filename with non-keyword characters removed
- Explicit module names can be declared with `#module` (must be first statement)
- Modules can be nested using directory structure

### Import Types

1. **Namespace import**: `#import ModuleName`
   - Access as `ModuleName.item`

2. **Aliased import**: `#import ModuleName: Alias`  
   - Access as `Alias.item`

3. **Selective import**: `#import ModuleName{item1, item2}`
   - Items available without module prefix

4. **Relative import**: `#import ./LocalModule` or `#import ../ParentModule`
   - Relative to current file location

### Module Resolution

1. **Relative imports**: Resolved relative to importing file
2. **Absolute imports**: Searched in order:
   - Current package directory
   - Project root directory
   - Standard library locations
   - Additional configured directories

### Module Constraints

- **Circular dependency prevention**: Module A cannot import module B if B imports A (directly or transitively)
- **Name conflict resolution**: Conflicting imports must be disambiguated
- **Initialization order**: Modules are initialized at import time, executing top-level code

### Module Examples

```
## File: utils/math/operations.vlnc
#module Operations

#define abs: {(:Number) => #match: {0 < => negate, _ => dup}}
```

```
## File: main.vlnc
#import utils.math.Operations
#import utils.math.Operations: Math
#import Operations{abs}

-5 Operations.abs  ## Using namespace
-3 Math.abs        ## Using alias  
-1 abs             ## Using selective import
```

## Extension Methods

Extension methods allow adding new functionality to existing elements or creating new elements entirely.

**Syntax:**

```ebnf
ExtensionDefinition = "#define" [ ExtensionAnnotations ] Identifier ":" Function

ExtensionAnnotations = "#stack" | "#required"

BuiltinReference = "#@" Identifier
```

### Extension Types

1. **Regular extensions**: Add new overloads to existing elements
2. **Stack extensions**: Operate on the entire stack state (annotated with `#stack`)
3. **Required extensions**: Abstract extensions that must be implemented (used in traits)

### Extension Semantics

- Extensions add function overloads to elements
- Must follow function overload prefix rules
- Can overwrite existing built-in definitions
- Original built-in definitions accessible via `#@element`

### Stack Extensions

Stack extensions receive the entire stack state and can perform arbitrary stack manipulation:

```
#define #stack dip: {(f: Function) =>
  ~>temp    ## Store top of stack
  `f`       ## Execute function
  $temp     ## Restore stored value
}
```

### Extension Scope

- Extensions are scoped to their defining module
- Imported extensions become available in the importing module
- Extensions can be selectively imported

## Function Annotations

Function annotations provide additional metadata and capabilities for function definitions.

### `#recursive` Annotation

Enables recursive function calls using `#this`:

**Syntax:**
```
{(params) #recursive => body}
```

**Semantics:**
- `#this` calls the current function recursively
- `#this[n]` calls the function n levels up the call stack
- Enables tail recursion optimization

### `#where` Annotation

Specifies type constraints and relationships between parameters:

**Syntax:**
```
{(params) -> (returns) #where: {constraint1, constraint2, ...} => body}
```

**Constraint Operations:**
- Basic arithmetic: `+`, `-`, `*`, `/`
- Stack operations: `dup`/`^`, `swap`/`\`, `pop`/`_`
- Variable operations: get, set
- Comparison: `==`, `<=`, `>=`, `!=`, `===`
- Value access: `length`, indexed access

**Dynamic Type Examples:**
```
{(f1: Function, f2: Function) -> ($f1.out / $f2.out) #where: {
  $f1.arity $f2.arity ==,
  $f1.multy $f2.multy ==
} => ...}

{|T| (list: T~, shape: @(Number...)) -> (:T+$n) #where: {
  $shape length ~> n
} => ...}
```

## Advanced Tuple Destructuring

Tuple destructuring allows automatic extraction of structured data from tuples and lists of tuples.

**Syntax:**

```ebnf
TupleDestructuring = "@(" DestructurePattern { "," DestructurePattern } ")"

DestructurePattern = Identifier ":" Type
                   | ":" Type

DestructuredParameter = TupleDestructuring [ "+" | "++" | "~" | "~~" ]
```

### Single Tuple Destructuring

Extract components from a single tuple:

```
{(@(x: Number, y: Number)) => $x $y +}
```

### List Tuple Destructuring

Extract "columns" from lists of tuples:

```
{(@(x: Number, y: Number)+) => $x sum $y sum}
## Input: [(x: 1, y: 10), (x: 2, y: 20)]
## Result: x = [1, 2], y = [10, 20]
```

### Higher-Rank Destructuring

Handle nested structures:

```
{(@(x: Number)++) => $x}
## Preserves the nested list structure while extracting the x field
```

## Named Dimensions

Named dimensions provide semantic labeling for multidimensional data structures.

**Syntax:**

```ebnf
NamedDimensions = Type "@[" DimensionSpec { "," DimensionSpec } "]"

DimensionSpec = Identifier [ ":" "[" Identifier { "," Identifier } "]" ]
```

### Dimension Declaration

```
Number@[x, y]                          ## 2D with named dimensions
Number@[channel: [R, G, B], width, height]  ## 3D with destructured dimension
```

### Dimension Access

Named dimensions become accessible as properties:

```
{(image: Number@[channel: [R, G, B], width, height]) =>
  $image.channel  ## Access the channel dimension
  $R              ## Access the R component directly
  $image.width    ## Access width dimension
}
```

### Dimension Semantics

- Named dimensions are equivalent to exact rank types
- `Number@[x, y]` is equivalent to `Number++`
- Higher-rank inputs vectorise over extra dimensions
- Cannot mix named dimensions with tuple destructuring

### Dimension-Aware Operations

```
$image dimensions.over: {$image.channel} {max}
## Apply max over the channel dimension

$data dimensions.over: {$data.time} {avg}  
## Average over the time dimension
```

## Lexing Conflict Resolution

Tokens are completed when no additional characters can extend the current token pattern.

For example, `123abc` is lexed as two tokens: `123` (a numeric literal) and `abc` (an element).

Notably, sequences like `++` are lexed as-is. `++` will remain a single token.

## Unknown Tokens

If a character sequence cannot form a valid token, a lexical error is raised.