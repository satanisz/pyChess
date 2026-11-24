# Executive Plan: PyChess

## Wydanie lokalnej platformy do gry i porównywania modeli

Punktem wyjścia jest działająca gra na Pythonie 3.14, kontroler reguł,
dwa wbudowane silniki i arena pojedynczych par. Dotychczasowy rejestr tworzył
jedynie silnik losowy lub heurystyczny, a wyniki areny znikały po zamknięciu
procesu. Poniższa pętla prowadzi od tego stanu do lokalnych eksperymentów.

| Etap | Decyzja implementacyjna | Próba odbiorowa |
| --- | --- | --- |
| 1. Kontrakt | Wspólny plik JSON wskazuje program UCI, argumenty, opcje i budżet na ruch. | Ten sam profil silnika działa w grze i w arenie, również spoza katalogu projektu. |
| 2. Źródła modeli | Katalog pobrań opisuje wersję, URL i SHA-256. Silnik z osadzoną siecią i oddzielny plik wag reprezentują dwa sposoby dystrybucji. | Pobrać publiczny silnik, sprawdzić sumę i uzyskać legalny ruch. Uruchomić przykładowy własny model jako osobny proces. |
| 3. Gra | Wybór graczy dla obu kolorów, stan partii i obsługa błędu silnika w oknie. | Zagrać ruch przeciwko silnikowi, obejrzeć odpowiedź, rozpocząć nową partię i zamknąć okno podczas obliczeń. |
| 4. Arena | Mecze i turniej każdy z każdym, zamiana kolorów, archiwum SQLite i eksport PGN. | Rozegrać turniej trzech uczestników, odczytać klasyfikację po ponownym uruchomieniu i odtworzyć partie z PGN. |
| 5. Integracja | Uruchamiać testy reguł i regresji, testy procesu UCI oraz próby obu publicznych poleceń. | Wynik walkowera jest zgodny w bazie, tabeli i PGN. Błędne wagi, timeout i przerwanie pobierania dają odtwarzalne wyniki lub komunikaty. |

Prace nad protokołem, oknem gry i areną można wykonywać równolegle po
uzgodnieniu interfejsu konfiguracji. Po połączeniu zmian powtarzamy próby
odbiorowe z prawdziwym silnikiem. Każdy wykryty błąd wraca do odpowiedniej
części wraz z przypadkiem testowym. Poniższa mapa rozwoju obejmuje także
przyszłe eksperymenty z treningiem i self-play.

### Wynik odbioru na Pythonie 3.14.4

W oknie Pygame na wirtualnym ekranie SDL człowiek zagrał e4, a Stockfish 18
odpowiedział e5. Zamykanie okna przerwało również aktywne obliczenia silnika.
Własny model z przykładu uruchomił się jako osobny proces z tego samego JSON.

Arena zapisała sześć partii turnieju Stockfish–heurystyka–model przykładowy
i dwie partie Stockfish–Maia z zamianą kolorów. Maia-1100 używała pobranych
wag i Lc0 0.32.1 na CPU. Odtworzenie wszystkich ośmiu eksportów PGN dało
te same końcowe wyniki i liczby półruchów co SQLite. Osobne testy objęły
nielegalną odpowiedź, niedostępny program, zawieszenie silnika i błędną
sumę pliku. Instalacja pakietu wheel w czystym środowisku pozwoliła uruchomić
katalog modeli oraz arenę z własnym graczem spoza katalogu projektu.

## Cel

Zbudować PyChess jako aplikację i platformę eksperymentalną dla konkurujących ze sobą modeli szachowych. Projekt ma obsługiwać tryby:

- człowiek kontra człowiek
- człowiek kontra model
- model kontra model
- turnieje wielu modeli

Modele mogą być klasycznymi silnikami, heurystykami albo sieciami neuronowymi. Reguły gry muszą pozostać deterministyczne i kontrolowane przez silnik zasad. Modele mają wyłącznie wybierać ruch spośród legalnych ruchów.

## Strategia

Najpierw kończymy stabilny produkt szachowy, a dopiero potem dokładamy warstwę AI. Dzięki temu modele konkurują jakością decyzji, a nie przypadkowymi błędami w logice gry, UI albo walidacji ruchów.

Główne warstwy projektu powinny być rozdzielone:

- `pychess.core`: logika gry, stan planszy, FEN, PGN, kontroler partii
- `pychess.ui`: renderer Pygame, input użytkownika, widoki
- `pychess.engines`: wspólny interfejs graczy i silników
- `pychess.arena`: headless tryb model kontra model
- `pychess.models`: wrappery na sieci neuronowe i modele eksperymentalne
- `pychess.eval`: rankingi, statystyki, raporty

## Faza 1: Core Gry

Zaimplementować pełne, poprawne zasady szachów. Rekomendowanym fundamentem jest `python-chess`, żeby nie pisać ręcznie walidacji roszady, mata, pata, en passant i promocji.

Zakres:

- model planszy i partii
- legalne ruchy
- stan gry: szach, mat, pat, remis
- roszada, en passant, promocja pionka
- cofanie ruchu
- zapis i odczyt FEN
- eksport PGN
- testy jednostkowe dla krytycznych stanów gry

Rezultat: gra działa poprawnie bez AI.

## Faza 2: UI Pygame

Zbudować pełne UI desktopowe na obecnej bazie Pygame.

Zakres:

- plansza 8x8
- renderowanie figur
- przeciąganie figur
- wybór figury kliknięciem
- podświetlanie legalnych ruchów
- oznaczenie ostatniego ruchu
- komunikaty o szachu, macie, pacie i remisie
- dialog promocji pionka
- historia ruchów
- restart partii
- podstawowy ekran wyboru trybu gry

Rezultat: aplikacja jest grywalna dla człowieka.

## Faza 3: Interfejs Gracza i Silnika

Wprowadzić stabilny kontrakt dla wszystkich graczy, zarówno ludzkich, jak i modelowych.

Przykładowy interfejs:

```python
class PlayerEngine:
    def choose_move(self, position, legal_moves, time_left) -> MoveDecision: ...
```

Wejście dla modelu:

- FEN pozycji
- lista legalnych ruchów
- historia partii
- czas pozostały na decyzję
- opcjonalne metadane turniejowe

Wyjście modelu:

- wybrany ruch
- confidence score
- czas obliczeń
- opcjonalne uzasadnienie
- opcjonalna dystrybucja policy po ruchach

Zasada bezpieczeństwa: aplikacja nigdy nie ufa modelowi w kwestii legalności ruchu. Legalność zawsze sprawdza `pychess.core`.

## Faza 4: Pierwsze Silniki

Dodać silniki bazowe, które będą punktem odniesienia dla sieci neuronowych.

Zakres:

- `HumanPlayer`
- `RandomEngine`
- `HeuristicEngine`
- `NeuralEngine`

`HeuristicEngine` powinien oceniać przynajmniej:

- materiał
- kontrolę centrum
- bezpieczeństwo króla
- mobilność
- proste groźby taktyczne

Rezultat: mamy baseline, który pozwala mierzyć, czy model neuronowy faktycznie gra lepiej niż losowo.

## Faza 5: Arena Modeli

Zbudować tryb headless do rozgrywania partii bez UI.

Zakres:

- model kontra model
- kolejka meczów
- limit czasu na ruch
- limit liczby półruchów
- automatyczny zapis PGN
- wynik partii
- tabela wyników
- ranking Elo albo Glicko
- statystyki ruchów i czasu decyzji
- wykrywanie nielegalnych odpowiedzi modelu

Przykładowe użycie:

```powershell
pychess-arena --white random --black heuristic --games 100
```

Rezultat: projekt staje się platformą ewaluacyjną, a nie tylko grą.

## Faza 6: Sieci Neuronowe

Nie zaczynać od dużego modelu trenowanego od zera. Najpierw przygotować małe, mierzalne modele.

Rekomendowane podejście:

- reprezentacja planszy jako tensor `8x8xN`
- wyjście jako scoring legalnych ruchów albo policy over moves
- trening supervised learning na partiach PGN
- później self-play
- ewaluacja zawsze przez arenę

Docelowe typy modeli:

- szybki model taktyczny
- model pozycyjny
- model końcówek
- model eksperymentalny
- ensemble albo voting engine

Rezultat: można podpinać wiele konkurujących sieci i obiektywnie porównywać wyniki.

## Faza 7: Product Polish

Po ustabilizowaniu core, UI i areny dopracować doświadczenie użytkownika.

Zakres:

- ekran menu
- wybór graczy i modeli
- konfiguracja turnieju
- zegary szachowe
- replay partii
- eksport PGN
- podgląd ewaluacji
- log decyzji modeli
- raport po turnieju

Rezultat: aplikacja jest używalna jako produkt, a nie tylko eksperyment techniczny.

## Minimalne MVP

Projekt można uznać za pierwsze sensowne MVP, gdy obsługuje:

- pełne legalne szachy
- `Human vs Human`
- `Human vs RandomEngine`
- `RandomEngine vs HeuristicEngine`
- zapis PGN
- headless arenę
- testy core i engine API
- Ruff i pytest przechodzą bez ręcznych kroków

## Ryzyka

Największe ryzyko to pomieszanie UI, logiki gry i AI. Te warstwy muszą pozostać osobne.

Drugie ryzyko to budowanie sieci neuronowej bez rzetelnej ewaluacji. Dlatego arena, baseline'y i ranking są ważniejsze niż sam model.

Trzecie ryzyko to zależność od Pygame w miejscach, które powinny działać headless. Arena i testy nie mogą wymagać otwierania okna.

## Definition of Done

Projekt jest skończony, gdy można:

- odpalić grę człowieka w UI
- odpalić turniej modeli bez UI
- podpiąć nowy model przez stabilny interfejs
- porównać modele rankingiem
- odtworzyć każdą partię z PGN
- zapisać i wczytać pozycję FEN
- uruchomić `ruff`, `pytest` i testy areny bez ręcznej konfiguracji

## Priorytet Wykonania

1. Core gry na `python-chess`
2. UI grywalne dla człowieka
3. Interfejs silników
4. Baseline engines
5. Arena headless
6. Ranking i raporty
7. Neural engine wrappers
8. Trening i self-play
9. Product polish
