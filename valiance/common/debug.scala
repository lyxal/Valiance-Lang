object debug:
    def disassemble(chunk: Chunk): Unit =
        println("=== Disassembling chunk ===")
        chunk.code.zipWithIndex.forEach {
            case (byte, index) =>
                val opcode = Opcode(byte)
                val opcodeName = opcode.name
                val opcodeValue = byte.toHexString
                println(f"$index%02d: $opcodeName%-20s $opcodeValue")
        }

