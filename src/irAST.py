class Interpreter:
    def __init__(self, CODE: list = []):
        self.code = CODE
        self.pointer = 0
        self.vars = {}
        for i, v in enumerate(self.code):
            if v == "main:":
                self.pointer = i + 1

        self.vm()

    def vm(self):
        while self.pointer < len(self.code):
            context = self.eval(self.code[self.pointer])
            self.pointer = context

    def eval(self, line):
        currLine = self.ir(line)
        if currLine[0] == "S":
            self.setVar(currLine)
            return self.pointer + 1
        elif currLine[0] == "I":
            return self.evalConditional(currLine)
        elif currLine[0] == "G":
            return int(currLine[2])
        elif currLine[0] == "P":
            self.printVar(currLine)
            return self.pointer + 1
        elif currLine[0] == "A":
            self.calcVar(currLine)
            return self.pointer + 1

    def evalConditional(self, cond):
        var1 = cond[2]
        op = cond[3]
        var2 = cond[4]
        goto = int(cond[6])

        if var1.isdigit():
            var1 = int(var1)
        elif '.' in var1:
            var1 = float(var1)
        else:
            var1 = self.vars[var1]

        if var2.isdigit():
            var2 = int(var2)
        elif '.' in var2:
            var2 = float(var2)
        else:
            var2 = self.vars[var2]

        if op == '<' and var1 < var2:
            return goto
        elif op == '>' and var1 > var2:
            return goto
        elif op == '==' and var1 == var2:
            return goto
        elif op == '!=' and var1 != var2:
            return goto
        elif op == '<=' and var1 <= var2:
            return goto
        elif op == '>=' and var1 >= var2:
            return goto
        else:
            return self.pointer + 1

    def setVar(self, line):
        var = line[1]
        if '"' in line[3] or "'" in line[3]:
            self.vars[var] = line[3][1:len(line[3])-1]
        elif line[3].isdigit():
            self.vars[var] = int(line[3])
        elif '.' in line[3]:
            self.vars[var] = float(line[3])
        elif line[3] in self.vars:
            self.vars[var] = self.vars[line[3]]
        else:
            print(f"error? setVar: db info {line}")

    def calcVar(self, line):
        delta = line[1]
        A = line[3]
        op = line[4]
        B = line[5]

        if B.isdigit():
            B = int(B)
        elif '.' in B:
            B = float(B)
        elif B in self.vars:
            B = self.vars[B]
        else:
            print("error calcvar B")
            return

        if A.isdigit():
            A = int(A)
        elif '.' in A:
            A = float(A)
        elif A in self.vars:
            A = self.vars[A]
        else:
            print("error calcvar A")
            return

        if op == '+':
            self.vars[delta] = A + B
        elif op == '-':
            self.vars[delta] = A - B
        elif op == '*':
            self.vars[delta] = A * B
        elif op == '/':
            if B == 0:
                print("error: division by zero")
                return
            self.vars[delta] = A / B
        elif op == '%':
            if B == 0:
                print("error: division by zero")
                return
            self.vars[delta] = A % B
        elif op == '++':
            self.vars[delta] = A + 1
        elif op == '--':
            self.vars[delta] = A - 1

    def printVar(self, line):
        output = ' '.join(line[1:])
        if '"' in output or "'" in output:
            print(output[1:len(output)-1])
        elif ',' in output:
            vars = output.split(',')
            formatted_output = ""
            for var in vars:
                var = var.strip()
                if var in self.vars:
                    formatted_output += str(self.vars[var]) + " "
                else:
                    formatted_output += var + " "
            print(formatted_output)
        else:
            if output in self.vars:
                print(self.vars[output])
            else:
                print(output)

    def ir(self, expr):
        res = []
        expr = expr.split(' ')

        if len(expr) == 1 and expr[0] != "main:":
            if expr[0][-2:] == '++':
                res.append('A')
                res.append(expr[0][:-2])
                res.append('=')
                res.append(expr[0][:-2])
                res.append('+')
                res.append('1')
            elif expr[0][-2:] == '--':
                res.append('A')
                res.append(expr[0][:-2])
                res.append('=')
                res.append(expr[0][:-2])
                res.append('-')
                res.append('1')
            return res

        elif expr[0] == 'if':
            res.append('I')
            for i in expr:
                res.append(i)
            return res

        elif expr[1] == "=" and len(expr) == 3:
            res.append("S")
            res.append(expr[0])
            res.append('=')
            res.append(' '.join(expr[2:]))
            return res

        elif expr[1] == "=" and len(expr) > 3:
            res.append('A')
            for i in expr:
                res.append(i)
            return res

        elif expr[0] == "print":
            res.append('P')
            res.append(' '.join(expr[1:]))
            return res

        elif expr[0] == "goto":
            res.append("G")
            for i in expr:
                res.append(i)
            return res

# Example usage