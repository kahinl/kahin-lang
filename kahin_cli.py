#!/usr/bin/env python3
"""
KAHİN CLI - AST hattı runner

kahin <dosya.kahin>          Çalıştır
kahin <dosya.kahin> --debug  Çevrilmiş Python kodunu göster
kahin --yardim               Yardım
kahin --versiyon             Versiyon

AST hattını kullanır (kahin_lexer + kahin_ast): optimize + yeni sözdizimi
(aralık 1..10, pipe |>, constant folding) otomatik aktif.
"""
import sys
import os
import ast

SURUM = "16.0"


def _proje_yolu():
    return os.path.dirname(os.path.abspath(__file__))


def _yollari_ekle():
    """Proje kökü + kahin_lib (Türkçe stdlib) sys.path'e."""
    proje = _proje_yolu()
    sys.path.insert(0, proje)
    sys.path.insert(0, os.path.join(proje, "kahin_lib"))


def yardim():
    print(f"Kahin v{SURUM} - Türkçe Programlama Dili")
    print()
    print("Kullanım:")
    print("  kahin                        İnteraktif kabuk (REPL)")
    print("  kahin <dosya.kahin>          Kahin dosyasını çalıştır")
    print("  kahin <dosya.py>             Saf Python dosyasını çalıştır")
    print("  kahin <dosya> --debug        Çevrilen/çalışan kodu göster")
    print("  kahin <dosya> --cache-yok    Bytecode cache atla")
    print("  kahin --yardim               Bu mesaj")
    print("  kahin --versiyon             Versiyon bilgisi")
    print()
    print("Yeni sözdizimi:")
    print("  1..10    → range(1, 10)      aralık")
    print("  1..=10   → range(1, 11)      içeren aralık")
    print("  x |> f   → f(x)              pipe (zincirlenebilir)")


def calistir(dosya_yolu, debug=False, cache_yok=False):
    if not os.path.exists(dosya_yolu):
        print(f"Hata: dosya bulunamadı: {dosya_yolu}", file=sys.stderr)
        return 1
    if os.path.isdir(dosya_yolu):
        print(f"Hata: {dosya_yolu} bir dizin", file=sys.stderr)
        return 1

    with open(dosya_yolu, 'r', encoding='utf-8') as f:
        kaynak = f.read()

    _yollari_ekle()

    saf_python = dosya_yolu.endswith('.py')

    if saf_python:
        # Normal Python dosyasi: parser atla, dogrudan derle
        try:
            kod = compile(kaynak, dosya_yolu, 'exec')
        except SyntaxError as e:
            import kahin_hata
            print(f"Sözdizimi hatası ({dosya_yolu}:{e.lineno}): {kahin_hata.syntax_turkcelestir(e.msg)}", file=sys.stderr)
            return 1
        if debug:
            print("# --- saf Python (cevirisiz) ---")
            print(kaynak)
            print("# --- çıktı ---")
    else:
        kod = None
        cache = None
        if not cache_yok and not debug:
            from kahin_cache import KahinCache
            cache = KahinCache()
            kod = cache.load(dosya_yolu)

        if kod is None:
            from kahin_ast import KahinParser

            parser = KahinParser(optimize=True)
            try:
                tree = parser.parse(kaynak, dosya_adi=dosya_yolu)
            except SyntaxError as e:
                import kahin_hata
                print(f"Sözdizimi hatası ({dosya_yolu}:{e.lineno}): {kahin_hata.syntax_turkcelestir(e.msg)}", file=sys.stderr)
                return 1

            if debug:
                print("# --- çevrilen Python ---")
                print(ast.unparse(tree))
                print("# --- çıktı ---")

            try:
                kod = compile(tree, dosya_yolu, 'exec')
            except SyntaxError as e:
                import kahin_hata
                print(f"Derleme hatası ({dosya_yolu}:{e.lineno}): {kahin_hata.syntax_turkcelestir(e.msg)}", file=sys.stderr)
                return 1

            if cache is not None:
                cache.save(dosya_yolu, kod)

    # Programın kendi __name__ == "__main__" bloğu çalışsın
    ns = {'__name__': '__main__', '__file__': dosya_yolu}
    try:
        exec(kod, ns)
    except Exception:
        import kahin_hata
        if debug:
            import traceback
            print("Çalışma zamanı hatası:", file=sys.stderr)
            traceback.print_exc()
        else:
            print(kahin_hata.turkcelestir(*sys.exc_info()), file=sys.stderr)
        return 1
    return 0


def _repl():
    _yollari_ekle()
    import kahin_repl
    kahin_repl.baslat(SURUM)
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    if "--yardim" in argv or "--help" in argv:
        yardim()
        return 0
    if "--versiyon" in argv or "--version" in argv:
        print(f"Kahin v{SURUM}")
        return 0

    debug = "--debug" in argv
    cache_yok = "--cache-yok" in argv
    dosya = next((a for a in argv if not a.startswith("--")), None)

    # Dosya yoksa veya --repl ile: interaktif kabuk
    if dosya is None or "--repl" in argv:
        return _repl()

    return calistir(dosya, debug=debug, cache_yok=cache_yok)


if __name__ == "__main__":
    sys.exit(main())
