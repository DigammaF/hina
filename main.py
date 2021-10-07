
from enum import Enum
import string

class HinaException(Exception): pass
class BadCodeInputException(HinaException): pass
class InternalException(HinaException): pass

class TokenSymbol(Enum):

    number = 0
    string = 1
    open_brace = 2
    close_brace = 3
    open_p = 4
    close_p = 5
    op = 6
    letters = 7
    point = 8
    comment = 9

OPS: [str] = [
    "++", "--", "+=", "-=", "*=", "/=", "//", "<=", ">=", "!=",
    "%", "+", "-", "*", "/", "&", "|",
]

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

    def __init__(self, symbol: TokenSymbol, raw: str, context: TokenContext):

        self.symbol = symbol
        self.raw = raw
        self.context = context

    def __str__(self):
        return f"({self.raw}){self.symbol}"

class TokenizeContext:

    def __init__(self, file_name: str):

        self.file_name = file_name

def tokenize(txt: str, context: TokenizeContext) -> [Token]:

    assert txt.endswith(" "), "Text must end with a space"
    tokens = []
    lines = txt.split("\n")
    chars = tuple(txt)
    line_num = 1
    reader = 0

    while True:
        match chars[reader:]:
            case tuple():
                break

            case (" " | "\t", *_):
                reader += 1

            case ("\n", *_):
                line_num += 1
                reader += 1

            case (letter, *_) if letter in string.ascii_letters:

                offset = 1

                while True:
                    match chars[reader + offset:]:
                        case (char, *_) if char in string.digits + "._":
                            offset += 1

                        case _:
                            break

                tokens.append(
                    Token(
                        symbol=TokenSymbol.letters,
                        raw=chars[reader:offset],
                        context=TokenContext(
                            raw_line=lines[line_num - 1],
                            line_num=line_num,
                            file_name=context.file_name,
                            start=reader,
                            length=offset,
                        ),
                    )
                )

                reader += offset + 1

            case (digit, *_) if digit in string.digits:

                offset = 1

                while True:
                    match chars[reader + offset:]:
                        case (char, *_) if char in string.digits + "._":
                            offset += 1

                        case _:
                            break

                tokens.append(
                    Token(
                        symbol=TokenSymbol.number,
                        raw=chars[reader:offset],
                        context=TokenContext(
                            raw_line=lines[line_num - 1],
                            line_num=line_num,
                            file_name=context.file_name,
                            start=reader,
                            length=offset,
                        ),
                    )
                )

                reader += offset + 1

            case (char, *_):

                for search_distance in range(max(len(w) for w in OPS), 0, -1):
                    match chars[reader:]:
                        case l if len(l) == search_distance and (op := "".join(l) in OPS):
                            tokens.append(
                                Token(
                                    symbol=TokenSymbol.op,
                                    raw=chars[reader:search_distance],
                                    context=TokenContext(
                                        raw_line=lines[line_num - 1],
                                        line_num=line_num,
                                        file_name=context.file_name,
                                        start=reader,
                                        length=search_distance,
                                    ),
                                )
                            )

                            reader += search_distance + 1
                            break

                else:
                    raise BadCodeInputException("\n".join(
                        tuple(TokenContext(
                            raw_line=lines[line_num - 1],
                            line_num=line_num,
                            file_name=context.file_name,
                            start=reader,
                            length=1,
                        ).lines) + (
                            f"'{char}' doesn't belong to the lexical set of Hina",
                        )
                    ))

    return tokens

def main():

    file_name = "test.hina"

    with open(file_name, "r", encoding="utf-8") as f:
        txt = f.read() + " "

    context = TokenizeContext(file_name=file_name)
    tokens = tokenize(txt, context)
    print(", ".join(str(t) for t in tokens))

if __name__ == "__main__":
    main()
