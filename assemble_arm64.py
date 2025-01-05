import re

# Initialize variable tracking
variables = {}
next_offset = 0

def parse_intermediate_code():
    """
    Parses the intermediate code from the 'innercode' file and converts it to a list of tuples.
    Handles array declarations and array operations.
    """
    with open('innercode', 'r') as file:
        stmts = [line.strip() for line in file.readlines()]

    four = []
    array_pattern = re.compile(r'(\w+)\[(\d+)\]')  # Pattern to match array declarations like a[40]
    # Handle array declarations (they are at the beginning)
    while stmts:
        first_line = stmts[0]
        array_match = array_pattern.match(first_line)
        if array_match:
            array_name, array_size = array_match.groups()
            array_size = int(array_size)
            variables[array_name] = {'offset': next_offset, 'size': array_size}
            globals()['next_offset'] += array_size  # Update global next_offset
            stmts.pop(0)  # Remove the array declaration line
        else:
            break  # No more array declarations

    for stmt in stmts:
        ops = stmt.split()
        # Convert numeric values to integers
        ops = [int(op) if op.isdigit() else op for op in ops]

        if len(ops) == 0:
            print('Ignoring unrecognizable statement', stmt)
            continue

        # Detect array assignments like a[t3] = i
        array_operand_re = re.compile(r'(\w+)\[(\w+)]')
        array_assign_match = array_operand_re.match(ops[1])
        if array_assign_match:
            assert ops[2] == '='
            array_name, index = array_assign_match.groups()
            four.append(('astore', array_name, index, ops[3]))
            continue

        array_access_match = array_operand_re.match(ops[3]) if len(ops) >= 4 and isinstance(ops[3], str) else None
        if array_access_match:
            array_name, index = array_assign_match.groups()
            four.append(('aload', array_name, index, ops[1]))
            continue

        # Handle other specific intermediate code patterns
        if ops[1] == "if":
            four.append(("j==", ops[2], 1, ops[4]))
        elif ops[1] == "goto":
            four.append(('j', '_', '_', ops[2]))
        elif ops[1] == "arg":
            four.append(('arg', '_', '_', ops[2]))
        elif ops[1] == "call":
            four.append(('call', '_', '_', ops[2]))
        elif ops[1] == "return":
            four.append(('ret', '_', '_', ops[2]))
        elif len(ops) > 3 and ops[3] == '!':
            four.append((ops[3], ops[4], '_', ops[1]))
        else:
            if isinstance(ops[1], str) and ops[1].startswith('t'):
                four.append((ops[4], ops[3], ops[5], ops[1]))
            else:
                four.append((ops[2], ops[3], '_', ops[1]))

    return four

def get_var_offset(var):
    """
    Gets the memory offset for a variable, allocating a new offset if the variable is not yet tracked.
    """
    global next_offset
    if var not in variables:
        variables[var] = next_offset
        next_offset += 4
    return variables[var]

def generate_labels(four, rules):
    """
    Generates labels for conditional and jump statements within the intermediate code.
    """
    label_indices = set()
    for i, line in enumerate(four):
        if rules[line[0]][0] in ["compare", "jump"]:
            label_indices.add(i)
            label_indices.add(line[3] - 1)

    label_map = {index: f".L{label_id}" for label_id, index in enumerate(sorted(label_indices), start=1)}
    return label_map

def generate_assembly(rules, four, label_map):
    """
    Generates ARM assembly code from the intermediate representation.
    """
    tab = "    "
    result = []

    # Prologue
    result.append(".global _start")
    result.append("_start:")
    result.append(f"{tab}stp x29, x30, [sp, #-16]!")  # Save frame pointer and link register
    result.append(f"{tab}mov x29, sp")  # Set up frame pointer

    for i, instr in enumerate(four):
        # Add label if this instruction is the target of a jump
        if i in label_map:
            result.append(f"{label_map[i]}:")

        opcode_type = rules[instr[0]][0]

        if opcode_type == "compare":
            generate_compare_assembly(result, instr, four, label_map, i, tab)
        elif opcode_type == "assign":
            generate_assign_assembly(result, instr, tab)
        elif opcode_type == "aload":
            generate_aload_assembly(result, instr, tab)
        elif opcode_type == "astore":
            generate_astore_assembly(result, instr, tab)
        elif opcode_type == "jump":
            result.append(f"{tab}b {label_map[instr[3] - 1]}")
        elif opcode_type == "return":
            generate_return_assembly(result, instr, tab)

    # Epilogue
    result.append("")
    return result

def generate_aload_assembly(result, instr, tab):
    """
    Generates assembly code for loading a value from an array.
    instr: ('aload', array_name, index, destination)
    """
    _, array_name, index, dest = instr
    array_info = variables[array_name]
    base_offset = array_info['offset']
    element_size = 4  # Assuming 4 bytes per element

    # Load base address of the array into x1
    result.append(f"{tab}add x1, x29, #{-base_offset}")  # Base address = x29 - base_offset

    # Load index into w2
    if isinstance(index, int):
        result.append(f"{tab}mov w2, #{index}")
    else:
        index_offset = get_var_offset(index)
        result.append(f"{tab}ldr w2, [x29, #-{index_offset}]")

    # Compute address: x1 + w2 * 4
    result.append(f"{tab}add x3, x1, x2, LSL #2")  # x2 = w2 zero-extended

    # Load value from [x3] into w0
    result.append(f"{tab}ldr w0, [x3]")

    # Store the loaded value into the destination variable
    dest_offset = get_var_offset(dest)
    result.append(f"{tab}str w0, [x29, #-{dest_offset}]")

def generate_astore_assembly(result, instr, tab):
    """
    Generates assembly code for storing a value into an array.
    instr: ('astore', array_name, index, value)
    """
    _, array_name, index, value = instr
    array_info = variables[array_name]
    base_offset = array_info['offset']
    element_size = 4  # Assuming 4 bytes per element

    # Load base address of the array into x1
    result.append(f"{tab}add x1, x29, #{-base_offset}")  # Base address = x29 - base_offset

    # Load index into w2
    if isinstance(index, int):
        result.append(f"{tab}mov w2, #{index}")
    else:
        index_offset = get_var_offset(index)
        result.append(f"{tab}ldr w2, [x29, #-{index_offset}]")

    # Compute address: x1 + w2 * 4
    result.append(f"{tab}add x3, x1, x2, LSL #2")  # x2 = w2 zero-extended

    # Load value to store into w0
    if isinstance(value, int):
        result.append(f"{tab}mov w0, #{value}")
    else:
        value_offset = get_var_offset(value)
        result.append(f"{tab}ldr w0, [x29, #-{value_offset}]")

    # Store the value into [x3]
    result.append(f"{tab}str w0, [x3]")

def generate_compare_assembly(result, instr, four, label_map, i, tab):
    """
    Generates assembly code for comparison statements.
    """
    prev_instr = four[i - 1]
    if prev_instr[0] in ['>', '<', '>=', '<=', '==', '!=']:
        # Load first operand
        if isinstance(prev_instr[1], int):
            result.append(f"{tab}mov w0, #{prev_instr[1]}")
        else:
            offset = get_var_offset(prev_instr[1])
            result.append(f"{tab}ldr w0, [x29, #-{offset}]")

        # Load second operand
        if isinstance(prev_instr[2], int):
            result.append(f"{tab}mov w1, #{prev_instr[2]}")
        else:
            offset = get_var_offset(prev_instr[2])
            result.append(f"{tab}ldr w1, [x29, #-{offset}]")

        # Perform comparison
        result.append(f"{tab}cmp w0, w1")

        # Generate branch instruction
        cond_map = {'>': 'gt', '<': 'lt', '>=': 'ge', '<=': 'le', '==': 'eq', '!=': 'ne'}
        cond = cond_map[prev_instr[0]]
        result.append(f"{tab}b.{cond} {label_map[instr[3] - 1]}")

def generate_assign_assembly(result, instr, tab):
    """
    Generates assembly code for assignment statements.
    """
    # Load source value
    if isinstance(instr[1], int):
        result.append(f"{tab}mov w0, #{instr[1]}")
    else:
        offset = get_var_offset(instr[1])
        result.append(f"{tab}ldr w0, [x29, #-{offset}]")

    # Store value in destination
    dest_offset = get_var_offset(instr[3])
    result.append(f"{tab}str w0, [x29, #-{dest_offset}]")

def generate_return_assembly(result, instr, tab):
    """
    Generates assembly code for return statements.
    """
    # Load return value
    if isinstance(instr[3], int):
        result.append(f"{tab}mov w0, #{instr[3]}")
    else:
        offset = get_var_offset(instr[3])
        result.append(f"{tab}ldr w0, [x29, #-{offset}]")

    # Function epilogue
    result.append(f"{tab}mov sp, x29")
    result.append(f"{tab}ldp x29, x30, [sp], #16")
    result.append(f"{tab}ret")

def write_assembly_to_file(assembly_code, filename='assembly.s'):
    """
    Writes the generated assembly code to a file.
    """
    with open(filename, 'w') as output_file:
        for line in assembly_code:
            output_file.write(f"{line}\n")

def assemble():
    # Rules for translating intermediate code to assembly
    rules = {
        "j==": ("compare", "b.eq"),
        "%": ("eval", ""),
        "^": ("eval", ""),
        "=": ("assign", "mov"),
        "+": ("eval", "add"),
        "-": ("eval", "sub"),
        "*": ("eval", "mul"),
        "/": ("eval", "sdiv"),
        ">=": ("eval", "ge"),
        "<=": ("eval", "le"),
        ">": ("eval", "gt"),
        "<": ("eval", "lt"),
        "==": ("eval", "eq"),
        "!=": ("eval", "ne"),
        "||": ("eval", "orr"),
        "&&": ("eval", "and"),
        "!": ("eval", "mvn"),
        "j": ("jump", "b"),
        "ret": ("return", "ret"),
        "arg": ("proced", "arg"),
        "call": ("proced", "bl"),
        "aload": ("aload", ""),
        "astore": ("astore", "")
    }

    # Parse, process, and generate the assembly code
    four = parse_intermediate_code()
    label_map = generate_labels(four, rules)
    assembly_code = generate_assembly(rules, four, label_map)
    write_assembly_to_file(assembly_code)


if __name__ == '__main__':
    assemble()