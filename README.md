# Kahin

Türkçe yazılan kaynağı Python'a çeviren bir programlama dili. `eger`, `tanimla`,
`her_biri_icin` gibi Türkçe anahtar kelimelerle yazarsın; Kahin bunu Python'a
çevirip çalıştırır. Altta CPython çalıştığı için Python'da ne varsa (sınıflar,
f-string, generator, match/case, tüm kütüphaneler) Kahin'de de var.

```
tanimla selamla(isim):
    dondur "Merhaba " + isim

her_biri_icin ad icinde ["Ada", "Can", "Derya"]:
    yazdir(selamla(ad))
```

```
Merhaba Ada
Merhaba Can
Merhaba Derya
```

## Kurulum

Gereksinim: Python 3.10+ (match/case için). Linux x86-64'te Rust hızlandırıcı
otomatik devreye girer; başka platformda Python yedeği çalışır.

```bash
git clone <repo-url> kahin
cd kahin
python kahin_cli.py program.kahin
```

İstersen `kahin` komutu olarak da kurabilirsin:

```bash
python install.py     # launcher script'i PATH'e koyar
kahin program.kahin
```

## Kullanım

```bash
kahin program.kahin            # çalıştır
kahin program.kahin --debug    # çevrilen Python'u göster
kahin program.kahin --cache-yok # bytecode cache'i atla
kahin                          # interaktif kabuk (REPL)
kahin --yardim                 # yardım
kahin --versiyon               # sürüm
```

## Dil

### Anahtar kelimeler

| Türkçe | Python | Türkçe | Python |
|--------|--------|--------|--------|
| `eger` | if | `tanimla` | def |
| `degilse_eger` | elif | `dondur` | return |
| `degilse` | else | `sinif` | class |
| `her_biri_icin` | for | `ile` | with |
| `dondu_boyunca` | while | `dene` / `yakala` | try / except |
| `icinde` | in | `sonunda` | finally |
| `dur` | break | `firlat` | raise |
| `devam_et` | continue | `ice_aktar` | import |
| `gec` | pass | `kaynaktan` | from |
| `ve` / `veya` / `degil` | and / or / not | `eslestir` / `desen` | match / case |
| `dogru` / `yanlis` / `hic` | True / False / None | `lambda` | lambda |

Yerleşik fonksiyonlar da Türkçe: `yazdir` (print), `uzunluk` (len), `aralik`
(range), `tam_sayi` (int), `metin` (str), `liste` (list), `sozluk` (dict),
`sirala` (sorted), `topla` (sum) ...

### Kahin'e özel sözdizimi

Python'da birebir karşılığı olmayan, ön-işlemede çevrilen kısayollar:

```
// yorum             -> # yorum
1..10                -> range(1, 10)
1..=10               -> range(1, 11)
x |> f |> g          -> g(f(x))
```

### match/case

```
tanimla durum_acikla(kod):
    eslestir kod:
        desen 200:
            dondur "Tamam"
        desen 404:
            dondur "Bulunamadi"
        desen 500 | 502 | 503:
            dondur "Sunucu hatasi"
        desen _:
            dondur "Bilinmeyen"
```

Literal, OR (`|`), wildcard (`_`), capture ve guard (`eger`) desenleri çalışır.

### Standart kütüphane

Türkçe API'li çekirdek modüller (`kahin_lib/`):

```
ice_aktar dosya
dosya.yaz("/tmp/not.txt", "selam")
yazdir(dosya.oku("/tmp/not.txt"))

ice_aktar veri
n = veri.cozumle('{"ad": "Kahin"}')

ice_aktar zaman
yazdir(zaman.gun_adi())
```

- `dosya` — oku, yaz, ekle, kaldir, var_mi
- `veri` — JSON: cozumle, serile, dosyadan_oku, dosyaya_yaz
- `zaman` — simdi, duraklat, tarih, gun_adi

Python kütüphaneleri de doğrudan kullanılabilir: `ice_aktar sistem` (os),
`ice_aktar istek` (requests), `kaynaktan math ice_aktar sqrt`.

### Hata mesajları

Çalışma zamanı hataları Türkçe ve `.kahin` satırını gösterir:

```
Çalışma zamanı hatası:
  program.kahin:5 satırında
  Sıfıra bölme: division by zero
```

Ham Python traceback için `--debug` kullan.

## Tek dosya binary (Python'suz çalıştırma)

Nuitka ile her şeyi (Python motoru dahil) tek dosyaya gömebilirsin:

```bash
python build_nuitka.py     # -> dist/kahin
```

Çıkan `dist/kahin` hedef makinede Python kurulu olmasa bile çalışır. Sadece
Linux x86-64'e taşınabilir; başka platform için orada derlemek gerekir.

## Nasıl çalışıyor

`.kahin` → ön-işleme → CPython tokenize → keyword değişimi → ast.parse →
optimize → compile → exec. İç işleyiş ve Rust hızlandırıcının yeri için
[MIMARI.md](MIMARI.md).

Rust hızlandırıcıyı yeniden derlemek için:

```bash
bash build_rust.sh    # cargo + kahin_rs.so kurar
```

## Proje yapısı

```
kahin_cli.py      giriş noktası (argüman, cache, REPL, hata)
kahin_lexer.py    tokenize + keyword + ön-işleme (Python yedeği)
kahin_ast.py      ast.parse + optimize transformer
kahin_cache.py    bytecode cache (~/.kahin_cache/)
kahin_hata.py     Python exception -> Türkçe mesaj
kahin_repl.py     interaktif kabuk
kahin_lib/        Türkçe stdlib (dosya, veri, zaman)
kahin_rs/         Rust ön-işleme kaynağı -> kahin_rs.so
build_nuitka.py   tek dosya binary derleme
MIMARI.md         iç işleyiş dokümanı
```
