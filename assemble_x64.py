def assemble():
    four = []
    with open('innercode', 'r') as file:
        stmts = list(line.replace('\n', '') for line in file.readlines())

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
        "j==": ("compare", "JE"),
        "%": ("eval", ""),
        "^": ("eval", ""),
        "=": ("assign", "mov"),
        "+": ("eval", "add"),
        "-": ("eval", "sub"),
        "*": ("eval", "mul"),
        "/": ("eval", "div"),
        ">=": ("eval", "GE"),
        "<=": ("eval", "LE"),
        ">": ("eval", "GT"),
        "<": ("eval", "LT"),
        "==": ("eval", ""),
        "!=": ("eval", "ne"),
        "||": ("eval", "and"),
        "&&": ("eval", "or"),
        "!": ("eval", "not"),
        "j": ("jump", "jmp"),
        "ret": ("return", "RET"),
        "arg": ("proced", "arg"),
        "call": ("proced", "call"),
    }

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
    # t.sort()
    four_in = {}
    m = 1
    for i in t:
        four_in[i] = "CODE" + str(m)
        m += 1
    # print(four_in)

    tab = "        "
    result += [("extern printf, scanf")]
    result += [("global main")]
    result += [("main:")]
    result += [tab + "enter 100, 0"]
    inx = "[rbp-"

    for i in range(len(four)):
        if i in four_in:
            result += [four_in[i] + ":"]
        if rules[four[i][0]][0] == "compare":
            # result += [tab + "mov eax," + (four[i][1]) + ""]
            if four[i - 1][0] == '>' or four[i - 1][0] == '<' or four[i - 1][0] == '>=' \
            or four[i - 1][0] == '<=' or four[i - 1][0] == '=='or four[i - 1][0] == '!=':
                if isinstance(four[i - 1][1], int):
                    result += [tab + "mov eax," + str(four[i - 1][1])]
                else:
                    result += [tab + "mov eax," + inx + str(4 * data.index(four[i - 1][1]) + 4) + "]"]
                if isinstance(four[i - 1][2], int):
                    result += [tab + "mov ebx," + str(four[i - 1][2])]
                else:
                    result += [tab + "mov ebx," + inx + str(4 * data.index(four[i - 1][2]) + 4) + "]"]
                result += [tab + "cmp eax,ebx"]
                if four[i - 1][0] == '>':
                    result += [tab + "" + "ja" + " " + four_in[four[i][3] - 1]]
                elif four[i - 1][0] == '<':
                    result += [tab + "" + "jb" + " " + four_in[four[i][3] - 1]]
                elif four[i - 1][0] == '>=':
                    result += [tab + "" + "jae" + " " + four_in[four[i][3] - 1]]
                elif four[i - 1][0] == '<=':
                    result += [tab + "" + "jbe" + " " + four_in[four[i][3] - 1]]
                elif four[i - 1][0] == '==':
                    result += [tab + "" + "je" + " " + four_in[four[i][3] - 1]]
                elif four[i - 1][0] == '!=':
                    result += [tab + "" + "jne" + " " + four_in[four[i][3] - 1]]
            else:
                if isinstance(four[i][2], int):
                    result += [tab + "mov eax," + str(four[i][2])]
                else:
                    result += [tab + "mov eax," + inx + str(4 * data.index(four[i][2]) + 4) + "]"]
                result += [tab + "cmp eax,1"]
                result += [tab + "" + "je" + " " + four_in[four[i][3] - 1]]
            result += [""]
        elif rules[four[i][0]][0] == "assign":
            if isinstance(four[i][1], int) or isinstance(four[i][1], float):
                data[data.index(-1)] = four[i][3]
                result += [tab + "mov eax," + str(four[i][1])]
                result += [tab + "mov " + inx + str(4 * data.index(four[i][3]) + 4) + "],eax"]
            else:
                data[data.index(-1)] = four[i][3]
                result += [tab + "mov eax," + inx + str(4 * data.index(four[i][1]) + 4) + "]"]
                result += [tab + "mov " + inx + str(4 * data.index(four[i][3]) + 4) + "],eax"]
        elif rules[four[i][0]][0] == "eval":
            if isinstance(four[i][1], int) or isinstance(four[i][1], float):
                result += [tab + "mov eax," + str(four[i][1])]
            elif four[i][1] != '_':
                result += [tab + "mov eax," + inx + str(4 * data.index(four[i][1]) + 4) + "]"]
            if isinstance(four[i][2], int) or isinstance(four[i][2], float):
                result += [tab + "mov ebx," + str(four[i][2])]
            elif four[i][2] != '_':
                result += [tab + "mov ebx," + inx + str(4 * data.index(four[i][2]) + 4) + "]"]
            if four[i][0] == "+" or four[i][0] == "-":
                result += [tab + rules[four[i][0]][1] + " eax,ebx"]
            elif four[i][0] == "*":
                result += [tab + "mul ebx"]
            elif four[i][0] == "/":
                result += [tab + "div ebx"]
            elif four[i][0] == "%":
                result += [tab + "div ebx"]
                result += [tab + "mov eax,edx"]
            elif four[i][0] == "^":
                result += [tab + "times " + str(four[i][2]) + " mul eax"]
            elif four[i][0] == ">" or four[i][0] == "<" or four[i][0] == ">=" or \
                four[i][0] == "<=" or four[i][0] == "==" or four[i][0] == "!=":
                pass
            elif four[i][0] == "&&" or four[i][0] == "||":
                result += [tab + rules[four[i][0]][1] + " eax,ebx"]
            elif four[i][0] == "!":
                result += [tab + rules[four[i][0]][1] + " eax"]
            else:
                result += ["----eval符未定义---"]
            data[data.index(-1)] = four[i][3]
            # result += [tab + "mov eax," + (four[i][3]) + ""]
            result += [tab + "mov " + inx + str(4 * data.index(four[i][3]) + 4) + "],eax"]

        elif rules[four[i][0]][0] == "jump":
            result += [tab + "jmp " + str(four_in[four[i][3] - 1])]
            result += [""]

        elif rules[four[i][0]][0] == "return":
            result += [tab + "leave"]
            result += [tab + "ret"]

        elif rules[four[i][0]][0] == "proced":
            if four[i][0] == "arg":
                result += [tab + "sub rsp, 8"]
                result += [tab + "mov rsi," + inx + str(4 * data.index(four[i][3]) + 4) + "]"]
            if four[i][0] == "call" and four[i][3] == "output":
                result += [tab + "mov rdi, out_format"]
                result += [tab + "xor rax, rax"]
                result += [tab + "call printf"]
                result += [tab + "xor rax, rax"]
                result += [tab + "add rsp, 8"]
            elif four[i][0] == "call" and four[i][3] == "input":
                result += [tab + 'mov rsi, number']
                result += [tab + 'mov rdi, in_format']
                result += [tab + "xor rax, rax"]
                result += [tab + 'call scanf']
                result += [tab + 'mov rbx, [number]']
                result += [tab + 'add rsp, 8']

    result += [""]
    result += ["section .data"]
    result += [tab + 'out_format: db "%#d", 10, 0']
    result += [tab + 'in_format: db "%d", 0']

    result += ["section .bss"]
    result += [tab + 'number resb 4']
    with open('assembly.s', 'w') as output_file:
        for line in result:
            output_file.write(f'{line}\n')
