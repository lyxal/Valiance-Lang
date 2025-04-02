It is impossible to be able to always determine the effective shape of a list at compile time. Sure, hardcoded lists can have their shape calculated, but the same can't be said about dynamically created lists. Non deterministic factors like RNG and user input are by definition unpredictable.  Therefore, it is impossible to provide shape safety at compile time. Only type safety can be ensured. 

But there can still be runtime shape safety. To accomplish this, the typing system is extended:

```
T+ -> Some form of list of T
T++ -> A nested list of T of at least depth 2
T+++ -> "" of at least depth 3
T++...+ -> "" of at least depth (number of pluses)
T+2 -> equivalent to T++
T+3 -> equivalent to T+++
T+n (where n is a number) -> equivalent to T++...+
T+(dimensions) -> A list of T with a minimum shape of dimensions. _ can be used to indicate the size of a dimension doesn't matter.
```

A T++...+ type will always fit into a type with less +'s. E.g T+++ is considered to be T+. 

These types lead to some design questions:

1. Should it be possible for T++...+ types to be checked at compile time? This would possibly require some form of `#asType` casts to ensure a list fits the type.