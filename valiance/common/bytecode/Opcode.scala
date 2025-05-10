enum Opcode(val byte: Byte, val name: String):
    case PUSH_B1 extends Opcode(0x11, "PUSH_B1")
    case PUSH_B2 extends Opcode(0x12, "PUSH_B2")
    case ADD extends Opcode(0x20, "ADD")