import pytest

from pychess.arena.archive import open_archive
from pychess.arena.cli import main


def test_player_history_uses_whole_league_and_keeps_archive_read_only(tmp_path, capsys):
    database = tmp_path / "league.sqlite3"
    with open_archive(database) as connection, connection:
        connection.executemany(
            """INSERT INTO games (white, black, result, termination, plies, seed,
                                  max_plies, pgn) VALUES (?, ?, ?, 'normal', 0, '1',
                                  512, '')""",
            [("A", "B", "1-0"), ("B", "C", "1-0"), ("C", "A", "0-1")],
        )
    before = database.read_bytes()
    assert main(["--database", str(database), "--elo-history", "C"]) == 0
    header, first, second = capsys.readouterr().out.splitlines()
    assert header.startswith("player game\tleague game\t")
    number, game_id, player, color, opponent, result, start, end, delta, rank, why = (
        first.split("\t")
    )
    assert (number, game_id, player, color, opponent, result) == (
        "1",
        "2",
        "C",
        "black",
        "B",
        "1-0",
    )
    # B had already lost to A. C loses more than 16 points to this opponent.
    assert float(start) == 1500 and float(end) < 1484 and float(delta) < -16
    assert (rank, why) == ("3", "normal")
    fields = second.split("\t")
    assert fields[:6] == ["2", "3", "C", "white", "A", "0-1"]
    assert fields[6] == end
    assert database.read_bytes() == before

    with pytest.raises(SystemExit) as error:
        main(["--database", str(database), "--elo-history", "missing"])
    assert error.value.code == 2
    assert "missing" in capsys.readouterr().err
    assert database.read_bytes() == before


def test_history_of_missing_archive_does_not_create_it(tmp_path):
    database = tmp_path / "missing.sqlite3"
    with pytest.raises(SystemExit) as error:
        main(["--database", str(database), "--elo-history", "player"])
    assert error.value.code == 2
    assert not database.exists()
