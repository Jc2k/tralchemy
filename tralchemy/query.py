
from types import GeneratorType
from opcode import HAVE_ARGUMENT, opname, cmp_op

def walk_generator(generator):
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


class Query(object):

    def __init__(self, generator):
        if not isinstance(generator, GeneratorType):
            raise ArgumentException("Must be passed a generator...")

        # Shortcuts to save typing
        co_consts = generator.gi_code.co_consts
        co_names = generator.gi_code.co_names
        co_varnames = generator.gi_code.co_varnames

        # Python opcodes are stack based (yay)
        stack = []

        for ip, op, offset in walk_generator(generator):
            print ip, op, offset

            if op == "BUILD_TUPLE":
                terms = [str(stack.pop()) for i in range(offset)]
                terms.reverse()
                stack.append("[%s]" % ", ".join(terms))
            elif op == "COMPARE_OP":
                term2, term1 = stack.pop(), stack.pop()
                op = cmp_op[offset]
                stack.append("%s %s %s" % (term1, op, term2))
            elif op == "FOR_ITER":
                pass
            elif op == "JUMP_ABSOLUTE":
                pass
            elif op == "JUMP_IF_FALSE":
                pass
            elif op == "JUMP_IF_TRUE":
                pass
            elif op == "LOAD_ATTR":
                term = co_names[offset]
                stack[-1] += ("." + term)
            elif op == "LOAD_CONST":
                val = co_consts[offset]
                stack.append(val)
            elif op == "LOAD_FAST":
                stack.append(co_varnames[offset])
            elif op == "LOAD_GLOBAL":
                stack.append(co_names[offset])
            elif op == "POP_TOP":
                stack.pop()
                #FIXME: Here is where we turn whatever expression we just built
                # into an actual condition
            elif op == "POP_BLOCK":
                pass
            elif op == "SETUP_LOOP":
                # start of a generator
                # initially we'll just assert that there is ONLY one
                # but maybe we can next them??
            elif op == "STORE_FAST":
                pass
            elif op == "YIELD_VALUE":
                # Whatever we just built is our return value
                pass
            elif op == "RETURN_VALUE":
                # End of generator code
                pass
            else:
                raise AssertError("Unexpected python opcode %s" % op)

            print stack

if __name__ == "__main__":
    Store = ['a','b']
    Contact = object

    q = Query((Contact.firstname, Contact.surname) for Contact in Store if Contact.location == "UK" and Contact.test == 1)

