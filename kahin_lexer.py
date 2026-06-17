#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
KAHİN LEXER (TOKENIZER) - CPython-like Implementation
═══════════════════════════════════════════════════════════════════════

CPython'un tokenizer'ı gibi çalışır.
Kahin kaynak kodunu TOKEN'lara ayırır.

TOKEN TÜRLERİ:
--------------
- KEYWORD    : eger, yazdir, tanimla, ...
- NAME       : değişken/fonksiyon isimleri
- NUMBER     : 123, 3.14
- STRING     : "merhaba", 'test'
- OP         : +, -, *, /, ==, >=, ...
- NEWLINE    : \n
- INDENT     : Girinti
- DEDENT     : Çıkıntı
- COMMENT    : // yorum

PERFORMANS:
-----------
- Python'un tokenize modülünü kullanır (C implementasyonu)
- Çok hızlı: ~0.001s for 1000 satır
"""

import tokenize
import io
import re
import token
from enum import IntEnum
from typing import List, Tuple, NamedTuple

# Rust hızlandırıcı (PyO3). Varsa ön işleme Rust'ta yapılır, yoksa Python fallback.
try:
    import kahin_rs as _kahin_rs
except ImportError:
    _kahin_rs = None


# ═══════════════════════════════════════════════════════════════════════
# TÜRKÇE ANAHTAR KELİMELER
# ═══════════════════════════════════════════════════════════════════════

TURKCE_KEYWORDS = {
    # Kontrol yapıları
    'ice_aktar', 'kaynaktan', 'tanimla', 'eger', 'degilse_eger', 'degilse',
    'dondu_boyunca', 'her_biri_icin', 'icinde', 'dondur',
    'dur', 'devam_et', 'gec', 'ile', 'yukle',

    # Mantık operatörleri
    've', 'veya', 'degil', 'ozdes',

    # Hata yakalama
    'dene', 'yakala', 'sonunda', 'firlat', 'olumla',

    # Sabitler
    'dogru', 'yanlis', 'hic',

    # OOP
    'sinif', 'sil', 'kuresel', 'yerel_degil', 'lambda',

    # Built-in fonksiyonlar (opsiyonel - normal NAME olarak da işlenebilir)
    'yazdir', 'girdi', 'uzunluk', 'aralik', 'tam_sayi',
    'metin', 'ondalik', 'liste', 'sozluk', 'kume',
    'demet', 'tur', 'yardim', 'mutlak', 'sirala',
    'ac', 'topla', 'en_buyuk', 'en_kucuk', 'bekle',
}

# Python karşılıkları
KEYWORD_MAP = {
    'ice_aktar': 'import', 'kaynaktan': 'from', 'tanimla': 'def', 'eger': 'if',
    'degilse_eger': 'elif', 'degilse': 'else', 'dondu_boyunca': 'while',
    'her_biri_icin': 'for', 'icinde': 'in', 'dondur': 'return',
    've': 'and', 'veya': 'or', 'degil': 'not', 'ozdes': 'is',
    'dur': 'break', 'devam_et': 'continue', 'gec': 'pass',
    'ile': 'with', 'yukle': 'yield', 'dene': 'try',
    'yakala': 'except', 'sonunda': 'finally', 'firlat': 'raise',
    'olumla': 'assert', 'dogru': 'True', 'yanlis': 'False',
    'hic': 'None', 'sinif': 'class', 'sil': 'del',
    'kuresel': 'global', 'yerel_degil': 'nonlocal', 'lambda': 'lambda',
    'as': 'as',

    # Built-ins
    'yazdir': 'print', 'girdi': 'input', 'uzunluk': 'len',
    'aralik': 'range', 'tam_sayi': 'int', 'metin': 'str',
    'ondalik': 'float', 'liste': 'list', 'sozluk': 'dict',
    'kume': 'set', 'demet': 'tuple', 'tur': 'type',
    'yardim': 'help', 'mutlak': 'abs', 'sirala': 'sorted',
    'ac': 'open', 'topla': 'sum', 'en_buyuk': 'max',
    'en_kucuk': 'min', 'bekle': 'input',

    # Modüller
    'sistem': 'os', 'zaman': 'time', 'istek': 'requests', 'arayuz': 'sys',
}


# ═══════════════════════════════════════════════════════════════════════
# TOKEN SINIFI (NamedTuple - CPython tarzı)
# ═══════════════════════════════════════════════════════════════════════

class KahinToken(NamedTuple):
    """
    Kahin Token - CPython'un TokenInfo'su gibi

    Attributes:
        type: Token tipi (NAME, NUMBER, STRING, OP, ...)
        string: Token'ın string değeri
        start: (satır, sütun) başlangıç pozisyonu
        end: (satır, sütun) bitiş pozisyonu
        line: Tam satır içeriği
    """
    type: int
    string: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    line: str


# ═══════════════════════════════════════════════════════════════════════
# LEXER (TOKENIZER) - CPython-like
# ═══════════════════════════════════════════════════════════════════════

class KahinLexer:
    """
    Kahin Lexer - CPython'un tokenizer'ı gibi

    NASIL ÇALIŞIR:
    --------------
    1. Python'un tokenize modülünü kullan (C implementasyonu, çok hızlı)
    2. Her token'ı oku
    3. Türkçe keyword'leri Python'a çevir
    4. Token stream döndür

    AVANTAJLAR:
    -----------
    - CPython'un C kodunu kullandığı için ÇOK HIZLI
    - Girinti (indent/dedent) otomatik handle edilir
    - String/comment parsing doğru çalışır
    - Encoding desteği
    """

    def __init__(self):
        self.tokens = []

    def tokenize(self, kaynak_kod: str) -> List[KahinToken]:
        """
        Kahin kaynak kodunu token'lara ayır

        Args:
            kaynak_kod: Kahin kaynak kodu (Türkçe)

        Returns:
            Token listesi

        Örnek:
            >>> lexer = KahinLexer()
            >>> tokens = lexer.tokenize('eger x > 5:\\n    yazdir("test")')
            >>> for tok in tokens:
            ...     print(f"{tok.type:10} {tok.string!r}")
            NAME       'if'
            NAME       'x'
            OP         '>'
            NUMBER     '5'
            OP         ':'
            NEWLINE    '\\n'
            INDENT     '    '
            NAME       'print'
            OP         '('
            STRING     '"test"'
            OP         ')'
        """

        # Önce ön işleme: yorum + yeni sözdizimi (aralık, pipe)
        kaynak_kod = self._on_isleme(kaynak_kod)

        # Python'un tokenizer'ını kullan
        tokens = []

        try:
            # Byte stream oluştur
            byte_stream = io.BytesIO(kaynak_kod.encode('utf-8'))

            # Tokenize et (CPython'un C implementasyonu)
            for tok in tokenize.tokenize(byte_stream.readline):
                # Token tipini al
                tok_type = tok.type
                tok_string = tok.string

                # NAME token ise ve Türkçe keyword ise çevir
                if tok_type == token.NAME and tok_string in KEYWORD_MAP:
                    tok_string = KEYWORD_MAP[tok_string]

                # KahinToken oluştur
                kahin_tok = KahinToken(
                    type=tok_type,
                    string=tok_string,
                    start=tok.start,
                    end=tok.end,
                    line=tok.line
                )

                tokens.append(kahin_tok)

        except tokenize.TokenError as e:
            raise SyntaxError(f"Lexer hatası: {e}")

        self.tokens = tokens
        return tokens

    def _on_isleme(self, kod: str) -> str:
        """
        Tokenize öncesi ön işleme.

        1. Yorum çevirisi (// → #)
        2. Yeni sözdizimi (string/yorum dışında):
           - Aralık:  1..10  → range(1, 10)   |  1..=10 → range(1, 11)
           - Pipe:    x |> f → f(x)            |  zincir soldan sağa

        String ve yorum içeriği KORUNUR — literal'ler bozulmaz.

        Rust modülü (kahin_rs) varsa tek geçişte orada yapılır; yoksa
        Python regex hattına düşülür. Çıktı eşittir.
        """
        if _kahin_rs is not None:
            return _kahin_rs.to_python(kod)
        kod = self._yorum_cevir(kod)
        kod = self._koruyarak_uygula(kod, self._aralik_cevir)
        kod = self._koruyarak_uygula(kod, self._pipe_cevir)
        return kod

    def _yorum_cevir(self, kod: str) -> str:
        """// → # çevirisi"""
        lines = []
        for line in kod.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('//'):
                indent = line[:len(line) - len(stripped)]
                comment = stripped[2:]
                line = indent + '#' + comment
            lines.append(line)
        return '\n'.join(lines)

    def _koruyarak_uygula(self, kod: str, donustur) -> str:
        """
        String ve yorumları placeholder ile koru, donustur(kod) uygula, geri yükle.
        donustur: sadece kod-segmentlerine uygulanan fonksiyon.
        """
        sakli = []

        def sakla(m):
            sakli.append(m.group(0))
            return f"\x00{len(sakli) - 1}\x00"

        # f-string, normal string, yorum — sırayla korunur
        korunmus = re.sub(r'f"[^"]*"|f\'[^\']*\'|"[^"]*"|\'[^\']*\'|#[^\n]*', sakla, kod)
        donusen = donustur(korunmus)
        for i, parca in enumerate(sakli):
            donusen = donusen.replace(f"\x00{i}\x00", parca)
        return donusen

    def _aralik_cevir(self, kod: str) -> str:
        """1..10 → range(1, 10) | 1..=10 → range(1, 11). İçerme (=) dahil eder."""
        def repl(m):
            bas, esit, son = m.group(1), m.group(2), m.group(3)
            ust = f"{son} + 1" if esit else son
            return f"range({bas}, {ust})"
        # tamsayı veya basit isim operandları
        return re.sub(r'(\b\w+)\.\.(=?)(\w+\b)', repl, kod)

    def _pipe_cevir(self, kod: str) -> str:
        """
        x |> f → f(x). Soldan sağa zincir, satır bazlı.
        f bir isim ya da çağrı olabilir: x |> f → f(x), x |> f(2) → f(x, 2).
        """
        if '|>' not in kod:
            return kod
        cikti = []
        for satir in kod.split('\n'):
            cikti.append(self._pipe_satir(satir))
        return '\n'.join(cikti)

    def _pipe_satir(self, satir: str) -> str:
        if '|>' not in satir:
            return satir
        # girinti + atama önekini koru
        m = re.match(r'^(\s*(?:[\w\.]+\s*=\s*|dondur\s+|return\s+)?)(.*)$', satir)
        onek, govde = m.group(1), m.group(2)
        parcalar = self._pipe_bol(govde)
        if len(parcalar) < 2:
            return satir
        ifade = parcalar[0].strip()
        for sag in parcalar[1:]:
            sag = sag.strip()
            if sag.endswith(')') and '(' in sag:
                # f(2) → f(ifade, 2)
                ac = sag.index('(')
                fn, arglar = sag[:ac], sag[ac + 1:-1].strip()
                ifade = f"{fn}({ifade}, {arglar})" if arglar else f"{fn}({ifade})"
            else:
                ifade = f"{sag}({ifade})"
        return onek + ifade

    def _pipe_bol(self, s: str):
        """Üst seviye |> ayır (parantez/bracket içini atla)."""
        parcalar, derinlik, son = [], 0, 0
        i = 0
        while i < len(s):
            c = s[i]
            if c in '([{':
                derinlik += 1
            elif c in ')]}':
                derinlik -= 1
            elif derinlik == 0 and c == '|' and i + 1 < len(s) and s[i + 1] == '>':
                parcalar.append(s[son:i])
                son = i + 2
                i += 2
                continue
            i += 1
        parcalar.append(s[son:])
        return parcalar

    def tokens_to_code(self, tokens: List[KahinToken]) -> str:
        """
        Token'ları tekrar kaynak koda çevir (detokenize)

        CPython'un tokenize.untokenize() gibi ama daha basit.
        """
        return tokenize.untokenize([
            (tok.type, tok.string, tok.start, tok.end, tok.line)
            for tok in tokens
        ]).decode('utf-8')


# ═══════════════════════════════════════════════════════════════════════
# TEST & BENCHMARK
# ═══════════════════════════════════════════════════════════════════════

def test_lexer():
    """Lexer test"""

    print("═" * 70)
    print("KAHİN LEXER - CPython-like Implementation")
    print("═" * 70)

    # Test kodu
    kahin_kod = '''// Test
eger x > 5:
    yazdir("Büyük")
degilse:
    yazdir("Küçük")

tanimla topla(a, b):
    dondur a + b
'''

    print("\nKahin Kodu:")
    print(kahin_kod)

    # Lexer oluştur
    lexer = KahinLexer()

    # Tokenize et
    import time
    start = time.perf_counter()
    tokens = lexer.tokenize(kahin_kod)
    elapsed = time.perf_counter() - start

    print(f"\nTokenize süresi: {elapsed*1000:.3f} ms")
    print(f"Token sayısı: {len(tokens)}")

    # Token'ları göster
    print("\nToken Stream:")
    print("-" * 70)
    print(f"{'TİP':<15} {'STRING':<20} {'POS':<15}")
    print("-" * 70)

    for tok in tokens[:20]:  # İlk 20 token
        tok_name = token.tok_name.get(tok.type, str(tok.type))
        print(f"{tok_name:<15} {tok.string!r:<20} {str(tok.start):<15}")

    if len(tokens) > 20:
        print(f"... ({len(tokens) - 20} token daha)")

    # Detokenize et
    print("\nDetokenize (Python Kodu):")
    print("-" * 70)
    python_kod = lexer.tokens_to_code(tokens)
    print(python_kod)


def benchmark_lexer():
    """Lexer performans testi"""

    print("\n" + "═" * 70)
    print("PERFORMANS TESTİ")
    print("═" * 70)

    # Büyük kod üret
    kod_parcalari = []
    for i in range(1000):
        kod_parcalari.append(f'''
tanimla fonksiyon_{i}(x):
    eger x > {i}:
        yazdir("Test {i}")
        dondur dogru
    degilse:
        dondur yanlis
''')

    buyuk_kod = '\n'.join(kod_parcalari)

    print(f"\nKod boyutu: {len(buyuk_kod)} karakter")
    print(f"Satır sayısı: {buyuk_kod.count(chr(10))}")

    # Benchmark
    import time

    lexer = KahinLexer()

    # Isınma
    for _ in range(3):
        lexer.tokenize(buyuk_kod)

    # Gerçek test
    iterations = 10
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        tokens = lexer.tokenize(buyuk_kod)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\nSonuçlar ({iterations} iterasyon):")
    print(f"  Ortalama: {avg_time*1000:.3f} ms")
    print(f"  En hızlı: {min_time*1000:.3f} ms")
    print(f"  En yavaş: {max_time*1000:.3f} ms")
    print(f"  Token sayısı: {len(tokens)}")
    print(f"  Token/saniye: {len(tokens)/avg_time:,.0f}")


if __name__ == "__main__":
    test_lexer()
    benchmark_lexer()
