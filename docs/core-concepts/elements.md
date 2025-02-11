| Keyword | Symbol | Inputs | Description |
|--|--|--|--|
|`add` | `+` | `Number, Number` | lhs + rhs |
| `Sconcat` | `+` | `String, String` | `Append rhs to lhs` |
| `minus` | `-` | `Number, Number` | `lhs - rhs` |
| `Sremove` | `-` | `String, String` | `Remove matches of regex rhs from lhs` |
| `times` | `*` | `Number, Number` | `lhs × rhs` |
| `map` | `*` | `T+, ∫<U>[T*;U]` | `Map function rhs to items of lhs. Returns U+` |
| `map` | `*` | `T!, ∫<U>[T;U]` | `Map function rhs over items of lhs, returns U!` |
| `divide` | `/` | `Number, Number` | `lhs ÷ rhs` |
| `Ssplit` | `/` | `String, String` | `Split lhs on regex matches of rhs` | 
| `fold` | `/` | `T+, ∫[T*, T*...; T]` | `Reduce lhs by function rhs` |
