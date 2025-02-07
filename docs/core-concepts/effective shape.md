# Effective Shape

In the world of arrays, shape is a very important concept. Shape defines the dimensions of a rectangular array, indicating how many items are in each dimension. From shape, rank can be derived - the number of dimensions of an array. 

However, shape is only well defined on rectangular arrays - data structures that have a consistent number of items across all axes. The traditional notion of shape quick falls apart on rugged lists. 

For example, the shape of the following lists would be undefined:

```
[[1,2],[3,4,5]]
[1, [2,3]]
[[1], [[2,3]]]
```

In the array world, these lists don't have shape. Even lists that look rectangular technically don't have shape, because the list model only has depth and item count. 

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