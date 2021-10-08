
import string
import collections

from enum import Enum

class HinaException(Exception): pass
class BadCodeInputException(HinaException): pass
class InternalException(HinaException): pass

class LexicalUnit(Enum):

    number = 0
    string = 1
    open_brace = 2
    close_brace = 3
    open_p = 4
    close_p = 5
    op = 6
    identifier = 7
    point = 8
    comment = 9
    r_string = 101

    k_and = 10
    k_or = 11
    k_macro = 12
    k_function = 13
    k_class = 14
    k_while = 15
    k_for = 16
    k_if = 17
    k_else = 18
    k_elif = 19
    k_use = 20
    k_as = 21
    k_true = 22
    k_false = 23
    k_var = 24
    k_const = 25
    k_not = 26
    k_is = 27

KEYWORDS = {
    "and": LexicalUnit.k_and,
    "or": LexicalUnit.k_or,
    "macro": LexicalUnit.k_macro,
    "function": LexicalUnit.k_function,
    "class": LexicalUnit.k_class,
    "while": LexicalUnit.k_while,
    "for": LexicalUnit.k_for,
    "if": LexicalUnit.k_if,
    "else": LexicalUnit.k_else,
    "elif": LexicalUnit.k_elif,
    "use": LexicalUnit.k_use,
    "as": LexicalUnit.k_as,
    "true": LexicalUnit.k_true,
    "false": LexicalUnit.k_false,
    "var": LexicalUnit.k_var,
    "const": LexicalUnit.k_const,
    "not": LexicalUnit.k_not,
    "is": LexicalUnit.k_is,
}
OPS: [str] = [
    "//=",
    "++", "--", "+=", "-=", "*=", "/=", "//", "<=", ">=", "!=", "==",
    "%", "+", "-", "*", "/", "&", "=", "<", ">", ".", "{",
    "}", "(", ")", "^",
]
MAX_OP_LENGTH = max(len(w) for w in OPS)
SPECIAL_OPS: {str: LexicalUnit} = {
    ".": LexicalUnit.point,
    "{": LexicalUnit.open_brace,
    "}": LexicalUnit.close_brace,
    "(": LexicalUnit.open_p,
    ")": LexicalUnit.close_p,
}

class TokenContext:

    def __init__(self, raw_line: str, line_num: int, file_name: str, start: int, length: int):

        self.raw_line = raw_line
        self.line_num = line_num
        self.file_name = file_name
        self.start = start
        self.length = length

    @property
    def lines(self) -> [str]:

        yield f"{self.file_name} line {self.line_num}"
        yield f"{self.raw_line}"
        yield " "*self.start + "^"*self.length

class Token:

    def __init__(self, unit: LexicalUnit, raw: str, context: TokenContext):

        self.unit = unit
        self.raw = raw
        self.context = context

    def __str__(self):
        return f"({self.raw}){self.unit}"

TokenizeContext = collections.namedtuple("TokenizeContext", ["file_name"])

def tokenize(txt: str, context: TokenizeContext) -> [Token]:

    lines = txt.split("\n")
    chars = tuple(txt) + (0,)
    line_num = 1
    line_reader = 0
    reader = 0

    while True:
        match chars[reader:]:
            case (0,):
                break

            case (" " | "\t", *_):
                line_reader += 1
                reader += 1

            case ("\n", *_):
                line_num += 1
                line_reader = 0
                reader += 1

            case ("#", "#", *_):

                comment_start = TokenContext(
                    raw_line=lines[line_num],
                    line_num=line_num,
                    file_name=context.file_name,
                    start=line_reader,
                    length=2,
                )
                reader += 1

                while True:

                    reader += 1

                    match chars[reader:]:
                        case ("#", "#", *_):
                            reader += 2
                            break

                        case ("\n", *_):
                            line_num += 1
                            line_reader = 0

                        case (0,):
                            raise BadCodeInputException("\n".join(
                                tuple(
                                    comment_start.lines
                                ) + (
                                    f"long comment is opened but never closed",
                                )
                            ))

            case ('"', *_):

                string_start = TokenContext(
                    raw_line=lines[line_num - 1],
                    line_num=line_num,
                    file_name=context.file_name,
                    start=line_reader,
                    length=1,
                )
                offset = 0

                while True:

                    offset += 1

                    match chars[reader + offset:]:
                        case ('"', *_):

                            raw = "".join(chars[reader + 1:reader + offset])
                            yield Token(unit=LexicalUnit.r_string,
                                        raw=raw,
                                        context=TokenContext(
                                            file_name=context.file_name,
                                            length=len(raw) + 2,
                                            line_num=line_num,
                                            raw_line=lines[line_num - 1],
                                            start=reader,
                                        ),)
                            reader += offset + 1
                            line_reader += offset + 1
                            break

                        case (0 | "\n", *_):
                            raise BadCodeInputException("\n".join(
                                tuple(
                                    string_start.lines
                                ) + (
                                    f"string is opened but not closed",
                                )
                            ))

            case ("#", *_):

                while True:

                    reader += 1
                    line_reader += 1

                    match chars[reader:]:
                        case ("\n", *_):
                            line_num += 1
                            line_reader = 0
                            reader += 1
                            break

            case (letter, *_) if letter in string.ascii_letters:

                offset = 1

                while True:
                    match chars[reader + offset:]:
                        case (char, *_) if char in string.ascii_letters + string.digits + "_":
                            offset += 1

                        case _:
                            break

                raw_letters = "".join(chars[reader:reader + offset])
                token_context = TokenContext(
                    raw_line=lines[line_num - 1],
                    line_num=line_num,
                    file_name=context.file_name,
                    start=line_reader,
                    length=offset,
                )

                if raw_letters in KEYWORDS:
                    yield Token(unit=KEYWORDS[raw_letters], raw=raw_letters, context=token_context)

                else:
                    yield Token(unit=LexicalUnit.identifier, raw=raw_letters, context=token_context)

                reader += offset
                line_reader += offset

            case (digit, *_) if digit in string.digits:

                offset = 1

                while True:
                    match chars[reader + offset:]:
                        case (char, *_) if char in string.digits + "._":
                            offset += 1

                        case _:
                            break

                raw = "".join(chars[reader:reader + offset])
                token_context = TokenContext(
                    raw_line=lines[line_num - 1],
                    line_num=line_num,
                    file_name=context.file_name,
                    start=line_reader,
                    length=offset,
                )

                try:
                    float(raw)

                except ValueError:
                    raise BadCodeInputException("\n".join(
                        tuple(
                            token_context.lines
                        ) + (
                            f"cannot use '{raw}' as a number",
                        )
                    ))

                yield Token(unit=LexicalUnit.number, raw=raw, context=token_context)

                reader += offset
                line_reader += offset

            case (char, *_):

                for search_distance in range(MAX_OP_LENGTH, 0, -1):
                    match chars[reader:reader + search_distance]:
                        case l if len(l) == search_distance and (op := "".join(l)) in OPS:

                            token_context = TokenContext(
                                raw_line=lines[line_num - 1],
                                line_num=line_num,
                                file_name=context.file_name,
                                start=line_reader,
                                length=search_distance,
                            )

                            if op in SPECIAL_OPS:
                                yield Token(unit=SPECIAL_OPS[op], raw=op, context=token_context)

                            else:
                                yield Token(unit=LexicalUnit.op, raw=op, context=token_context)

                            reader += search_distance
                            line_reader += search_distance
                            break

                else:
                    raise BadCodeInputException("\n".join(
                        tuple(TokenContext(
                            raw_line=lines[line_num - 1],
                            line_num=line_num,
                            file_name=context.file_name,
                            start=line_reader,
                            length=1,
                        ).lines) + (
                            f"'{char}' doesn't belong to the lexical set of Hina",
                        )
                    ))

def main():

    file_name = "test.hina"

    with open(file_name, "r", encoding="utf-8") as f:
        txt = f.read()

    context = TokenizeContext(file_name=file_name)
    tokens = tuple(tokenize(txt, context))
    print(", ".join(str(t) for t in tokens))

if __name__ == "__main__":
    main()
