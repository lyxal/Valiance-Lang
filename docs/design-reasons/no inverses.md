"The big array languages all have support for inverses, why doesn't Valiance?"

Simply put, inverses are an excuse for:

1. A lack of primitives and/or standard library functions
2. Lacking API design
3. A missing triadic assignment operator

BQN proposes two categories of inverses ("unders"):

1. Computational inverses
2. Structural inverses

Computational inverses are functions that really should be built into a language, via either primitives, or some form of standard library function. Consider Uiua, a language with prolific support for inverses. It has a primitive `√` which gets the square root of a number. The inverse of `√`, `°√`, squares a number. This is silly for two reasons: 1) `ⁿ2` already exists to square a number, and 2) `ⁿ₂` squares a number while remaining a single unit in the context of modifiers. 

Additionally, computational inverses force a naming scheme that could be better expressed with dedicated names. "un"-something is not always clearer or more obvious than having a dedicated name. Consider Uiua again. It also has a primitive `⍆` which sorts an array. The inverse of `⍆`, `°⍆` (read as `unsort`), shuffles an array. While this does make logical sense, it can be unexpected if one's interpretation of "unsorting" a list is to shuffle the list (an equally valid interpretation could be that `unsort` would return a deterministic permutation of the list that isn't sorted). 

"But computational inverses help make inverting a greater function possible"

That is true, but I believe that the need for inverting a greater function is a symptom of bad API design. Structural inverses/unders are said to "capture the pattern of doing some transformation, modifying the data, then undoing the transformation". This typically is used for two purposes:

1. Complex array modification
2. Context management

The context management use-case is easy to point out as a symptom of lacking API design. Going back to Uiua, because it's got the most involved inverses system of any array language, an example of inverses as context management is `⍜&fo` (`under fileopen`). This will read a file, perform a function on its data, and then automatically close the file. This is useful, but could easily be simulated as a method of a `File` class/library (yes, Uiua doesn't have that kind of luxury, but that's kind of why inverses are neccesary in Uiua). For example, Valiance might define:

```
#object File: {($filename: String) =>
  #define open: {() => ...}
  #define close: {() => ...}
  #define readAndDo: {(f: Function) =>
    open `f` close
  }
}

"myfile.txt" `File` readAndDo: {println}
```

(in Uiua:

```
⍜&fo &p "myfile.txt"
```
)

System function naming scheme aside, the `File` extension makes it clearer from 10ft away what the code is doing than `⍜&fo`. 

The complex array modification use-case of inverses requires a bit more to justify its absence. In traditional array languages, structural inverses provide a syntax-friendly tacit-ready method of applying functions to or on a subset of array data. For example, from the BQN docs:

```
⌽⌾(⊢↑˜≠÷2˙) "abcdef"
```

Uses under (`⌾`) to apply reverse (`⌽`) to only the first half of the string (`⊢↑˜≠÷2˙`). 

Another example from the Uiua docs:

```
⍜(⊡2|×10) [1 2 3 4]
```

Uses under (`⍜`) to apply `× 10` at item 2 (`⊡2`).

These two examples, and many more boil down to an operation that:

- Takes a list
- Takes a "doing" function
- Takes a "selection" function

And applies the "doing" function to all items returned by the "selection" function. Given that this use case of inverses would require an unweidly amount of code to simulate, it is worth adding a tradic element that acts like APL's `@`. This element is defined (roughly) as:

```
#define at: {
  ([T] list: T~,
       selection: Function[T~; T~]/T~,
       doing: Function[T~; T~]/T~
  ) =>

  $selection #match: {
    ~> f: Function[T~; T~] => {$list `f`},
    :T~ => {$list \ index}
  } ~> filtered

  $doing #match {
    ~> f: Function[T~; T~] => {$filtered `f`},
    :T~ => {$filtered length take}
  } ~> updated

  ## Code to replace filtered in list with updated
}
```

This covers the array modification use-case of inverses.

Thus, all reasons for inverses have been covered without adding any new core language features. Hence, inverses are not needed.
