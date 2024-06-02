from isa import TermType, Opcode, OpcodeType, OpcodeParamType, OpcodeParam

ALL_OPCODES = {
    TermType.DI: [Opcode(OpcodeType.DI, [])],
    TermType.EI: [Opcode(OpcodeType.EI, [])],
    TermType.DUP: [Opcode(OpcodeType.DUP, [])],
    TermType.ADD: [Opcode(OpcodeType.ADD, [])],
    TermType.SUB: [Opcode(OpcodeType.SUB, [])],
    TermType.MUL: [Opcode(OpcodeType.MUL, [])],
    TermType.DIV: [Opcode(OpcodeType.DIV, [])],
    TermType.MOD: [Opcode(OpcodeType.MOD, [])],
    TermType.OMIT: [Opcode(OpcodeType.OMIT, [])],
    TermType.SWAP: [Opcode(OpcodeType.SWAP, [])],
    TermType.DROP: [Opcode(OpcodeType.DROP, [])],
    TermType.OVER: [Opcode(OpcodeType.OVER, [])],
    TermType.EQ: [Opcode(OpcodeType.EQ, [])],
    TermType.LS: [Opcode(OpcodeType.LS, [])],
    TermType.GR: [Opcode(OpcodeType.GR, [])],
    TermType.READ: [Opcode(OpcodeType.READ, [])],
    TermType.VARIABLE: [],
    TermType.ALLOT: [],
    TermType.STORE: [Opcode(OpcodeType.STORE, [])],
    TermType.LOAD: [Opcode(OpcodeType.LOAD, [])],
    TermType.IF: [Opcode(OpcodeType.ZJMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    TermType.ELSE: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    TermType.THEN: [],
    TermType.DEF: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    TermType.RET: [Opcode(OpcodeType.RET, [])],
    TermType.DEF_INTR: [],
    TermType.DO: [
        Opcode(OpcodeType.DI, []),
        Opcode(OpcodeType.POP, []),  # R(i)
        Opcode(OpcodeType.POP, []),  # R(i, n)
        Opcode(OpcodeType.EI, []),
    ],
    TermType.LOOP: [
        Opcode(OpcodeType.DI, []),
        Opcode(OpcodeType.RPOP, []),  # (n)
        Opcode(OpcodeType.RPOP, []),  # (n, i)
        Opcode(OpcodeType.PUSH, [OpcodeParam(OpcodeParamType.CONST, 1)]),  # (n, i, 1)
        Opcode(OpcodeType.ADD, []),  # (n, i + 1)
        Opcode(OpcodeType.OVER, []),  # (n, i + 1, n)
        Opcode(OpcodeType.OVER, []),  # (n, i + 1, n, i + 1)
        Opcode(OpcodeType.LS, []),  # (n, i + 1, n > i + 1 [i + 1 < n])
        Opcode(OpcodeType.ZJMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)]),  # (n, i + 1)
        Opcode(OpcodeType.DROP, []),  # (n)
        Opcode(OpcodeType.DROP, []),  # ()
        Opcode(OpcodeType.EI, []),
    ],
    TermType.BEGIN: [],
    TermType.UNTIL: [Opcode(OpcodeType.ZJMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    TermType.LOOP_CNT: [
        Opcode(OpcodeType.DI, []),
        Opcode(OpcodeType.RPOP, []),
        Opcode(OpcodeType.RPOP, []),
        Opcode(OpcodeType.OVER, []),
        Opcode(OpcodeType.OVER, []),
        Opcode(OpcodeType.POP, []),
        Opcode(OpcodeType.POP, []),
        Opcode(OpcodeType.SWAP, []),
        Opcode(OpcodeType.DROP, []),
        Opcode(OpcodeType.EI, []),
    ],
    TermType.CALL: [Opcode(OpcodeType.CALL, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    TermType.ENTRYPOINT: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
}
