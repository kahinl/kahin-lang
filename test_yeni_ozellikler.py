#!/usr/bin/env python3
"""Yeni özellikler testi: AST folding + aralık/pipe sözdizimi."""

import ast
from kahin_ast import KahinParser
from kahin_lexer import KahinLexer

p = KahinParser(optimize=True)
lx = KahinLexer()
gecti = basarisiz = 0


def kontrol(ad, kosul):
    global gecti, basarisiz
    if kosul:
        gecti += 1
        print(f"  OK   {ad}")
    else:
        basarisiz += 1
        print(f"  FAIL {ad}")


def eval_kod(kod):
    t = p.parse(kod, mode='eval')
    return ast.literal_eval(t.body)


def calistir(kod):
    """Kahin kodu çalıştır, yerel namespace döndür."""
    tree = p.parse(kod)
    ns = {}
    exec(compile(tree, '<test>', 'exec'), ns)
    return ns


print("=== Compare folding ===")
kontrol("5 > 3 → True", eval_kod('5 > 3') is True)
kontrol("1 == 2 → False", eval_kod('1 == 2') is False)
kontrol("1 < 2 < 3 → True", eval_kod('1 < 2 < 3') is True)
kontrol("1 < 5 < 3 → False", eval_kod('1 < 5 < 3') is False)
kontrol('"a" == "a" → True', eval_kod('"a" == "a"') is True)

print("=== UnaryOp folding ===")
kontrol("not dogru → False", eval_kod('not dogru') is False)
kontrol("not yanlis → True", eval_kod('not yanlis') is True)
kontrol("-5 → -5", eval_kod('-5') == -5)

print("=== BoolOp folding ===")
p.transformer.optimizations_applied = 0
kontrol("dogru and x → x", ast.unparse(p.parse('z = dogru and x')) == 'z = x')
kontrol("yanlis and x → False", ast.unparse(p.parse('z = yanlis and x')) == 'z = False')
kontrol("dogru or x → True", ast.unparse(p.parse('z = dogru or x')) == 'z = True')
kontrol("yanlis or x → x", ast.unparse(p.parse('z = yanlis or x')) == 'z = x')

print("=== Aralık operatörü (önişleme) ===")
kontrol("1..10 → range(1, 10)", lx._on_isleme('1..10') == 'range(1, 10)')
kontrol("1..=10 → range(1, 10 + 1)", lx._on_isleme('1..=10') == 'range(1, 10 + 1)')

print("=== Aralık (uçtan uca exec) ===")
ns = calistir('toplam = 0\nher_biri_icin i icinde 1..5:\n    toplam = toplam + i')
kontrol("for 1..5 toplam = 10", ns['toplam'] == 10)
ns = calistir('toplam = 0\nher_biri_icin i icinde 1..=5:\n    toplam = toplam + i')
kontrol("for 1..=5 toplam = 15", ns['toplam'] == 15)

print("=== Pipe operatörü (önişleme) ===")
kontrol("x |> f → f(x)", lx._on_isleme('s = x |> f') == 's = f(x)')
kontrol("zincir", lx._on_isleme('s = x |> f |> g') == 's = g(f(x))')
kontrol("argümanlı", lx._on_isleme('s = x |> f(2)') == 's = f(x, 2)')

print("=== Pipe (uçtan uca exec) ===")
ns = calistir(
    'tanimla kare(n):\n    dondur n * n\n'
    'tanimla artir(n):\n    dondur n + 1\n'
    'sonuc = 3 |> kare |> artir'
)
kontrol("3 |> kare |> artir = 10", ns['sonuc'] == 10)

print("=== String/yorum koruması ===")
kontrol("literal pipe bozulmaz", lx._on_isleme('m = "x |> y"') == 'm = "x |> y"')
kontrol("literal aralık bozulmaz", lx._on_isleme('m = "1..10"') == 'm = "1..10"')

print("=== Mantık operatörleri (ve/veya/degil/ozdes) ===")
ns = calistir('a = dogru ve yanlis')
kontrol("dogru ve yanlis → False", ns['a'] is False)
ns = calistir('a = dogru veya yanlis')
kontrol("dogru veya yanlis → True", ns['a'] is True)
ns = calistir('a = degil dogru')
kontrol("degil dogru → False", ns['a'] is False)
ns = calistir('a = hic ozdes hic')
kontrol("hic ozdes hic → True", ns['a'] is True)

print("=== from import (kaynaktan) ===")
ns = calistir('kaynaktan math ice_aktar pi')
kontrol("kaynaktan math ice_aktar pi", abs(ns['pi'] - 3.14159) < 0.001)

print("=== Comprehension ===")
ns = calistir('k = [x*x her_biri_icin x icinde aralik(5)]')
kontrol("liste comprehension", ns['k'] == [0, 1, 4, 9, 16])
ns = calistir('s = {n: n*2 her_biri_icin n icinde aralik(3)}')
kontrol("sözlük comprehension", ns['s'] == {0: 0, 1: 2, 2: 4})

print(f"\nSONUC: {gecti} gecti, {basarisiz} basarisiz")
exit(1 if basarisiz else 0)
