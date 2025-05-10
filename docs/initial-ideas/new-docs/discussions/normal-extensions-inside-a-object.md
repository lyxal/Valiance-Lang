```
#object ID: {
  0 ::=count
  #define next: {() -> (Number) =>
  $count
  1 ::{+}=count
 }
}

`ID` ::=counter

$counter:next
```

The method is allowed to modify variable attributes in-place.