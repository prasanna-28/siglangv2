# coding=utf-8
from sigLex import tokens, constant_table
from ply import yacc
from symboltable import *
from irAST import *
import sys


def pget(p, idx):
    try:
        return p[idx]
    except IndexError:
        return None


def error_msg(msg):
    raise Exception('[Error]: {}'.format(msg))


def gencode(x: str):
    global nextinstr
    intermediate.append(x)
    nextinstr += 1


def gencode_rel(lhs: Content, arg1: Content, arg2: Content, op: str):
    lhs.data_type = arg1.data_type
    lhs.truelist = [nextinstr]
    lhs.falselist = [nextinstr+1]
    gencode('if ' + str(arg1.addr) + op + str(arg2.addr) + ' goto _')
    gencode('goto _')


def gencode_math(lhs: Content, arg1: Content, arg2: Content, op: str):
    global temp_var_number
    lhs.addr = 't' + str(temp_var_number)
    expr = str(lhs.addr) + ' = ' + str(arg1.addr) + op + str(arg2.addr)
    lhs.code = arg1.code + arg2.code + expr
    temp_var_number += 1
    gencode(expr)


def backpatch(v1: list, number: int):
    for idx in v1:
        intermediate[idx] = intermediate[idx].replace('_', str(number))


def merge(v1: list, v2: list):
    return v1 + v2


def type_check(left: int, right: int, flag: int):
    if left != right:
        if flag == 0:
            error_msg('Type mismatch in arithmetic expression')
        elif flag == 1:
            error_msg('Type mismatch in assignment expression')
        elif flag == 2:
            error_msg('Type mismatch in logical expression')


precedence = (
    ('left', 'COMMA'),
    ('right', 'ASSIGN'),
    ('left', 'LOGICAL_OR'),
    ('left', 'LOGICAL_AND'),
    ('left', 'EQ', 'NOT_EQ'),
    ('left', 'LS', 'GR', 'LS_EQ', 'GR_EQ'),
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('right', 'NOT'),
    ('nonassoc', 'ELSE', 'LOWER_THAN_ELSE')
)


def p_starter(p):
    '''starter : starter builder
               | builder'''


def p_builder(p):
    '''builder : function
               | declaration'''


def p_function(p):
    '''function : type identifier seen_identifier LP argument_list seen_argument_list RP compound_stmt'''
    global is_func
    is_func = 0


def p_seen_identifier(p):
    '''seen_identifier :'''
    global func_type, is_declaration
    func_type = current_dtype
    is_declaration = 0
    scopes.create_new_scope()
    dprint('current scope = {}'.format(scopes.current_scope))
    gencode(p[-1].lexme + ':')


def p_seen_argument_list(p):
    '''seen_argument_list :'''
    global param_idx, is_declaration, is_func, flag
    is_declaration = 0
    p[-4].fill_parameter_list(param_list, param_idx)
    param_idx = 0
    is_func = 1
    flag = 1


def p_type(p):
    '''type : data_type pointer
            | data_type'''
    global is_declaration
    is_declaration = 1


def p_data_type(p):
    '''data_type : sign_specifier type_specifier
                 | type_specifier'''


def p_pointer(p):
    '''pointer : MUL pointer
               | MUL '''


def p_sign_specifier(p):
    '''sign_specifier : SIGNED
                      | UNSIGNED'''


def p_type_specifier(p):
    '''type_specifier : INT
                      | SHORT INT
                      | SHORT
                      | LONG
                      | LONG_LONG
                      | LONG INT
                      | LONG_LONG INT
                      | CHAR
                      | FLOAT
                      | VOID
                      | CHAR_STAR'''
    global current_dtype
    if p[1] == 'int':
        current_dtype = 0
    elif p[1] == 'short':
        current_dtype = 1
    elif p[1] == 'long':
        current_dtype = 2
    elif p[1] == 'long long':
        current_dtype = 3
    elif p[1] == 'char':
        current_dtype = 4
    elif p[1] == 'float':
        current_dtype = 5
    elif p[1] == 'void':
        current_dtype = 6
    elif p[1] == 'char*':
        current_dtype = 7


def p_argument_list(p):
    '''argument_list : arguments
                     | '''


def p_arguments(p):
    '''arguments : arguments COMMA arg
                 | arg'''


def p_arg(p):
    '''arg : type identifier'''
    global param_idx, param_list
    param_list[param_idx] = p[2].data_type
    param_idx += 1
    gencode('arg ' + p[2].lexme)


def p_stmt(p):
    '''stmt : compound_stmt
            | single_stmt'''
    p[0] = p[1]


def p_compound_stmt(p):
    '''compound_stmt : BLP seen_BLP statements BRP '''
    scopes.exit_scope()
    p[0] = p[3]


def p_seen_BLP(p):
    '''seen_BLP :'''
    global flag
    if flag != 0:
        scopes.create_new_scope()
    else:
        flag = 0


def p_statements(p):
    '''statements : statements M stmt
                  | '''
    p[0] = Content()
    try:
        if pget(p, 3):
            backpatch(p[1].nextlist, p[2])
            p[0].nextlist = p[3].nextlist
            p[0].breaklist = merge(p[1].breaklist, p[3].breaklist)
            p[0].continuelist = merge(p[1].continuelist, p[3].continuelist)
    except IndexError:
        pass


def p_single_stmt(p):
    '''single_stmt : if_block seen_control
                   | for_block seen_control
                   | while_block seen_control
                   | declaration
                   | function_call SEMICOLON
                   | RETURN SEMICOLON
                   | prntf_call SEMICOLON
                   | RETURN sub_expr SEMICOLON
                   | CONTINUE SEMICOLON
                   | BREAK SEMICOLON '''
    if p[1] == 'return':
        if is_func != 0:
            if (pget(p, 2) == ';' and func_type != 6) or (pget(p, 2)!= ';' and func_type != pget(p, 2).data_type):
                error_msg('return type mismacth')
        else:
            error_msg('not in function')
    elif p[1] == 'continue':
        if is_loop == 0:
            error_msg('illegal use of continue')
        p[0] = Content()
        p[0].continuelist = [nextinstr]
        gencode('goto _')
    elif p[1] == 'break':
        if is_loop == 0:
            error_msg('illegal use of break')
        p[0] = Content()
        p[0].breaklist = [nextinstr]
        gencode('goto _')
    elif pget(p, 2) == 'control':
        p[0] = p[1]
        backpatch(p[0].nextlist, nextinstr)
    else:
        p[0] = Content()


def p_seen_control(p):
    '''seen_control :'''
    p[0] = 'control'


def p_expression_stmt(p):
    '''expression_stmt : expression SEMICOLON
                       | SEMICOLON '''
    p[0] = Content()
    if pget(p, 2) == ';':
        p[0].truelist = p[1].truelist
        p[0].falselist = p[1].falselist



def p_for_block(p):
    '''for_block : FOR LP expression_stmt M expression_stmt M expression RP before_loop N M stmt after_loop'''
    backpatch(p[5].truelist, p[11])
    backpatch(p[12].nextlist, p[6])
    backpatch(p[12].continuelist, p[6])
    backpatch(p[10].nextlist, p[4])
    p[0] = Content()
    p[0].nextlist = merge(p[5].falselist, p[12].breaklist)
    gencode('goto ' + str(p[6]))


def p_before_loop(p):
    '''before_loop :'''
    global is_loop
    is_loop = 1


def p_after_loop(p):
    '''after_loop :'''
    global is_loop
    is_loop = 0


def p_if_block(p):
    '''if_block :  IF LP expression RP M stmt ELSE N M stmt
                | IF LP expression RP M stmt'''
    if pget(p, 7) == 'goon':
        backpatch(p[3].truelist, p[5])
        backpatch(p[3].falselist, p[9])
        p[0] = Content()
        tmp = merge(p[6].nextlist, p[8].nextlist)
        p[0].nextlist = merge(tmp, p[10].nextlist)
        p[0].breaklist = merge(p[10].breaklist, p[6].breaklist)
        p[0].continuelist = merge(p[10].continuelist, p[6].continuelist)
    else:
        backpatch(p[3].truelist, p[5])
        p[0] = Content()
        p[0].nextlist = merge(p[3].falselist, p[6].nextlist)
        p[0].breaklist = p[6].breaklist
        p[0].continuelist = p[6].continuelist


def p_while_block(p):
    '''while_block : WHILE M LP expression RP M before_loop stmt after_loop'''
    backpatch(p[8].nextlist, p[2])
    backpatch(p[4].truelist, p[6])
    backpatch(p[8].continuelist, p[2])
    p[0] = Content()
    p[0].nextlist = merge(p[4].falselist, p[8].breaklist)
    gencode('goto ' + str(p[2]))


def p_declaration(p):
    '''declaration : type declaration_list SEMICOLON
                   | declaration_list SEMICOLON
                   | unary_expr'''
    if pget(p, 3) == ';':
        global is_declaration
        is_declaration = 0


def p_declaration_list(p):
    '''declaration_list : declaration_list COMMA sub_decl
                        | sub_decl'''


def p_sub_decl(p):
    '''sub_decl : assignment_expr
                | identifier
                | array_access'''


def p_expression(p):
    '''expression : expression COMMA sub_expr
                  | sub_expr'''
    p[0] = Content()
    if pget(p, 2) == ',':
        p[0].truelist = p[3].truelist
        p[0].falselist = p[3].falselist
    else:
        p[0].truelist = p[1].truelist
        p[0].falselist = p[1].falselist


def p_sub_expr(p):
    '''sub_expr : sub_expr GR sub_expr
                | sub_expr LS sub_expr
                | sub_expr EQ sub_expr
                | sub_expr NOT_EQ sub_expr
                | sub_expr GR_EQ sub_expr
                | sub_expr LS_EQ sub_expr
                | sub_expr LOGICAL_AND M sub_expr
                | sub_expr LOGICAL_OR M sub_expr
                | NOT sub_expr
                | arithmetic_expr seen_arith
                | assignment_expr
                | unary_expr'''
    p[0] = Content()
    if pget(p, 2) in ['<', '>', '==', '!=', '>=', '<=']:
        type_check(p[1].data_type, p[3].data_type, 2)
        gencode_rel(p[0], p[1], p[3], ' ' + p[2] + ' ')
    elif pget(p, 2) == '&&':
        type_check(p[1].data_type, p[4].data_type, 2)
        p[0].datatype = p[1].data_type
        backpatch(p[1].truelist, p[3])
        p[0].truelist = p[4].truelist
        p[0].falselist = merge(p[1].falselist, p[4].falselist)
    elif pget(p, 2) == '||':
        type_check(p[1].data_type, p[4].data_type, 2)
        p[0].datatype = p[1].data_type
        backpatch(p[1].falselist, p[3])
        p[0].truelist = merge(p[1].truelist, p[4].truelist)
        p[0].falselist = p[4].falselist
    elif p[1] == '!':
        p[0].data_type = p[2].data_type
        p[0].truelist = p[1].falselist
        p[0].falselist = p[1].truelist
    else:
        p[0].data_type = p[1].data_type
        if pget(p, 2):
            p[0].addr = p[1].addr


def p_seen_arith(p):
    '''seen_arith :'''
    p[0] = 'seen'


def p_assignment_expr(p):
    '''assignment_expr : lhs assign arithmetic_expr seen_arch
                       | lhs assign array_access seen_array
                       | lhs assign function_call seen_func_call
                       | lhs assign unary_expr seen_unary'''
    p[0] = Content()
    global rhs
    if pget(p, 4) in ['arch', 'array', 'unary']:
        type_check(p[1].entry.data_type, p[3].data_type, 1)
        p[0].data_type = p[3].data_type
        p[0].code = str(p[1].entry.lexme) + str(p[2]) + str(p[3].addr)
        gencode(p[0].code)
        rhs = 0
    elif pget(p, 4) == 'func_call':
        type_check(p[1].entry.data_type, p[3], 1)
        p[0].data_type = p[3]


def p_seen_arch(p):
    '''seen_arch :'''
    p[0] = 'arch'


def p_seen_array(p):
    '''seen_array :'''
    p[0] = 'array'


def p_seen_func_call(p):
    '''seen_func_call :'''
    p[0] = 'func_call'


def p_seen_unary(p):
    '''seen_unary :'''
    p[0] == 'unary'


def p_unary_expr(p):
    '''unary_expr : identifier INCREMENT
                  | identifier DECREMENT
                  | DECREMENT identifier
                  | INCREMENT identifier'''
    p[0] = Content()
    if p[1] in ['++', '--']:
        p[0].data_type = p[2].data_type
        p[0].code = p[1] + p[2].lexme
    else:
        p[0].data_type = p[1].data_type
        p[0].code = p[1].lexme + p[2]
    gencode(p[0].code)


def p_lhs(p):
    '''lhs : identifier seen_id
           | array_access'''
    p[0] = Content()
    if pget(p, 2) == 'seen_identifier':
        p[0].entry = p[1]
    else:
        p[0].code = p[1].code


def p_seen_id(p):
    '''seen_id :'''
    p[0] = 'seen_identifier'


def p_identifier(p):
    '''identifier : IDENTIFIER'''
    if is_declaration != 0 and rhs == 0:
        p[1] = scopes.symboltable_list[scopes.current_scope].insert(p[1], 2147483647, current_dtype)
        if not p[1]:
            error_msg('redeclaration of variable')
    else:
        print(p[0],p[1])
        p[1] = scopes.recursive_search(p[1])
        if not p[1]:
            error_msg('varible bot declared')
    p[0] = p[1]


def p_assign(p):
    '''assign : ASSIGN
              | ADD_ASSIGN
              | SUB_ASSIGN
              | DIV_ASSIGN
              | MOD_ASSIGN
              | MUL_ASSIGN'''
    global rhs
    rhs = 1
    p[0] = ' ' + p[1] + ' '


def p_arithmetic_expr(p):
    '''arithmetic_expr : arithmetic_expr ADD arithmetic_expr
                       | arithmetic_expr SUB arithmetic_expr
                       | arithmetic_expr MUL arithmetic_expr
                       | arithmetic_expr DIV arithmetic_expr
                       | arithmetic_expr MOD arithmetic_expr
                       | LP arithmetic_expr RP
                       | SUB arithmetic_expr
                       | identifier
                       | constant'''
    p[0] = Content()
    if pget(p, 2) in ['+', '-', '*', '/', '%']:
        type_check(p[1].data_type, p[3].data_type, 0)
        p[0].data_type = p[1].data_type
        gencode_math(p[0], p[1], p[3], ' ' + p[2] + ' ')
    elif p[1] == '(':
        p[0].data_type = p[2].data_type
        p[0].addr = p[2].addr
        p[0].code = p[2].code
    elif p[1] == '-':
        global temp_var_number
        p[0].data_type = p[2].data_type
        p[0].addr = 't' + str(temp_var_number)
        expr = p[0].addr + ' = minus ' + p[2].addr
        p[0].code = p[2].code + expr
        gencode(expr)
        temp_var_number += 1
    else:
        p[0].data_type = p[1].data_type
        if p[1].is_constant == 1:
            p[0].addr = p[1].value
        else:
            p[0].addr = p[1].lexme


def p_constant(p):
    '''constant : DEC_CONSTANT
                | HEX_CONSTANT
                | CHAR_CONSTANT
                | FLOAT_CONSTANT'''
    p[1] = constant_table[p[1]]
    p[1].is_constant = 1
    p[0] = p[1]


def p_array_access(p):
    '''array_access : identifier MLP array_index MRP '''
    if is_declaration == 1:
        if p[3].value <= 0:
            error_msg('size of array invalid')
        elif p[3].is_constant == 1:
            p[1].array_dimension = p[3].value
    elif p[3].is_constant == 1:
        if p[3].value > p[1].array_dimension:
            error_msg('array index out of bound')
        elif p[3].value < 0:
            error_msg('array index cannot be negative')
    p[0] = Content()
    p[0].data_type = p[1].data_type
    if p[3].is_constant == 1:
        p[0].code = p[1].lexme + '[' + str(p[3].value) + ']'
    else:
        p[0].code = p[1].lexme + '[' + p[3].lexme + ']'
    p[0].entry = p[1]


def p_array_index(p):
    '''array_index : constant
                   | identifier'''
    p[0] = p[1]


def p_function_call(p):
    '''function_call : identifier LP parameter_list RP
                     | identifier LP RP '''
    global param_idx, param_list
    p[1].check_parameter_list(param_list, param_idx)
    p[0] = p[1].data_type
    param_idx = 0
    gencode('call ' + p[1].lexme)

def p_prntf_call(p):
    '''prntf_call : PRNTF LP STRING RP
                   | PRNTF LP STRING COMMA parameter_list RP'''
    if pget(p, 4) == ',':
        gencode('print ' + p[3] + ', ' + ', '.join(map(str, param_list[:param_idx])))
    else:
        gencode('print ' + p[3])


def p_parameter_list(p):
    '''parameter_list : parameter_list COMMA parameter
                      | parameter '''


def p_parameter(p):
    '''parameter : sub_expr
                 | STRING'''
    global param_list, param_idx
    if isinstance(p[1], Content):
        param_list[param_idx] = p[1].data_type
        gencode('param ' + str(p[1].addr))
    else:
        param_list[param_idx] = constant_table[p[1]].data_type
        gencode('param ' + p[1])
    param_idx += 1


def p_M(p):
    'M : '
    p[0] = nextinstr


def p_N(p):
    'N : '
    p[0] = Content()
    p[0].nextlist = [nextinstr]
    gencode('goto _')


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python sigParse.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    print('filename = {}, generate intermediate code, result:'.format(filename))
    current_dtype, is_declaration, is_loop, is_func, param_idx, flag, rhs, func_type, nextinstr, temp_var_number = \
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    param_list = [0] * 10
    intermediate = []
    scopes = ScopeTable()
    parser = yacc.yacc()
    with open(filename, 'r') as code:
        parser.parse(code.read(), debug=0)
    ir = intermediate
    print(ir)
    interpreter = Interpreter(ir)