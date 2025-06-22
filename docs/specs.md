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

More details about types will be provided later in this specification.

## Variables

Variables allow for values to be temporarily stored separately to the stack. Variables can be set and later pushed back to the stack.

**Syntax:**

```ebnf
Variable_Get = "$" Identifier
Variable_Set = "~>" Identifier [":" Type]
```

**Notes**:

- All variables are local, no global variables. 
- A variable has to be set before it can be used.
- Every variable has a type. The type of a variable is determined the first time it is set. Every following variable set must set the variable to that type. 

More details about variables will be provided later in this specification.

## Lexing Conflict Resolution

Tokens are completed when no additional characters can extend the current token pattern.

For example, `123abc` is lexed as two tokens: `123` (a numeric literal) and `abc` (an element).

Notably, sequences like `++` are lexed as-is. `++` will remain a single token.

## Unknown Tokens

If a character sequence cannot form a valid token, a lexical error is raised.