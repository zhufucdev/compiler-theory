def assemble():
    with open('Innercode', 'r') as file:
        stmts = list(line.replace('\n', '') for line in file.readlines())
    four = []

    # Parse intermediate code
    for stmt in stmts:
        ops = stmt.split()
        for i in range(len(ops)):
            try:
                ops[i] = int(ops[i])
            except:
                pass
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
        elif len(ops)>3 and ops[3] == '!':
            four.append((ops[3], ops[4], '_', ops[1]))
        else:
            if (ops[1][0] == 't'):
                four.append((ops[4], ops[3], ops[5], ops[1]))
            else:
                four.append((ops[2], ops[3], '_', ops[1]))

    result = []
    t = []
    data = [-1] * 100

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
    }

    # Generate labels
    n = 0
    for line in four:
        if rules[line[0]][0] == "compare":
            t.append(n)
            t.append(line[3] - 1)
        elif rules[line[0]][0] == "jump":
            t.append(n)
            t.append(line[3] - 1)
        n = n + 1
    t = list(set(t))
    four_in = {}
    m = 1
    for i in t:
        four_in[i] = ".L" + str(m)
        m += 1

    tab = "    "
    result += [".global _start"]
    result += ["_start:"]
    result += [tab + "stp x29, x30, [sp, #-16]!"]  # Save frame pointer and link register
    result += [tab + "mov x29, sp"]  # Set up frame pointer

    for i in range(len(four)):
        if i in four_in:
            result += [four_in[i] + ":"]

        if rules[four[i][0]][0] == "compare":
            if four[i - 1][0] in ['>', '<', '>=', '<=', '==', '!=']:
                if isinstance(four[i - 1][1], int):
                    result += [tab + f"mov w0, #{four[i - 1][1]}"]
                else:
                    result += [tab + f"ldr w0, [x29, #{-4 * data.index(four[i - 1][1])}]"]

                if isinstance(four[i - 1][2], int):
                    result += [tab + f"mov w1, #{four[i - 1][2]}"]
                else:
                    result += [tab + f"ldr w1, [x29, #{-4 * data.index(four[i - 1][2])}]"]

                result += [tab + "cmp w0, w1"]

                cond = {'>': 'gt', '<': 'lt', '>=': 'ge', '<=': 'le',
                    '==': 'eq', '!=': 'ne'}[four[i - 1][0]]
                result += [tab + f"b.{cond} {four_in[four[i][3] - 1]}"]

        elif rules[four[i][0]][0] == "assign":
            if isinstance(four[i][1], int):
                result += [tab + f"mov w0, #{four[i][1]}"]
                data[data.index(-1)] = four[i][3]
                result += [tab + f"str w0, [x29, #{-4 * data.index(four[i][3])}]"]
            else:
                data[data.index(-1)] = four[i][3]
                result += [tab + f"ldr w0, [x29, #{-4 * data.index(four[i][1])}]"]
                result += [tab + f"str w0, [x29, #{-4 * data.index(four[i][3])}]"]

        elif rules[four[i][0]][0] == "jump":
            result += [tab + f"b {four_in[four[i][3] - 1]}"]

        elif rules[four[i][0]][0] == "return":
            if isinstance(four[i][3], int):
                result += [tab + f"mov w0, #{four[i][3]}"]
            else:
                result += [tab + f"ldr w0, [x29, #{-4 * data.index(four[i][3])}]"]
            result += [tab + "ldp x29, x30, [sp], #16"]
            result += [tab + "ret"]

    result += [""]
    with open('assembly.s', 'w') as output_file:
        for line in result:
            output_file.write(f'{line}\n')
