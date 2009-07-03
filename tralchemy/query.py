# query.py
#
# Copyright (C) 2009, Codethink Ltd.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#
# Author:
#       John Carr <john.carr@unrouted.co.uk>

from types import GeneratorType
from opcode import HAVE_ARGUMENT, opname, cmp_op

import dis

def walk_generator(generator):
    dis.dis(generator.gi_code)
    code = map(ord, generator.gi_code.co_code)
    size = len(code)
    cursor = 0

    while cursor < size:
        ip = cursor
        opcode = code[cursor]
        cursor += 1

        if opcode >= HAVE_ARGUMENT:
            lo = code[cursor]
            hi = code[cursor+1]
            cursor += 2
            offset = lo + (hi << 8)
        else:
            offset = 0

        yield ip, opname[opcode], offset


class Node(object):
    def __repr__(self):
        return str(self)

class Constant(object):

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return str(self.val)

class Identifier(Node):
    def __init__(self, ident):
        self.ident = ident

    def get_symbol(self):
        if self.ident in locals():
            return self.locals()[self.ident]
        if self.ident in globals():
            return self.globals()[self.ident]
        return None

    def __str__(self):
        symbol = self.get_symbol()
        if symbol:
            return symbol.uri
        return self.ident

class Attribute(Identifier):
    def __init__(self, ident, attr):
        self.ident = ident
        self.attr = attr

    def get_symbol(self):
        sym = self.ident.get_symbol()
        return getattr(sym, self.attr)

    def __str__(self):
        sym = self.get_symbol()
        if sym:
            return sym.uri
        return "%s.%s" % (self.ident, self.attr)

class Select(Identifier):
    pass

class Comparison(Node):
    def __init__(self, a, b, type):
        self.a = a
        self.b = b
        self.type = type

    def __str__(self):
        return "%s %s %s" % (self.a, self.type, self.b)

class And(Comparison):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.type = "and"
    def __str__(self):
        return "(%s) %s (%s)" % (self.a, self.type, self.b)

class Or(Comparison):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.type = "or"
    def __str__(self):
        return "(%s) %s (%s)" % (self.a, self.type, self.b)

class Query(object):

    def __init__(self, generator):
        if not isinstance(generator, GeneratorType):
            raise ArgumentException("Must be passed a generator...")

        # Shortcuts to save typing
        co_consts = generator.gi_code.co_consts
        co_names = generator.gi_code.co_names
        co_varnames = generator.gi_code.co_varnames

        print co_names
        print co_varnames

        stack = []

        ignore_pop = 0

        current_cond = None

        for ip, op, offset in walk_generator(generator):
            print ip, op, offset

            if op == "BUILD_TUPLE":
                terms = [str(stack.pop()) for i in range(offset)]
                terms.reverse()
                stack.append("[%s]" % ", ".join(terms))
            elif op == "COMPARE_OP":
                term2, term1 = stack.pop(), stack.pop()
                stack.append(Comparison(term1, term2, cmp_op[offset]))
            elif op == "FOR_ITER":
                stack.append("FOR")
                first_loop = False
            elif op == "JUMP_ABSOLUTE":
                pass
            elif op == "JUMP_IF_FALSE":
                x = And(stack.pop(), True)
                if current_cond:
                    current_cond.b = x
                else:
                    stack.append(x)
                current_cond = x
                ignore_pop += 1
            elif op == "JUMP_IF_TRUE":
                x = Or(stack.pop(), False)
                if current_cond:
                    current_cond.b = x
                else:
                    stack.append(x)
                current_cond = x
                ignore_pop += 1
            elif op == "LOAD_ATTR":
                stack.append(Attribute(stack.pop(), co_names[offset]))
            elif op == "LOAD_CONST":
                stack.append(Constant(co_consts[offset]))
            elif op == "LOAD_FAST":
                stack.append(Identifier(co_varnames[offset]))
            elif op == "LOAD_GLOBAL":
                stack.append(co_names[offset])
            elif op == "POP_TOP":
                if ignore_pop:
                    ignore_pop -= 1
                    continue
                stack.pop()
                #FIXME: Here is where we turn whatever expression we just built
                # into an actual condition
            elif op == "POP_BLOCK":
                assert stack.pop() == "BLOCK"
            elif op == "SETUP_LOOP":
                # start of a generator
                # initially we'll just assert that there is ONLY one
                # but maybe we can next them??
                stack.append("BLOCK")
            elif op == "STORE_FAST":
                #stack.append(co_varnames[offset])
                stack.pop()
            elif op == "YIELD_VALUE":
                # Whatever we just built is our return value
                retval = stack.pop()
                break
            elif op == "RETURN_VALUE":
                # End of generator code
                stack.pop()
            else:
                raise AssertError("Unexpected python opcode %s" % op)
            print stack

        print "ANSWER IS", retval

Store = []

if __name__ == "__main__":
    Contact = object

    q = Query((Contact.firstname, Contact.surname) for Contact in Store if Contact.location == "UK" and Contact.test == 1 or Contact.badger == 3)

