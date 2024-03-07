# coding=utf-8
def dprint(str, debug=0):
    if debug == 1:
        print(str)


class Content(object):
    def __init__(self, entry={}, data_type=0):
        self.truelist = []
        self.falselist = []
        self.nextlist = []
        self.continuelist = []
        self.breaklist = []
        self.addr = ''
        self.code = ''
        self.entry = entry
        self.data_type = data_type


class Node(object):
    def __init__(self, lexme, value, data_type):
        self.lexme = lexme
        self.value = value
        self.parameter_list = []
        self.array_dimension = -1
        self.is_constant = 0
        self.num_params = 0
        self.data_type = data_type

    def __getitem__(self, item):
        return self.item

    def __setitem__(self, key, value):
        self.key = value

    def check_parameter_list(self, params: list, m: int):
        if m != self.num_params:
            raise Exception('Number of parameters and arguments do not match')
        i = 0
        for param in self.parameter_list:
            if param != params[i]:
                raise Exception('Parameter and argument types do not match')
            i += 1
        return 1

    def fill_parameter_list(self, params: list, m: int):
        self.parameter_list = params
        self.num_params = m


class SymbolTable(object):
    def __init__(self, parent=-1):
        self.symboltable = {}
        self.parent = parent

    def insert(self, lexme, value, data_type):
        entry = self.search(lexme)
        if entry and entry.is_constant == 1:
            return entry
        elif entry:
            return None
        else:
            entry = Node(lexme, value, data_type)
            self.symboltable[lexme] = entry
        return entry

    def search(self, lexme):
        if lexme in self.symboltable:
            return self.symboltable[lexme]
        else:
            return None

    def __getitem__(self, item):
        if item == 'parent':
            return self.parent
        if item in self.symboltable:
            return self.symboltable[item]
        else:
            return None


class ScopeTable(object):
    def __init__(self, size=10):
        self.symboltable_list = [SymbolTable()] * size
        self.table_index = 0
        self.current_scope = 0

    def __repr__(self):
        return 'ScopeTable with table_index = {} and current_scope = {}'.format(self.table_index, self.current_scope)

    def create_new_scope(self):
        dprint('create new scope with tableIndex={} and parent = {}'.format(self.table_index, self.current_scope))
        self.table_index += 1
        self.symboltable_list[self.table_index] = SymbolTable(parent=self.current_scope)
        self.current_scope = self.table_index

    def exit_scope(self):
        if self.symboltable_list[self.current_scope].parent == -1:
            self.table_index = 0
            self.current_scope = 0
        else:
            self.current_scope = self.symboltable_list[self.current_scope].parent
            self.table_index = self.current_scope

    def recursive_search(self, lexme):
        idx = self.current_scope
        entry = None
        while idx != -1:
            entry = self.symboltable_list[idx].search(lexme)
            dprint('search lexme={} in {}'.format(lexme, self.symboltable_list[idx]))
            dprint('result = {}'.format(entry))
            if entry:
                break
            idx = self.symboltable_list[idx].parent
        return entry
