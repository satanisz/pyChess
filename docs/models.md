# Podłączanie modeli szachowych

UCI (Universal Chess Interface) to protokół tekstowy między aplikacją
prowadzącą partię a procesem silnika. Aplikacja wysyła pozycję, historię ruchów
i polecenie rozpoczęcia poszukiwań. Silnik zwraca ruch w rodzaju
`bestmove e7e5`. Ten sam program można uruchomić po obu stronach lub wystawić
przeciwko silnikowi innego autora. Aplikacja sprawdza legalność każdej decyzji.
[Specyfikacja UCI](https://backscattering.de/chess/uci/) ·
[Obsługa UCI w python-chess](https://python-chess.readthedocs.io/en/latest/engine.html)

## Własny model w Pythonie

Uruchamialny przykład składa się z [klasy oceniającej ruchy](../examples/my_model.py)
i [wag JSON](../config/example-weights.json). Aby podłączyć swoją sieć:

1. Skopiuj przykład. Załaduj swoje wagi raz, przed wywołaniem `serve_scorer`.
2. W metodzie `score_moves(context)` zwróć słownik ocen dla legalnych ruchów UCI.
   Model dostaje FEN, stronę na ruchu, legalne ruchy, historię i budżet czasu
   w sekundach. Możesz użyć `pychess.models.encode_position(context.fen)`,
   jeśli model potrzebuje 12 płaszczyzn figur 8×8. Roszady, en passant i licznik
   ruchów są dostępne w FEN. Wyniki diagnostyczne programu wypisuj na stderr.
3. Dodaj wpis w `engines` i użyj jego nazwy w oknie gry lub na arenie. Poniżej
   działający profil z dołączonej konfiguracji:

```json
{
  "engines": {
    "my-model": {
      "command": ["{python}", "../examples/my_model.py", "example-weights.json"],
      "move_time": 0.1,
      "timeout": 5
    }
  },
  "play": {"white": "none", "black": "my-model"},
  "arena": {"participants": ["my-model", "heuristic"], "games": 2}
}
```

Zapisz ten przykład w katalogu `config/`, żeby ścieżki wskazywały dołączone
pliki. `{python}` oznacza interpreter bieżącego środowiska. Możesz też podać
interpreter innego środowiska wirtualnego, program napisany w C++ lub dowolny
inny silnik UCI. Funkcja `serve_scorer` wykonuje jedną predykcję na ruch i wybiera
najwyżej oceniony legalny ruch. Dla własnego silnika przeszukującego drzewo
możesz użyć jego natywnej implementacji UCI.

## Konfiguracja eksperymentu

| Pole | Znaczenie |
| --- | --- |
| `engines.<id>.command` | Program i argumenty jako tablica JSON. Ścieżka do programu jest względna wobec pliku konfiguracji. Sama nazwa programu jest wyszukiwana w PATH. |
| `cwd` | Katalog roboczy procesu. Domyślnie jest to katalog pliku JSON. Względem niego silnik otwiera argumenty plikowe i wagi. |
| `options` | Opcje ogłaszane przez dany silnik w UCI, np. `{"Hash": 32, "Threads": 1}` dla Stockfisha. |
| `move_time`, `timeout` | Budżet na ruch oraz dodatkowy czas na odpowiedź protokołu, w sekundach. Timeout obowiązuje także przy uruchamianiu procesu. |
| `nodes` | Opcjonalny dodatni limit przeszukanych węzłów, wysyłany wraz z budżetem czasu. |
| `play.white`, `play.black`, `play.seed` | Profile graczy w oknie. `none` oznacza człowieka. |
| `arena.white`, `arena.black` | Profile w meczu ze stałymi kolorami. |
| `arena.participants`, `arena.games` | Uczestnicy turnieju każdy z każdym i liczba partii na parę. |
| `arena.max_plies`, `arena.seed`, `arena.database` | Limit półruchów, początkowy seed oraz ścieżka do opcjonalnej bazy względem JSON. |

Nadaj osobne identyfikatory różnym wagom i ustawieniom, np. `model-v1`
i `model-v2`. Baza zestawia wyniki po identyfikatorze gracza. Seed steruje
wbudowanym generatorem losowym. Dla zewnętrznego silnika ustawienia losowości
zależą od obsługiwanych przez niego opcji.

## Pobieranie wag i silników

`pychess-models fetch` pobiera wybrany plik przez HTTPS i sprawdza SHA-256.
W przypadku archiwum TAR odczytuje wskazaną binarkę i sprawdza dodatkowo jej
sumę. Zweryfikowany plik trafia do katalogu docelowego przez zmianę nazwy.
Ponowne uruchomienie korzysta z prawidłowej kopii obecnej na dysku.
Uruchomienie profilu UCI oznacza uruchomienie programu z uprawnieniami Twojego
konta, dlatego korzystaj z binarek i konfiguracji z zaufanego źródła.

Wbudowany katalog zawiera następujące pozycje:

| Pozycja | Co pobierasz | Jak grać |
| --- | --- | --- |
| `stockfish-18-linux-x64` | Binarka Stockfisha 18 z osadzonymi wagami NNUE dla Linuksa x86-64. | Profil `stockfish-18` w przykładowej konfiguracji. |
| `maia-1100` | Wagi sieci Maia-1100. | Profil `maia-1100` przekazuje plik wag do Lc0 z limitem jednego węzła. |

Dla Mai trzeba mieć odpowiednią dla platformy binarkę Leela Chess Zero.
Dołączony profil oczekuje jej w `.pychess/models/lc0`. Jeżeli masz już Lc0
w PATH, zmień pierwszy element `command` na `"lc0"`. Ustawienia wag i budżetu
są już w [config/local.json](../config/local.json).
[Wydanie Stockfisha 18](https://github.com/official-stockfish/Stockfish/releases/tag/sf_18) ·
[Modele Maia i zalecenia dotyczące limitu węzłów](https://github.com/CSSLab/maia-chess) ·
[Wersje Lc0 dla poszczególnych platform](https://lczero.org/play/download/)

```bash
uv run pychess-models fetch maia-1100
uv run pychess --config config/local.json --black-engine maia-1100
```

Na tym stanowisku w katalogu modeli jest już Lc0 0.32.1 z obsługą CPU
przez Eigen. Na nowym Linuksie z kompilatorem C++20, Git, Mesonem, Ninja,
pkg-config i nagłówkami zlib oraz Eigen można odtworzyć tę wersję, wykonując
z katalogu PyChess:

```bash
mkdir -p .pychess/build .pychess/models
git clone --recurse-submodules --branch v0.32.1 https://github.com/LeelaChessZero/lc0.git .pychess/build/lc0-src
CPLUS_INCLUDE_PATH=/usr/include/eigen3 meson setup .pychess/build/lc0-cpu .pychess/build/lc0-src --buildtype=release --default-library=static -Dgtest=false -Dopenblas=false -Dplain_cuda=false -Db_lto=false -Dispc=false
meson compile -C .pychess/build/lc0-cpu lc0
install -m755 .pychess/build/lc0-cpu/lc0 .pychess/models/lc0
```

Możesz dodać własny katalog na wzór [catalog.json](../src/pychess/models/catalog.json).
Wpis dla surowego pliku zawiera `description`, `url`, `sha256` i `filename`.
Dla wykonywalnego silnika dodaj `"executable": true`. Dla pojedynczego pliku
z archiwum TAR podaj też `tar_member` i `file_sha256`. Profil JSON gry
wskazuje wynikowy plik lub program, który wczyta pobrane wagi.

```bash
uv run pychess-models --catalog moj-katalog.json list
uv run pychess-models --catalog moj-katalog.json fetch nazwa-modelu --directory .pychess/models
```
