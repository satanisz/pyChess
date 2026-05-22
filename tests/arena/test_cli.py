from pychess.arena.cli import main


def test_arena_cli_runs_match(capsys) -> None:
    exit_code = main(
        [
            "--white",
            "random",
            "--black",
            "heuristic",
            "--games",
            "1",
            "--max-plies",
            "2",
            "--seed",
            "3",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "random vs heuristic" in output
    assert "score:" in output
