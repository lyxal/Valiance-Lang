# Effective Shape

In the world of arrays, shape is a very important concept. Shape defines the dimensions of a rectangular array, indicating how many items are in each dimension. From shape, rank can be derived - the number of dimensions of an array. 

However, shape is only well defined on rectangular arrays - data structures that have a consistent number of items across all axes. The traditional notion of shape quick falls apart on rugged lists. 

For example, the shape of the following lists would be undefined:

```
[[1,2],[3,4,5]]
[1, [2,3]]
[[1], [[2,3]]]
```

In the Iversonian array world, these lists don't have shape. Even lists that look rectangular technically don't have shape, because the list model only has depth and item count. 

But just because something doesn't make sense under traditional array rules, that doesn't mean a different set of rules can be invented. 

This is where the concept of effective shape comes in. It's what you might call "duck shaping" if you were to make an analogy to mainstream programming terms. Essentially, if a list looks like it has certain dimensions, and can act like it has those certain dimensions, then for all intents and purposes, it has those dimensions as if it _were_ a rectangular array. 

This intuitively covers lists that would otherwise fit into a rectangular array model, but how about the examples from earlier? They certainly don't look like they can be rectangular. To this end, a general algorithm for finding the effective shape can be used:

```
1. Find the minimum depth of the list
2. Shape = []
3. At each depth up to the minimum depth:
3.1. Append the maximum length among all lists at the depth to shape
```

The algorithm can be summarised as _maximum length at minimum depth_.

Applying this to the rugged examples from before gives:

```
[[1,2],[3,4,5]] -> [2, 3]
[1, [2,3]] -> [2]
[[1], [[2,3]]] -> [2, 1]
```

Undoubtedly this will cause ruckus among array language enthusiasts - applying a well defined concept to non-well defined inputs will inevitably break properties of the well defined concept. However that's okay. That's why it's an extension, not a replacement, of the shape system. 

---

One might notice that the effective shape will return an array size larger than some of the items in a dimension. This is because the current design choice is to prefer internally empty slots over losing information - minimum shape at minimum depth would cut off the longer lists. And while returning a simpler shape (e.g minimum depth where all lists are the same size else top level) would be logically sound, I think it possible to do better than that. 

So then what happens with shorter lists? The `[[1,2],[3,4,5]] -> [2, 3]` example is a good demonstration of this problem. 

My current theoretical solution is to have an "empty" type in the interpreter. This empty type would be replaced with the default value for the array if it exists, otherwise operations with empty would return another empty. This would be different to None, which is its own type and not a default value. Empty would effectively be an adaptive type. 

This has some problems of its own that I haven't solved yet. For example, what should happen if an operation is passed more than one empty and there's no default value? Should it just return an empty leading to mysteriously disappearing values? 

This can be slightly mitigated with elements like `ensure exact shape`, but still needs some extra thought. 

---

The concept of effective shape handles deriving shape of all types of finite rugged lists (the shape of infinite lists is a whole different problem). However there is a lingering issue that needs to be resolved - how can one tell whether an effective shape is a natural fit, or an approximation? To this end, there will be three shape elements:

1. `shape` (glyph tbd, most likely a triangle) - this returns effective shape regardless of precision. 
2. `exact-shape` (glyph also tbd, most likely a triangle with a line through it if such a symbol exists) - this returns the shape if exact, else None. Basically `Number+?`.
3. `shape-meta` (name open to change, symbol yet undecided) - returns the shape with a 0 appended if exact, else a 1 if approximate. 

These 3 shape elements should provide tools generalised enough to handle all shape checking related cases. 