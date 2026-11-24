# PyChess

PyChess pozwala rozegrać partię na jednej planszy, zagrać przeciwko modelowi
albo porównać kilka silników w lokalnym turnieju. Gra i arena czytają te same
profile JSON. Zewnętrzne silniki komunikują się z aplikacją przez UCI.

## Pierwsza partia

W katalogu projektu wykonaj:

```bash
uv sync --locked
uv run pychess --config config/local.json
```

Grasz białymi, a czarnymi gra przykładowy model napisany w Pythonie. Pierwsza
partia działa bez pobierania dodatkowego silnika. Kliknij figurę i pole docelowe
albo przeciągnij figurę. **M** otwiera wybór obu graczy, **R** rozpoczyna nową
partię, **Q** zamyka grę. W panelu widać kolej ruchu, szach, wynik i historię.
Przy promocji wybierz figurę w panelu lub klawiszem **1–4**.

Plansza dopasowuje się do okna. Przeciągnij jego krawędź lub zmaksymalizuj
okno, żeby uzyskać więcej miejsca. Przyciskami **−** i **+** obok napisu
„Plansza” albo klawiszami **−** i **+** zmienisz jej rozmiar od 50% do 100%
dostępnego miejsca, także podczas partii.

```bash
# Dwie osoby przy jednym komputerze
uv run pychess

# Lista profili z konfiguracji
uv run pychess --config config/local.json --list-engines

# Obserwacja gry dwóch silników na planszy
uv run pychess --config config/local.json --white-engine my-model --black-engine heuristic
```

## Gra z pobranym silnikiem

Na Linuksie x86-64 można pobrać Stockfisha 18 z wbudowaną siecią NNUE.
Uruchom te polecenia z katalogu projektu:

```bash
uv run pychess-models list
uv run pychess-models fetch stockfish-18-linux-x64
uv run pychess --config config/local.json --black-engine stockfish-18
```

Pliki trafiają do `.pychess/models/`. Kolejna gra korzysta z lokalnej kopii.
Na innych platformach w polu `command` podaj ścieżkę do wersji silnika dla
swojego systemu. Osobne pliki wag i własne programy opisuje
[przewodnik po modelach](docs/models.md).

## Turniej i wyniki

Przykładowa konfiguracja uruchamia turniej modelu użytkownika, silnika
heurystycznego i losowego. Każda para gra dwie partie z zamianą kolorów.
Polecenia poniżej pozwalają rozegrać turniej, odczytać tabelę i wyeksportować
partie do odtworzenia w dowolnej przeglądarce PGN.

```bash
uv run pychess-arena --config config/local.json
uv run pychess-arena --config config/local.json --standings
uv run pychess-arena --config config/local.json --export-pgn .pychess/turniej.pgn
```

Aby porównać swój model bezpośrednio ze Stockfishem po jego pobraniu:

```bash
uv run pychess-arena --config config/local.json --participants my-model stockfish-18 --games 2
```

`--games` określa liczbę partii **na parę**. Parzysta wartość daje każdemu tyle
samo gier białymi i czarnymi. Aby ustalić kolory, użyj
`--white my-model --black heuristic`. Ten tryb pozwala też grać z samym sobą.
Flagi wiersza poleceń mają pierwszeństwo przed wartościami z JSON.

Po każdej partii arena zapisuje wynik, przyczynę zakończenia, graczy, seed,
limit półruchów i PGN w bazie `.pychess/arena.sqlite3`. Kolejne uruchomienia
dopisują partie. Pierwsza tabela przedstawia wyniki właśnie zakończonej sesji,
a `--standings` obejmuje całą wskazaną bazę. Możesz użyć `--database PLIK`
do osobnego eksperymentu. Lokalny ranking Elo startuje od 1500, z K=32.
Partia przerwana przez limit półruchów zachowuje wynik `*`. Takie partie
i gry z samym sobą pomijane są przy obliczaniu Elo. Błąd procesu,
przekroczenie czasu i nielegalny ruch kończą partię walkowerem.

### Wewnętrzna liga Elo

Do prowadzenia ligi wybierz osobny plik SQLite na sezon. Przykład wykorzystuje
pięć lokalnych profili, w tym Stockfisha i Maię z Lc0. Jedna kolejka to
20 partii, po dwie na parę. Kolejne uruchomienie z tą samą bazą dopisuje
wyniki do sezonu. Zmieniaj `--seed` między kolejkami, aby silnik losowy
rozgrywał inne partie.

```bash
uv run pychess-arena --config config/local.json --database .pychess/liga-01.sqlite3 --participants stockfish-18 maia-1100 my-model heuristic random --games 2 --seed 2
uv run pychess-arena --database .pychess/liga-01.sqlite3 --elo
uv run pychess-arena --database .pychess/liga-01.sqlite3 --elo-history my-model
```

Polecenie `--elo` porządkuje uczestników według rankingu z całego sezonu.
Opcja `--elo-history NAZWA` pokazuje kolejne partie jednego modelu,
jego przeciwników, kolor, wynik zapisany z perspektywy białych, zmianę Elo
oraz miejsce w lidze po każdej partii.
W [raporcie z sezonu](docs/liga-01/README.md) znajdziesz wykres i historię
50 partii każdego z pięciu modeli wraz z zapisami PGN.
Używaj odrębnych nazw profili dla kolejnych wersji swojego modelu, aby każda
wersja miała własną historię i ocenę.

## Środowisko i testy

Lokalna wersja Pythona to 3.14.4. Ten sam plik blokady zależności i polecenia
`uv` działają również w PowerShell. Baza korzysta z SQLite dostarczanego
z Pythonem. Gra i arena działają bez usług w tle.

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Możliwa jest również instalacja edytowalna w środowisku wirtualnym przez
`python -m pip install -e . --group dev`. W takim środowisku grę uruchamia
`python -m pychess`. Przykład eksportu grafiki wymaga systemowej biblioteki
Cairo. Polecenie `uv run --extra examples python examples/simple.py` zapisuje
`image.svg` i `image_scaled.png` w bieżącym katalogu.

[Plan wykonania i kryteria odbioru](docs/executive-plan.md)
