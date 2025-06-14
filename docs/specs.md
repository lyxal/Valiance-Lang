# Valiance Language Specification

> [!NOTE]
> To view philosophy, design goals, and for a more narrative-style
> overview, check [the overview document](overview.md).

## General Language Points

* Files are, by default, UTF-8 encoded.
* Source code files use the `.vlnc` extension.
* There is no concept of "lines" in Valiance. Expressions, statements,
  etc. do not need to be separated by newlines nor semicolons.
* Whitespace is not significant, except when separating tokens.

## EBNF Definitions

```ebnf
LETTER = r[a-zA-Z]
DIGIT = r[0-9]
ELEMENT_SYMBOL = r[0-9a-zA-Z_\-?!*+=&%><]
```

## Comments

### Description

* Comments are used to annotate the source code, providing
  explanations or notes for developers.

### Syntax

* Single line comments start with `##` and continue until the first
  newline character
* Multi-line comments start with `##{` and end with `}##`
* Comments are ignored by the compiler and do not affect the program's
  behavior.

## Elements

### Description

* Elements are the basic building blocks of Valiance programs. They
  are the equivalent of keywords and operators in other languages.

### Syntax

* An element is defined as:

```ebnf
Element = (ELEMENT_SYMBOL - DIGIT) {ELEMENT_SYMBOL}
```

### System Elements

* System elements are predefined system constructs that are part of the Valiance
  language, and cannot be overridden or redefined.
* System elements encompass syntax constructs, compile-time versions
  of built-in elements, and other core language features.
* System elements are defined as:

```ebnf
SystemElement = '#' Element
```

* In this way, Valiance does not have reserved keywords in the traditional
  sense. Rather, protected concepts are marked with symbolic prefixes.

### Identifiers/Names

* Identifiers (also called "names" interchangeably) are similar
  to elements, but restricted to only letters, digits, and `_`.
* Identifiers must start with a letter or `_`.
* Identifiers are used with variables and types.
* An identifier is defined as:

```ebnf
Identifier = (LETTER | '_') {LETTER | DIGIT | '_'}
```

### Literals

* Literals are hardcoded values in the source code used to create
  some of the built-in data types.

#### Numbers

* Numbers can be whole numbers, decimal numbers, or complex numbers.

```ebnf
NumericLiteral = DecimalNumber ['i' DecimalNumber]
DecimalNumber = '-'? Number ["." Number]
Number = 0 | (r[1-9] {DIGIT})
```