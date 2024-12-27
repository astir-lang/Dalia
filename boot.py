from asm import ASM
from ast_1 import Parser, Lexer  # type: ignore

# from asm import ASM # type: ignore


def run():
    file = open("boot.dal").read()
    lexer = Lexer(file)
    lexer.lex_all()
    print(f"{lexer.results}\n\n")
    parser = Parser(lexer.results)
    parser.parse_all()

    print(f"{parser.results}\n\n")
    code_generator = ASM(parser.results, parser.symbol_tables)
    code_generator.generate_all()
    print(f"{code_generator.lines}")
    open("boot.s", "w+").write("\n".join(code_generator.lines))


if __name__ == "__main__":
    run()
