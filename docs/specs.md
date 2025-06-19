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

- **Atomic value** (_atomic_) = A value that is not a list. 

## Lexical Structure

### Character Set and Encoding

Valiance files, ending with the `.vlnc` extension, are utf-8 encoded files containing Valiance source code.

### Whitespace

Whitespace is considered insignificant in Valiance, except where it is used to separate tokens. Whitespace characters are:

- Space (` `) (U+0020)
- Tab (`\t`) (U+0009)
- Newline (`\n`) (U+000A)

### Code Lines

There is no concept of a "line" of code in Valiance. Code is split into tokens, and whitespace is used to separate these tokens. A line break does not imply the end of a statement or expression.

### Comments

Comments are used to annotate code and explain purpose, context, and meaning to other developers. They are ignored by the compiler and do not affect program execution. There are two types of comments:

- **Single-line comments**: Start with `##` and continue to the next newline character.
- **Multi-line comments**: Start with `#/` and end with `/#`. They can contain multiple newlines.

Multi-line comments cannot be nested.

### Elements

Elements are the basic building blocks of Valiance programs. They are the equivalent of keywords and operators in other languages.

**Syntax:**

```ebnf
DIGIT = r[0-9]
ELEMENT_SYMBOL = r[0-9a-zA-Z_\-?!*+=&%><]
Element = (ELEMENT_SYMBOL - DIGIT) {ELEMENT_SYMBOL}
```

**Notes:**

- There are no limitations on element names. In fact, reserved element names begin with a `#` (see system elements below).

More will be explained about elements further on in this specification.

### System Elements

System elements are predefined system constructs that are part of the Valiance language, and cannot be overridden or redefined. System elements encompass syntax constructs, compile-time versions of built-in elements, and other core language features.

**Syntax:**

```ebnf
SystemElement = '#' Element
```

More will be explained about system elements further on in this specification.

### Identifiers

Identifiers (also called "names" interchangeably) are similar to elements, but restricted to only letters, digits, and `_`. Identifiers must start with a letter or `_`. Identifiers are used with variables and types.

**Syntax:**

```ebnf
LETTER = (* any character with Unicode general category Lu, Ll, Lt, Lm, Lo, or Nl *)
DIGIT = (* any character with Unicode general category Nd *)
Identifier = (LETTER | '_') {LETTER | DIGIT | '_'}
```

**Notes:**

- As identifiers are used in concordance with sigils/environments expecting only a user defined name, there are no limitations on what can be used as an identifier.

### Literals

Literals are hardcoded values in the source code used to create some of the built-in data types.

#### Numeric Literals

Numbers can be whole numbers, decimal numbers, or complex numbers.

**Syntax:**

```ebnf
DIGIT = r[0-9]
NumericLiteral = DecimalNumber ['i' DecimalNumber]
DecimalNumber = '-'? Number ["." Number]
Number = 0 | (r[1-9] {DIGIT})
```

**Notes:**

- Numbers can be arbitrarily large and arbitrarily exact. There's no maximum/minimum number size, nor is there a limit to the number of decimal places that can be stored. 
- All numbers fall under the `Number` (`ℕ`) type, with subtyping as needed (eg `Number.Whole`, `Number.Decimal`).
- Numbers can also have a complex part. This will make the number equal `real part + imaginary part`

#### String Literals

Strings can consist of any number of utf8 characters. 

**Syntax**:

```ebnf
String = @" {r[^"]|@\ @"} @"
```

**Notes:**

- Strings are utf8 encoded. 
- Strings are considered a single atomic value, rather than a list of characters.
- There is a whole system of string formatting and templating. This will be specified later in this specification. 

## Types

Every value in Valiance has a type. Some built-in types are pre-provided. Types can be comprised of multiple different types, and can be modified to indicate the type is a list.

**Syntax:**

```ebnf
Type = Union_Type
Union_Type = Intersection_Type {"/" Intersection_Type}
Intersection_Type = Primary_Type {"&" Primary_Type}
Primary_Type = ((Simple_Type | Generic_Type | Tuple_Type | Dimension_Destructure_Type) [Type_Modifiers]) | ("(" Type ")")
Tuple_Type = "@(" [Tuple_Type_Item {"," Tuple_Type_Item}] ")"
Dimension_Destructure_Type = "@[" [Tuple_Type_Item {"," Tuple_Type_Item}] "]"
Tuple_Type_Item = (Identifier ":" Type) | (":" Type)
Simple_Type = Identifier
Generic_Type = Simple_Type "[" Type {"," Type} "]"
Type_Modifiers = {"+"|"~"|"?"} ["!"|"_"]
```

More on types will be explained later in this specification.

## Variables

Variables allow for values to be temporarily stored separately to the stack. Variables can be set and later pushed back to the stack.

**Syntax:**

```ebnf
Variable_Get = "$" Identifier
Variable_Set = "~>" {WHITESPACE} Identifier [":" Type]
```

**Notes**:

- All variables are local, no global variables. 
- A variable has to be set before it can be used.
- Every variable has a type. The type of a variable is determined the first time it is set. Every following variable set must set the variable to that type. 

More will be explained about variables later in this specification.

## Lexing Conflict Resolution

Tokens are completed when no additional characters can extend the current token pattern.

For example, `123abc` is lexed as `123` and `abc`.

Notably, sequences like `++` are lexed as-is. `++` will remain a single token.


## Unknown Tokens

If a character sequence cannot form a valid token, a lexical error is raised.