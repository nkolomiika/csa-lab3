from __future__ import annotations

import logging
import sys
import typing
from enum import Enum

from isa import OpcodeType, read_code

# import pytest as pytest

logger = logging.getLogger("machine_logger")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# f = open("text_alice.txt", mode='w')


class Selector(str, Enum):
    SP_INC = "sp_inc"
    SP_DEC = "sp_dec"
    I_INC = "i_inc"
    I_DEC = "i_dec"
    RET_STACK_PC = "ret_stack_pc"
    RET_STACK_OUT = "ret_stack_out"
    NEXT_MEM = "next_mem"
    NEXT_TOP = "next_top"
    NEXT_TEMP = "next_temp"
    TEMP_NEXT = "temp_next"
    TEMP_TOP = "temp_top"
    TEMP_RETURN = "temp_return"
    TOP_TEMP = "top_temp"
    TOP_NEXT = "top_next"
    TOP_ALU = "top_alu"
    TOP_MEM = "top_mem"
    TOP_IMMEDIATE = "top_immediate"
    TOP_INPUT = "top_input"
    PC_INC = "pc_int"
    PC_RET = "pc_ret"
    PC_IMMEDIATE = "pc_immediate"

    def __str__(self) -> str:
        return str(self.value)


class ALUOpcode(str, Enum):
    INC_A = "inc_a"
    INC_B = "inc_b"
    DEC_A = "dec_a"
    DEC_B = "dec_b"
    ADD = "add"
    MUL = "mul"
    DIV = "div"
    SUB = "sub"
    MOD = "mod"
    EQ = "eq"
    GR = "gr"
    LS = "ls"

    def __str__(self) -> str:
        return str(self.value)


class ALU:
    alu_operations: typing.ClassVar[list[ALUOpcode]] = [
        ALUOpcode.INC_A,
        ALUOpcode.INC_B,
        ALUOpcode.DEC_A,
        ALUOpcode.DEC_B,
        ALUOpcode.ADD,
        ALUOpcode.MUL,
        ALUOpcode.DIV,
        ALUOpcode.SUB,
        ALUOpcode.MOD,
        ALUOpcode.EQ,
        ALUOpcode.GR,
        ALUOpcode.LS,
    ]
    result = None
    src_a = None
    src_b = None
    operation = None

    def __init__(self):
        self.result = 0
        self.src_a = None
        self.src_b = None
        self.operation = None

    def calc(self) -> None:  # noqa: C901 -- function is too complex
        if self.operation == ALUOpcode.INC_A:
            self.result = self.src_a + 1
        elif self.operation == ALUOpcode.INC_B:
            self.result = self.src_b + 1
        elif self.operation == ALUOpcode.DEC_A:
            self.result = self.src_a - 1
        elif self.operation == ALUOpcode.DEC_B:
            self.result = self.src_b - 1
        elif self.operation == ALUOpcode.ADD:
            self.result = self.src_a + self.src_b
        elif self.operation == ALUOpcode.MUL:
            self.result = self.src_a * self.src_b
        elif self.operation == ALUOpcode.DIV:
            self.result = self.src_b // self.src_a
        elif self.operation == ALUOpcode.SUB:
            self.result = self.src_b - self.src_a
        elif self.operation == ALUOpcode.MOD:
            self.result = self.src_b % self.src_a
        elif self.operation == ALUOpcode.EQ:
            self.result = int(self.src_a == self.src_b)
        elif self.operation == ALUOpcode.GR:
            self.result = int(self.src_a < self.src_b)
        elif self.operation == ALUOpcode.LS:
            self.result = int(self.src_a >= self.src_b)
        else:
            pass
            # pytest.fail(f"Unknown ALU operation: {self.operation}")

    def set_details(self, src_a, src_b, operation: ALUOpcode) -> None:
        self.src_a = src_a
        self.src_b = src_b
        self.operation = operation


class DataPath:
    memory_size = None
    memory = None
    data_stack_size = None
    data_stack = None
    return_stack_size = None
    return_stack = None

    sp = None
    i = None
    pc = None
    top = None
    next = None
    temp = None

    alu = None

    def __init__(self, memory_size: int, data_stack_size: int, return_stack_size: int):
        assert memory_size > 0, "Data memory size must be greater than zero"
        assert data_stack_size > 0, "Data stack size must be greater than zero"
        assert return_stack_size > 0, "Return stack size must be greater than zero"

        self.memory_size = memory_size
        self.data_stack_size = data_stack_size
        self.return_stack_size = return_stack_size
        self.memory = [4747] * memory_size
        self.data_stack = [8877] * data_stack_size
        self.return_stack = [9988] * return_stack_size

        self.sp = 4
        self.i = 4
        self.pc = 0
        self.top = self.next = self.temp = 8877

        self.alu = ALU()

    def signal_latch_sp(self, selector: Selector) -> None:
        if selector is Selector.SP_DEC:
            self.sp -= 1
        elif selector is Selector.SP_INC:
            self.sp += 1

    def signal_latch_i(self, selector: Selector) -> None:
        if selector is Selector.I_DEC:
            self.i -= 1
        elif selector is Selector.I_INC:
            self.i += 1

    def signal_latch_next(self, selector: Selector) -> None:
        if selector is Selector.NEXT_MEM:
            assert self.sp >= 0, "Address below 0"
            assert self.sp < self.data_stack_size, "Data stack overflow"
            self.next = self.data_stack[self.sp]
        elif selector is Selector.NEXT_TOP:
            self.next = self.top
        elif selector is Selector.NEXT_TEMP:
            self.next = self.temp

    def signal_latch_temp(self, selector: Selector) -> None:
        if selector is Selector.TEMP_RETURN:
            assert self.i >= 0, "Address below 0"
            assert self.i < self.return_stack_size, "Return stack overflow"
            self.temp = self.return_stack[self.i]
        elif selector is Selector.TEMP_TOP:
            self.temp = self.top
        elif selector is Selector.TEMP_NEXT:
            self.temp = self.next

    def signal_latch_top(self, selector: Selector, immediate=0) -> None:
        if selector is Selector.TOP_NEXT:
            self.top = self.next
        elif selector is Selector.TOP_TEMP:
            self.top = self.temp
        elif selector is Selector.TOP_INPUT:
            self.top = 47474747
        elif selector is Selector.TOP_ALU:
            self.top = self.alu.result
        elif selector is Selector.TOP_MEM:
            self.top = self.memory[self.top]
        elif selector is Selector.TOP_IMMEDIATE:
            self.top = immediate

    def signal_data_wr(self) -> None:
        assert self.sp >= 0, "Address below 0"
        assert self.sp < self.data_stack_size, "Data stack overflow"
        self.data_stack[self.sp] = self.next

    def signal_ret_wr(self, selector: Selector) -> None:
        assert self.i >= 0, "Address below 0"
        assert self.i < self.return_stack_size, "Return stack overflow"
        if selector is Selector.RET_STACK_PC:
            self.return_stack[self.i] = self.pc
        elif selector is Selector.RET_STACK_OUT:
            self.return_stack[self.i] = self.temp

    def signal_mem_write(self) -> None:
        assert self.top >= 0, "Address below 0"
        assert self.top < self.memory_size, "Memory overflow"
        self.memory[self.top] = self.next

    def signal_alu_operation(self, operation: ALUOpcode) -> None:
        self.alu.set_details(self.top, self.next, operation)
        self.alu.calc()


def opcode_to_alu_opcode(opcode_type: OpcodeType):
    return {
        OpcodeType.MUL: ALUOpcode.MUL,
        OpcodeType.DIV: ALUOpcode.DIV,
        OpcodeType.SUB: ALUOpcode.SUB,
        OpcodeType.ADD: ALUOpcode.ADD,
        OpcodeType.MOD: ALUOpcode.MOD,
        OpcodeType.EQ: ALUOpcode.EQ,
        OpcodeType.GR: ALUOpcode.GR,
        OpcodeType.LS: ALUOpcode.LS,
    }.get(opcode_type)


class ControlUnit:
    out_buffer = ""

    program_memory_size = None
    program_memory = None
    data_path = None
    ps = None
    IO = "h"

    input_tokens: typing.ClassVar[list[tuple]] = []
    tokens_handled: typing.ClassVar[list[bool]] = []

    instuct_number = 0

    def __init__(self, data_path: DataPath, program_memory_size: int, input_tokens: list[tuple]):
        self.data_path = data_path
        self.input_tokens = input_tokens
        self.tokens_handled = [False for _ in input_tokens]
        self.program_memory_size = program_memory_size
        self.program_memory = [{"index": x, "command": 0, "arg": 0} for x in range(self.program_memory_size)]
        self.ps = {"Intr_Req": False, "Intr_On": True}

    def fill_command_memory(self, opcodes: list) -> None:
        for opcode in opcodes:
            mem_cell = int(opcode["index"])
            assert 0 <= mem_cell < self.program_memory_size, "Program index out of memory size"
            self.program_memory[mem_cell] = opcode

    def signal_latch_pc(self, selector: Selector, immediate=0) -> None:
        if selector is Selector.PC_INC:
            self.data_path.pc += 1
        elif selector is Selector.PC_RET:
            self.data_path.pc = self.data_path.return_stack[self.data_path.i]
        elif selector is Selector.PC_IMMEDIATE:
            self.data_path.pc = immediate - 1

    def signal_latch_ps(self, intr_on: bool) -> None:
        self.ps["Intr_On"] = intr_on
        self.ps["Intr_Req"] = self.check_for_interrupts()

    def check_for_interrupts(self) -> bool:
        # example input [(1, 'h'), (10, 'e'), (20, 'l'), (25, 'l'), (100, 'o')]
        if self.ps["Intr_On"]:
            for index, interrupt in enumerate(self.input_tokens):
                if not self.tokens_handled[index] and interrupt[0] <= self.instuct_number:
                    self.IO = interrupt[1]
                    self.ps["Intr_Req"] = True
                    self.ps["Intr_On"] = False
                    self.tokens_handled[index] = True
                    print(interrupt, self.instuct_number, self.data_path.pc)
                    self.exec_instruction(
                        [
                            lambda: self.data_path.signal_ret_wr(Selector.RET_STACK_PC),
                            lambda: self.signal_latch_pc(Selector.PC_IMMEDIATE, 1),
                            lambda: self.data_path.signal_latch_i(Selector.I_INC),
                        ]
                    )
                    break
        return False

    def exec_instruction(self, operations: list[typing.Callable], comment="") -> None:
        self.instuct_number += 1
        for operation in operations:
            operation()
        self.__print__(comment)

    def command_cycle(self):
        self.decode_and_execute_instruction()
        self.check_for_interrupts()
        self.signal_latch_pc(Selector.PC_INC)

    def call_arithmetic_operation(self, arithmetic_operation):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_alu_operation(arithmetic_operation),
                lambda: self.data_path.signal_latch_top(Selector.TOP_ALU),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
            ]
        )

    def call_push(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_data_wr(),
                lambda: self.data_path.signal_latch_sp(Selector.SP_INC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TOP),
                lambda: self.data_path.signal_latch_top(Selector.TOP_IMMEDIATE, memory_cell["arg"]),
            ]
        )

    def call_drop(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
            ]
        )

    def call_omit(self, memory_cell):
        self.out_buffer += chr(self.data_path.next)
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
            ]
        )

    def call_read(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_data_wr(),
                lambda: self.data_path.signal_latch_sp(Selector.SP_INC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TOP),
                lambda: self.data_path.signal_latch_top(Selector.TOP_IMMEDIATE, ord(self.IO)),
            ]
        )

    def call_swap(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_temp(Selector.TEMP_TOP),
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TEMP),
            ]
        )

    def call_over(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_data_wr(),
                lambda: self.data_path.signal_latch_temp(Selector.TEMP_TOP),
                lambda: self.data_path.signal_latch_sp(Selector.SP_INC),
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TEMP),
            ]
        )

    def call_dup(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_data_wr(),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TOP),
                lambda: self.data_path.signal_latch_sp(Selector.SP_INC),
            ]
        )

    def call_load(self, memory_cell):
        self.exec_instruction([lambda: self.data_path.signal_latch_top(Selector.TOP_MEM)])

    def call_store(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_mem_write(),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
            ]
        )

    def call_pop(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_temp(Selector.TEMP_TOP),
                lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM),
                lambda: self.data_path.signal_ret_wr(Selector.RET_STACK_OUT),
                lambda: self.data_path.signal_latch_i(Selector.I_INC),
            ]
        )

    def call_rpop(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_latch_i(Selector.I_DEC),
                lambda: self.data_path.signal_latch_temp(Selector.TEMP_RETURN),
                lambda: self.data_path.signal_data_wr(),
                lambda: self.data_path.signal_latch_next(Selector.NEXT_TOP),
                lambda: self.data_path.signal_latch_sp(Selector.SP_INC),
                lambda: self.data_path.signal_latch_top(Selector.TOP_TEMP),
            ]
        )

    def call_zjmp(self, memory_cell):
        if self.data_path.top == 0:
            self.exec_instruction(
                [
                    lambda: self.signal_latch_pc(Selector.PC_IMMEDIATE, memory_cell["arg"]),
                    lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                    lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                ]
            )
            self.exec_instruction([lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM)])
        else:
            self.exec_instruction(
                [
                    lambda: self.data_path.signal_latch_top(Selector.TOP_NEXT),
                    lambda: self.data_path.signal_latch_sp(Selector.SP_DEC),
                ]
            )
            self.exec_instruction([lambda: self.data_path.signal_latch_next(Selector.NEXT_MEM)])

    def call_jmp(self, memory_cell):
        self.exec_instruction([lambda: self.signal_latch_pc(Selector.PC_IMMEDIATE, memory_cell["arg"])])

    def call_call(self, memory_cell):
        self.exec_instruction(
            [
                lambda: self.data_path.signal_ret_wr(Selector.RET_STACK_PC),
                lambda: self.data_path.signal_latch_i(Selector.I_INC),
                lambda: self.signal_latch_pc(Selector.PC_IMMEDIATE, memory_cell["arg"]),
            ]
        )

    def call_di(self, memory_cell):
        self.exec_instruction([lambda: self.signal_latch_ps(False)])

    def call_ei(self, memory_cell):
        self.exec_instruction([lambda: self.signal_latch_ps(True)])

    def call_ret(self, memory_cell):
        self.exec_instruction(
            [lambda: self.data_path.signal_latch_i(Selector.I_DEC), lambda: self.signal_latch_pc(Selector.PC_RET)]
        )

    def call_halt(self, memory_cell):
        print(self.out_buffer)
        raise StopIteration

    def decode_and_execute_instruction(self) -> None:
        memory_cell = self.program_memory[self.data_path.pc]
        command = memory_cell["command"]
        arithmetic_operation = opcode_to_alu_opcode(command)
        if arithmetic_operation is not None:
            self.call_arithmetic_operation(arithmetic_operation)
            return
        operations_map = {
            OpcodeType.PUSH: lambda mem: self.call_push(mem),
            OpcodeType.DROP: lambda mem: self.call_drop(mem),
            OpcodeType.OMIT: lambda mem: self.call_omit(mem),
            OpcodeType.READ: lambda mem: self.call_read(mem),
            OpcodeType.SWAP: lambda mem: self.call_swap(mem),
            OpcodeType.OVER: lambda mem: self.call_over(mem),
            OpcodeType.DUP: lambda mem: self.call_dup(mem),
            OpcodeType.LOAD: lambda mem: self.call_load(mem),
            OpcodeType.STORE: lambda mem: self.call_store(mem),
            OpcodeType.POP: lambda mem: self.call_pop(mem),
            OpcodeType.RPOP: lambda mem: self.call_rpop(mem),
            OpcodeType.ZJMP: lambda mem: self.call_zjmp(mem),
            OpcodeType.JMP: lambda mem: self.call_jmp(mem),
            OpcodeType.CALL: lambda mem: self.call_call(mem),
            OpcodeType.DI: lambda mem: self.call_di(mem),
            OpcodeType.EI: lambda mem: self.call_ei(mem),
            OpcodeType.RET: lambda mem: self.call_ret(mem),
            OpcodeType.HALT: lambda mem: self.call_halt(mem),
        }
        operation = operations_map.get(command)
        if operation:
            operation(memory_cell)
        else:
            raise ValueError

    def __print__(self, comment: str) -> None:
        tos_memory = self.data_path.data_stack[self.data_path.sp - 1: self.data_path.sp - 4: -1]
        tos = [self.data_path.top, self.data_path.next, *tos_memory]
        ret_tos = self.data_path.return_stack[self.data_path.i - 1: self.data_path.i - 4: -1]
        state_repr = (
            "exec_instruction: {:4} | PC: {:3} | PS_REQ {:1} | PS_STATE: {:1} | SP: {:3} | I: {:3} | "
            "TEMP: {:7} | DATA_MEMORY[TOP]: {:7} | TOS : {} | RETURN_TOS : {}"
        ).format(
            self.instuct_number,
            self.data_path.pc,
            self.ps["Intr_Req"],
            self.ps["Intr_On"],
            self.data_path.sp,
            self.data_path.i,
            self.data_path.temp,
            self.data_path.memory[self.data_path.top] if self.data_path.top < self.data_path.memory_size else "?",
            str(tos),
            str(ret_tos),
        )
        logger.info(state_repr + " " + comment)
        # f.write(state_repr + " " + comment + "\n")


def simulation(code: list, limit: int, input_tokens: list[tuple]):
    data_path = DataPath(15000, 15000, 15000)
    control_unit = ControlUnit(data_path, 15000, input_tokens)
    control_unit.fill_command_memory(code)
    while control_unit.instuct_number < limit:
        try:
            control_unit.command_cycle()
        except StopIteration:
            break
    return [control_unit.out_buffer, control_unit.instuct_number]


def main(code_path: str, token_path: str | None) -> None:
    input_tokens = []
    if token_path is not None:
        with open(token_path, encoding="utf-8") as file:
            input_text = file.read()
            input_tokens = eval(input_text)
    code = read_code(code_path)
    output, instr_num = simulation(
        code,
        limit=17000,
        input_tokens=input_tokens,
    )
    print(f"Output: {output}\nInstruction number: {instr_num - 1}")


if __name__ == "__main__":
    assert 2 <= len(sys.argv) <= 3, "Wrong arguments: machine.py <code_file> [<input_file>]"
    if len(sys.argv) == 3:
        _, code_file, input_file = sys.argv
    else:
        _, code_file = sys.argv
        input_file = None
    main(code_file, input_file)
