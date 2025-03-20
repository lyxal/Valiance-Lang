# An Analysis on the Purpose of Hash Keywords

_For reference: A hash keyword is simply a reserved word in the Valiance
programming language that starts with a `#` character. This is in
contrast to elements which do not require a `#` character._

There are some programming language constructs in Valiance that are better
expressed as hard-coded syntax rather than a combination of elements. However,
the challenge is identifying which constructs fall under which category:
something that could be expressed as elements might have better ergonomics
and semantics as hard-coded syntax, and vice versa.

Some candidates for hard-coded syntax include:

- Things that shouldn't allow extensions. E.g. type related stuff.
- Constructs where one may want to modify local variables, but the
  element form would take a function, thus constraining variables
  to the scope of the function.
- Things that absolutely must be hard-coded syntax. E.g. `#define`

## Absolute Guaranteed Keywords

- `#define` - Literally has to be syntax. Defining overloads of an
  element can't be expressed with an element in a statically pleasing way.
- `#object` - Similar reasoning as `#define`.
- `#trait` - Similar reasoning as `#define`.
- `#import` - While some languages allow imports to be function calls (
   like CommonJS), this isn't the best idea. Importing a module based
   on a dynamic value makes static analysis harder.
- `#typeof` - While `typeof` _could_ be an element, it would allow for
  user-defined extensions, breaking the purpose of `typeof`. E.g:

```
#define typeof: {(Number) -> (String) =>
    "This would usually be something of type ⨂, but is now a string. Oops!"
}
```

- `#matchesType` - Similar reasoning as `#typeof`.
- `#assert` - A keyword to avoid user-defined extensions. Could otherwise be
  an element, callable as a modifier
- `#match` - When doing language design, I really tried to make this work as an
  element. However, the typing doesn't really work out. The element would have to
  be defined as a function with an unknown number of generic parameters. While
  not impossible to incorporate into a type system, it could lead to some
  strange behaviours. Additionally, the fact that the argument to `match` would
  have to be a function, that greatly limits what syntax could be used. There'd
  be a lot of `|`s lying around. Not very nice. Therefore, a keyword is more
  suitable, as there's no weird typing issues, and syntax options are
  infinite.

## Potential Keywords

- `#foreach` - In addition to being an element, a for loop could also
   have a keyword version that allows local variables to be modified.
   That is, guaranteed execution on-site. As an element, any references
   to local variables would be to the function scope, not the loop scope.
- `#if` - Similar reasoning as `#foreach`.
- `#bind` - To potentially disallow user-defined extensions. Seems excessive
  to require `#` every time you want to bind, but maybe that's a good thing
  given it's non-standard behaviour.
- `#thisFN` - Allow for specification of how many layers up to call as "this"


## Might Seem Like Good Fits, But Aren't

- `while` - The fact it already requires state to be passed between
  iterations makes the need for modifying local variables less
  important.
