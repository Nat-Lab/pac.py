import string

from pyparsing import (
    Literal, White, Word, alphanums, CharsNotIn, Forward, Group, SkipTo,
    Optional, OneOrMore, ZeroOrMore, pythonStyleComment)


class Parser(object):
    left_bracket = Literal("{").suppress()
    right_bracket = Literal("}").suppress()
    semicolon = Literal(";").suppress()
    space = White().suppress()
    key = Word(alphanums + "_/")
    value = CharsNotIn("{};")
    value2 = CharsNotIn(";")
    location = CharsNotIn("{};," + string.whitespace)
    ifword = Literal("if")
    setword = Literal("set")
    modifier = Literal("=") | Literal("~*") | Literal("~") | Literal("^~")
    assignment = (key + Optional(space + value) + semicolon)
    setblock = (setword + OneOrMore(space + value2) + semicolon)
    block = Forward()
    ifblock = Forward()
    subblock = Forward()

    ifblock << (
        ifword
        + SkipTo('{')
        + left_bracket
        + subblock
        + right_bracket)

    subblock << ZeroOrMore(
        Group(assignment) | block | ifblock | setblock
    )

    block << Group(
        Group(key + Optional(space + modifier) + Optional(space + location))
        + left_bracket
        + Group(subblock)
        + right_bracket
    )

    script = OneOrMore(Group(assignment) | block).ignore(pythonStyleComment)

    def __init__(self, source):
        self.source = source

    def parse(self):
        return self.script.parseString(self.source)

    def as_list(self):
        return self.parse().asList()


class Dumper(object):
    def __init__(self, blocks, indentation=4):
        self.blocks = blocks
        self.indentation = indentation

    def __iter__(self, blocks=None, current_indent=0, spacer=' '):
        blocks = blocks or self.blocks
        for key, values in blocks:
            if current_indent:
                yield spacer
            indentation = spacer * current_indent
            if isinstance(key, list):
                yield indentation + spacer.join(key) + ' {'
                for parameter in values:
                    if isinstance(parameter[0], list):
                        dumped = self.__iter__(
                            [parameter],
                            current_indent + self.indentation)
                        for line in dumped:
                            yield line
                    else:
                        dumped = spacer.join(parameter) + ';'
                        yield spacer * (
                            current_indent + self.indentation) + dumped

                yield indentation + '}'
            else:
                yield spacer * current_indent + key + spacer + values + ';'

    def as_string(self):
        return '\n'.join(self)

    def to_file(self, out):
        for line in self:
            out.write(line+"\n")
        out.close()
        return out


def loads(source):
    return Parser(source).as_list()


def load(_file):
    return loads(_file.read())


def dumps(blocks, indentation=4):
    return Dumper(blocks, indentation).as_string()


def dump(blocks, _file, indentation=4):
    return Dumper(blocks, indentation).to_file(_file)
