Terms:

- "Multibyte" - Reading bytes up to and including the first byte with a leading bit of 0.

| Bytes | Name | Description |
|--|--|--|
|`00`|`ELEMENT`|Execute the element with the given multibyte lookup code|
|`01`|`ELEMENT_B`|Like `ELEMENT` except reads the next full byte |
|`02`|`VEC_ELEMENT`|Execute the next element but with runtime vectorisation checking|
|`03`|`POP`|Pop a single value off the stack|
|`04`|`DUP`|Duplicate the top value on the stack|
|`05`|`SWAP`|Classic swap operation|
|`06`|`JMP`|Set the instruction pointer to a multibyte address|
|`07`|`JMP_B1`|Like `JMP` but the address is the next full byte|
|`08`|`VEC_ELEMENT_B`|Like `VEC_ELEMENT` except 1 byte|
|`09`|`PRINT`|Pop and print the top of the stack|
|`0a`|`JNZ`|Jump to instruction at multibyte address if top of stack is not 0|
|`0b` | `JZ` | Jump to instruction at multibyte address if top of stack is 0|
|`0c` | `ENTER` | Pop a function from the stack and set up the call frame |
| `0d` | `EXIT` | Exit function call frame |
| `0e` | `GET_VAR` | Get the variable at the multibyte address |
| `0f` | `SET_VAR` | Pop the top of the stack and set the variable at the multibyte address to that value |
|`10`|`PUSH`|Push a multibyte number|
|`11`| `PUSH_B1` | Like the union of `PUSH` and `ELEMENT_B1` |
|`12`|`PUSH_B2`|Like the union of `PUSH_B1` and `ELEMENT_B2` |
|`13`|`LOAD_CONSTANT`|Load the constant at the multibyte address|
|`14`|`DUMP_STACK`|Print the entire contents of the stack|
|`15`|`PUSH_STRING`|Push a string consisting of (multibyte number) utf8 bytes - length then bytes|
|`16`|`PUSH_LIST`|Pop the last (multibyte number) of items and wrap them into a list. Push that list back to the stack|
|`17`|`CREATE_OBJECT`|Pop a type and any required arguments and then push the newly created object|
|`18`|`PUSH_TYPE`|Push a type corresponding to the multibyte number|
|`19`|`INPUT`|Read the next line of input and push it as a string|
|`1a`|`PUSH_TYPE_B1`|Like `PUSH_TYPE` but reads only the next byte|
|`1b`|`GET_FIELD`|Access field (multibyte number) of the top of the stack|
|`1c`|`SET_FIELD`|Set field (multibyte number) to the top of the stack|
|`1d`|`DEBUG`|Print a helpful debug or diagnostic look at the program internals|
|`1e`|`PUSH_FUNCTION`|Push the next (multibyte number) of bytes as a function|
|`1f`|`GET_FUNCTION_ARG`|Push the (multibyte number)th function argument. Errors if not in a call frame|
|`20`|`ADD`|Pop 2 numbers and add them|
|`21`|`SUBTRACT`|x - y|
|`22`|`TIMES`|x × y|
|`23`|`DIVIDE`|x ÷ y|
|`24`|`INT_DIVIDE`|floor(x ÷ y)|
|`25`|`MODULO`|x % y|
|`26`|`NEGATE`|-x|
|`27`|`EQUALS`|x == y (vectorising)|
|`28`|`IS_EXACTLY`|x === y|
|`29`|`LESS_THAN`|x < y|
|`2a`|`GREATER_THAN`|x > y|
|`2b`|`LE`|x <= y|
|`2c`|`GE`|x >= y|
|`2d`|`NOT_EQUAL`|x != y (vectorising)|
|`2e`|`IS_NOT`|x !== y|
|`2f`|`ABS`|absolute value of x|
|`30`|`AND`|x && y|
|`31`|`OR`|x or y|
|`32`|`NOT`|!x|
|`33`|`LENGTH`|length of x|
|`34`|`APPEND`|x += [y]|
|`35`|`PREPEND`|[x].insert(0,y)|
|`36`|`CONCAT`|x ++ y|
|`37`|`TRANSPOSE`|transpose x|
|`38`|`AS_TYPE`|cast x to type y|
|`39`|`ASSERT`|Error if x == 0|
|`3a`|`TYPE_OF`|Push type of x|
|`3b`|`0_RANGE`|range 0 to x, exclusive|
|`3c`|`1_RANGE`|range 1 to x, inclusive|
|`3d`|`FIRST`|x[0]|
|`3e`|`LAST`|x[-1]|
|`3f`|`INDEX`|x[y]|

