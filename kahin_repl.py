#!/usr/bin/env python3
"""
Kahin REPL - interaktif kabuk.

Satırları Kahin→Python'a çevirip InteractiveConsole üzerinden çalıştırır.
Çok satırlı bloklar (eger/tanimla/eslestir) otomatik devam ister.
Çıkış: cik() veya Ctrl-D.
"""
import sys
import code

from kahin_lexer import KahinLexer
import kahin_hata

CIKIS = {'cik', 'cik()', 'exit', 'exit()', 'quit', 'quit()'}


class KahinKonsol(code.InteractiveConsole):
    def __init__(self):
        super().__init__(locals={'__name__': '__main__'})
        self.lexer = KahinLexer()

    def runsource(self, source, filename="<kahin>", symbol="single"):
        if source.strip() in CIKIS:
            raise SystemExit

        try:
            python_kod = self.lexer.tokens_to_code(self.lexer.tokenize(source))
        except SyntaxError as e:
            # tokenize yarım blokta "EOF" der → daha fazla girdi iste
            if 'EOF' in str(e) or 'multi-line' in str(e):
                return True
            self.showsyntaxerror(filename)
            return False

        return super().runsource(python_kod, filename, symbol)

    def showtraceback(self):
        # Ham Python traceback yerine Türkçe tek satır
        print(kahin_hata.turkcelestir(*sys.exc_info()), file=sys.stderr)


def baslat(surum="16.0"):
    sys.ps1 = "kahin> "
    sys.ps2 = "...... "
    konsol = KahinKonsol()
    banner = (
        f"Kahin v{surum} REPL — Türkçe Programlama Dili\n"
        f"Çıkış: cik() veya Ctrl-D"
    )
    try:
        konsol.interact(banner=banner, exitmsg="")
    except SystemExit:
        pass
    print("Görüşürüz.")


if __name__ == "__main__":
    baslat()
