# The Valiance Programming Language

## Overview

Valiance is a statically typed stack-based array programming language designed
to make array programming accessible to a wider audience. It does so by
de-emphasising the need for cryptic symbols, opting instead for a dash of
verbosity. Ideally, the meaning of programs should be somewhat obvious to
programmers coming from other languages.

## Syntax

As Valiance is a stack-based programming language, syntax is, for the most part,
reminiscent of "Reverse Polish Notation". This means that function calls come
after their arguments. For example, to add two numbers, one would write:

```valiance
1 2 +
```

This also demonstrates that data is pushed onto a central "stack", and popped
from the same stack when needed for a function call.

### Comments

Comments start with `##` and continue until the end of the line. Multi-line
comments start with `#/` and end with `/#`.

### Whitespace

Whitespace is not significant in Valiance, separation of tokens excepted.

### Numeric Literals

The syntax for numeric literals is:

```ebnf
NUMERIC_LITERAL ::= DECIMAL ("i" DECIMAL)?
DECIMAL ::= NUMBER ("." NUMBER)?
NUMBER ::= 0 | ([1-9] [0-9]*)
```

### String Literals

String literals are enclosed in double quotes. The syntax for string
literals is:

```ebnf
STRING_LITERAL ::= '"' ([^"\\] | "\\" .)* '"'
```

### List Literals

List literals are enclosed in square brackets. The syntax for list
literals is:

```ebnf
LIST_LITERAL ::= "[" (EXPRESSION ("," EXPRESSION)*)? "]"
```

`EXPRESSION` refers to any valid expression, including literals, variable retrieval, 
tuples, elements, etc.

There is more to be said about lists, but that will be for the section of the specs
that talks about array models (forewarned: it's not your typical array model).

### Tuples

Tuples start with `@(` and end with `)`. They allow for multiple values to be
grouped together without allowing for vectorisation. The syntax for tuples
is:

```ebnf
TUPLE ::= "@(" (EXPRESSION ("," EXPRESSION)*)? ")"
```

### Variables

Variables are set with `::=` and retrieved with `$`. Variable names can
be any string matching `[a-zA-Z_][0-9a-zA-Z_]*`, and are case-sensitive.

When setting a variable, the type of the variable can be specified
with a colon followed by the type name. If no type is specified,
the type is inferred from the value assigned to the variable.

```ebnf
VARIABLE_SET ::= "::=" NAME (":" TYPE)?
VARIABLE_GET ::= "$" NAME
NAME ::= [a-zA-Z_][0-9a-zA-Z_]*
```

### Types

The syntax for types is:

```ebnf
TYPE ::= UNION_TYPE
UNION_TYPE ::= INTERSECTION_TYPE ("|" INTERSECTION_TYPE)*
INTERSECTION_TYPE ::= ATOMIC_TYPE ("&" ATOMIC_TYPE)*
ATOMIC_TYPE ::= (NAME | TUPLE | LIST | FUNCTION) TYPE_OPERATION?
TYPE_OPERATION ::= ("!" | "?" | "+" | "~")+
```

### Functions

Functions start with `{` and end wit `}`. They can specify arguments and return
types, and have multiple branches. They can also omit arguments altogether to
assume a single-argument function. The syntax for functions is:

```ebnf
FUNCTION_LITERAL ::= "{" ( 
            "(" FUNCTION_PARAMETERS? ")" 
            ("->" TYPE ("," TYPE)*)? 
            "=>"
    )?
    PROGRAM
"}"
```

