# Objects

Valiance has support for OOP. `#object` allows for a new object to be defined:

```valiance
#object Name: {
    ## This is the constructor + where attributes are defined
    ## Any arguments to this function are filled when the constructor is called
}
```

Attributes are simply variable assignments.

Normal assignment makes an attribute "readable" - it can be read from outside the object, but not modified outside the object. The idea is that this
saves having to define a getter function for every attribute.

Constant assignment makes an attribute "private", much like normal OOP.

If an attribute does not have a value explicitly assigned in the constructor,
it will take its value from the stack when the constructor is called. That is,
`10 ::= attr` will set `attr` to `10` when the constructor is called, but
`::=attr` will set `attr` to whatever is on the stack at that time.

An object can also implement traits:

```valiance
#object Name implements [Trait1, Trait2, ..., TraitN]: {
    %%%
}
```

Traits are defined with `#trait`:

```valiance
#trait Name: {
    ## Extensions defined in here must be implemented by objects
    ## that implement this trait
}
```

Extensions in a trait that need to be implemented by the object can use
`%%%` as the function body if a default implementation is not provided.

## Example

```valiance
#trait Shape: {
    #define getArea: {() -> (Number) => %%%}
}

#object Circle implements [Shape]: {(:Number) =>
    ::=radius
    #define getArea: {() -> (Number) => $radius square 3.14 *}
    #define .makeBiggerBy: {(:Number) => ::{+}=radius}
}

#object Square implements [Shape]: {(:Number) =>
    ::=side
    #define getArea: {() -> (Number) => $side square}
    #define makeBiggerBy: {(:Number) => ::{+}=side}
}

#define getPerimeter: {(:Square) => (Number) => $side square 4 *}
#define getPerimeter: {(:Circle) => (Number) => $radius square 2 * 3.14}

5 `Circle` ::=myCircle
$myCircle getArea
2 $myCircle .makeBiggerBy
getPerimeter
$myCircle.radius

10 `Square` ::=mySquare
$mySquare getArea
2 $mySquare makeBiggerBy ## Useless, as it will not return the modified object
2 $mySquare:makeBiggerBy ## Performs directly to variable
$mySquare getPerimeter
```

- A `.` before an extension name indicates that the extension will return
  the modified object.
- Dot extensions can only be defined inside objects.
- General extensions defined within an object can modify object attributes
  directly. However, they will not return the modified object unless explicitly
  specified.
- A general extension defined inside an object can modify an object held
  in a variable though, and the variable will be updated. `$name:method`
  is used.
- A general extension defined outside of an object can only read attributes
  of an object that are visible outside of the object.
