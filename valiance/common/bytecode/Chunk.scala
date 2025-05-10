
class Chunk:
    var code: Seq[Byte] = Seq()
    def init(): Unit = code.empty
    def writeByte(byte: Byte): Unit = code :+= byte
    def writeByte(opcode: Opcode): Unit = code :+= opcode.byte
