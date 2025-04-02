# Function Overload Matching Algorithm

The first step is to figure out how a single parameter function would be
matched against calls to that function.

## Order of Exactness

1. Exact match
2. Base-type match, but may be list or generics
3. Optional type match
4. Intersection match
5. Union match
6. Implemented trait match

Examples:

```
Pretend that these are all overloads of the same function

A = 𝔽[T]
B = 𝔽[T|U]
C = 𝔽[T[U]]
D = 𝔽<V>[T[V]]
E = 𝔽[t]
F = 𝔽[t&u]
G = 𝔽[t|u]
H = 𝔽[W+]
I = 𝔽[X~]
J = 𝔽[Z?]
K = 𝔽[T!]
L = 𝔽[T?]

Given those, and

object M implements t
object N implements u
object O implements t, u


Function Call -> Matched Overload (Why?)
T -> A (Exact match, trumps T? and T!)
U -> B (Union match)
T[U] -> C (Exact match, beats D because there's an entire match)
T[W] -> D (Doesn't match C because W != U)
M -> E (Trait match)
O -> F (Intersection match beats single trait match)
N -> G (Union match)
W+ -> H (Exact match)
X+ -> I (X+ fits X~)
X++ -> I (X++ fits X~)
X~ -> I (Exact match)
X~~ -> I (X~~ fits X~)
Z -> J (Matches Z?)
Z? -> J (Exact match)
None -> Error (Ambiguous, could be J or L. However, if L wasn't present, it'd match J)


T+ -> A (Base type match, will vectorise)
T+? -> L (Base type match, will vectorise)
```

## Extension to Multiple Parameters

Idea: Sort by number of exact matches. If there's a tie, sort tied overloads
by number of base-type matches. If there's still a tie, sort by number of
optional matches. And so on. If after sorting, there's still a tie, then
we have an ambiguous overload, so we error.