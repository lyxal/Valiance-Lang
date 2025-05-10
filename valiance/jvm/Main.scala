package jvm

object Main:
    def main(args: Array[String]): Unit =
        val chunk: Chunk = Chunk()
        chunk.init()

        chunk.writeByte(Opcode.PUSH_B1)
        chunk.writeByte(0x09)
        chunk.writeByte(Opcode.PUSH_B1)
        chunk.writeByte(0x0A)
        chunk.writeByte(Opcode.ADD)

        debug.disassemble(chunk)