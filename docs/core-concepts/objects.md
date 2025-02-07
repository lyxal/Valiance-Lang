# Object Oriented Programming

**Valiance** has a rather simplified object-oriented model:

1. Objects are merely "structs". They have members which may also be functions.
2. There is no inheritance, only composition.
3. There are traits though, to provide a level of polymorphism.

## Object Creation

```
#object Name<Traits>[Generics] (
    readableMember: Type,
    $privateMember: Type
): {
    (args) =>
    ## Constructor code goes here
}
```

- Any functions defined in the member list are considered methods.

## Instantiation

```
constructorArgs `Name`
## OR
constructorArgs $Name()
```

## Accessing Members

```
$.member
## If object has been placed in a variable
$Name.member
```

## Extension Methods

Methods defined in the object require `$.` to access. However, extension
methods can be defined that allow for keyword access.

```
#extension Name: {
    (args) => %%%
}

## To make specifically part of the object

#extension Name.method: {
    (args) => %%%
}
```

### Using Extension Methods

```
## If not object-specific it's as if it were a keyword
## If object-specific:

.method
```

## Traits

Traits are a contract that, in exchange for implementing certain methods, allows
an object to be treated as if it were of a different type.

```
#trait Name (
    memberName: Type,
    methodName: Function[Types]
)
```

An object with a trait must have the required members, plus any extensions.

## Example

```
#object Node[T](
    $prev: Node[T],
    $next: Node[T],
    data: T
): {
    (val: T)
}
```