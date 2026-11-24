"""Player selection, move list and controls beside the board."""

from __future__ import annotations

from collections.abc import Mapping

import pygame

from pychess.core import GameStatus, MoveRecord, Side

BACKGROUND = (28, 36, 34)
PANEL = (37, 47, 44)
TEXT = (238, 239, 227)
MUTED = (179, 192, 183)
BUTTON = (62, 76, 69)
ACCENT = (198, 222, 145)
ERROR = (255, 189, 156)
PROMOTIONS = {"q": "Hetman", "r": "Wieża", "b": "Goniec", "n": "Skoczek"}


def player_label(name: str) -> str:
    return "Człowiek" if name == "none" else name


def status_text(status: GameStatus, automated: bool) -> str:
    if status.is_checkmate:
        return f"Mat · {status.result}"
    if status.is_game_over:
        return f"{'Pat' if status.is_stalemate else 'Remis'} · {status.result}"
    title = "Ruch białych" if status.turn == Side.WHITE else "Ruch czarnych"
    if status.is_check:
        return f"{title} · szach"
    if automated:
        return f"{title} · obliczanie"
    return title


class GamePanel:
    def __init__(self, screen: pygame.Surface, left: int) -> None:
        self.buttons: dict[str, pygame.Rect] = {}
        font = pygame.font.match_font("inter,dejavusans")
        self.body = pygame.font.Font(font, 24)
        self.small = pygame.font.Font(font, 20)
        self.heading = pygame.font.Font(font, 32)
        self.compact_heading = pygame.font.Font(font, 26)
        self.heading.bold = self.compact_heading.bold = True
        self.scroll = 0
        self.zoom_percent = 100
        self.resize(screen, left)

    def resize(self, screen: pygame.Surface, left: int) -> None:
        """Move the panel and discard hitboxes from the previous frame."""
        self.screen = screen
        self.left = left
        padding = 12 if screen.get_width() - left < 300 else 18
        self.x = left + padding
        self.width = max(1, screen.get_width() - self.x - padding)
        self.buttons.clear()

    def _label(
        self,
        text: str,
        y: int,
        *,
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] = TEXT,
        x: int | None = None,
        width: int | None = None,
    ) -> None:
        font = font or self.body
        width = self.width if width is None else width
        if font.size(text)[0] > width:
            while text and font.size(text + "…")[0] > width:
                text = text[:-1]
            text += "…"
        self.screen.blit(
            font.render(text, True, color), (self.x if x is None else x, y)
        )

    def _button(
        self, action: str, label: str, y: int, *, index: int = 0, columns: int = 1
    ) -> None:
        gap = 6
        width = (self.width - (columns - 1) * gap) // columns
        x = self.x + index * (width + gap)
        rect = pygame.Rect(x, y, width, 40)
        self._draw_button(action, rect)
        if label.endswith("]") and self.small.size(label)[0] > width - 4:
            label = label.rsplit(" [", 1)[0]
        inset = min(9, max(2, (width - self.small.size(label)[0]) // 2))
        self._label(
            label,
            rect.centery - self.small.get_height() // 2,
            font=self.small,
            x=x + inset,
            width=width - 2 * inset,
        )

    def _heading_font(self, text: str) -> pygame.font.Font:
        if self.heading.size(text)[0] <= self.width:
            return self.heading
        return self.compact_heading

    def _paragraph(self, text: str, y: int) -> None:
        rendered = self.body.render(text, True, MUTED, wraplength=self.width)
        self.screen.blit(rendered, (self.x, y))

    def _draw_button(self, action: str, rect: pygame.Rect) -> None:
        self.buttons[action] = rect
        pygame.draw.rect(self.screen, BUTTON, rect, border_radius=5)

    def _zoom_controls(self, y: int) -> None:
        self._label(
            f"Plansza {self.zoom_percent}%",
            y + 16 - self.small.get_height() // 2,
            font=self.small,
            width=self.width - 84,
        )
        for i, (action, glyph) in enumerate((("zoom_out", "-"), ("zoom_in", "+"))):
            rect = pygame.Rect(self.x + self.width - 78 + i * 42, y, 36, 32)
            self._draw_button(action, rect)
            label = self.body.render(glyph, True, TEXT)
            self.screen.blit(label, label.get_rect(center=rect.center))

    def action_at(self, pos: tuple[int, int]) -> str | None:
        return next(
            (key for key, rect in self.buttons.items() if rect.collidepoint(pos)), None
        )

    def _begin(self) -> None:
        self.buttons.clear()
        self.screen.fill(
            PANEL,
            (
                self.left,
                0,
                self.screen.get_width() - self.left,
                self.screen.get_height(),
            ),
        )

    def draw_play(
        self,
        players: Mapping[Side, str],
        status: GameStatus,
        moves: tuple[MoveRecord, ...],
        error: str | None,
        promotion: bool,
    ) -> None:
        self._begin()
        title = (
            "Błąd silnika"
            if error
            else status_text(status, players[status.turn] != "none")
        )
        detail = ""
        if self.heading.size(title)[0] > self.width:
            title, _, detail = title.partition(" · ")
        title_font = self._heading_font(title)
        self._label(
            title,
            14,
            font=title_font,
            color=ERROR if error else ACCENT,
        )
        y = 14 + title_font.get_linesize()
        if detail:
            self._label(detail, y, font=self.small, color=MUTED)
            y += self.small.get_linesize()
        y += 12
        compact = self.screen.get_height() < 640
        label_column = self.small.size("Czarne")[0] + 12
        for side, label in ((Side.WHITE, "Białe"), (Side.BLACK, "Czarne")):
            self._label(label, y, font=self.small, color=MUTED)
            name_offset = label_column if compact else 0
            if not compact:
                y += self.small.get_linesize()
            self._label(
                player_label(players[side]),
                y,
                x=self.x + name_offset,
                width=self.width - name_offset,
            )
            y += self.body.get_linesize() + 6
        content_top = y + 8
        footer_top = self.screen.get_height() - 146
        if error:
            self._error_text(error, content_top, footer_top)
        elif promotion:
            font = self._heading_font("Promocja pionka")
            self._label("Promocja pionka", content_top, font=font)
            for index, (suffix, name) in enumerate(PROMOTIONS.items()):
                self._button(
                    suffix,
                    f"{index + 1}. {name}",
                    content_top + font.get_linesize() + 5 + (index // 2) * 46,
                    index=index % 2,
                    columns=2,
                )
        else:
            self._history(moves, content_top, footer_top)
        self._zoom_controls(footer_top)
        y = footer_top + 41
        self._button("menu", "Gracze [M]", y, columns=2)
        self._button("restart", "Od nowa [R]", y, columns=2, index=1)
        self._button("quit", "Zakończ [Q]", y + 46)

    def _error_text(self, message: str, y: int, bottom: int) -> None:
        # Long paths and diagnostics may contain no spaces.
        while message and y + self.small.get_height() < bottom:
            end = 1
            while (
                end < len(message)
                and self.small.size(message[: end + 1])[0] <= self.width
            ):
                end += 1
            split = message.rfind(" ", 0, end) if end < len(message) else end
            split = split if split > 0 else end
            self._label(message[:split], y, font=self.small)
            message = message[split:].lstrip()
            y += self.small.get_linesize()

    def _history(self, moves: tuple[MoveRecord, ...], top: int, bottom: int) -> None:
        rows: dict[int, list[str]] = {}
        for move in moves:
            pair = rows.setdefault(move.fullmove_number, ["", ""])
            pair[int(move.side == Side.BLACK)] = move.san
        font = self._heading_font("Historia ruchów")
        self._label("Historia ruchów", top, font=font)
        first_row_y = top + font.get_linesize() + 6
        if not rows:
            self._paragraph("Oczekiwanie na pierwszy ruch", first_row_y)
            return
        row_height = self.body.get_linesize() + 4
        visible = max(1, (bottom - first_row_y - 8) // row_height)
        if len(rows) > visible:
            visible = max(1, visible - 1)
            self._label(
                "Przewiń kółkiem myszy",
                bottom - self.small.get_linesize() - 4,
                font=self.small,
                color=MUTED,
            )
        self.scroll = max(0, min(self.scroll, len(rows) - visible))
        end = len(rows) - self.scroll
        column_width = (self.width - 46) // 2
        for i, (number, (white, black)) in enumerate(
            list(rows.items())[max(0, end - visible) : end]
        ):
            y = first_row_y + row_height * i
            self._label(f"{number}.", y, color=MUTED, width=42)
            self._label(white, y, x=self.x + 46, width=column_width)
            self._label(black, y, x=self.x + 46 + column_width, width=column_width)

    def draw_menu(self, players: Mapping[Side, str]) -> None:
        self._begin()
        self._label(
            "Nowa partia", 14, font=self._heading_font("Nowa partia"), color=ACCENT
        )
        self._paragraph("Kliknij gracza, aby go zmienić.", 62)
        self._label("Białe", 134, font=self.small, color=MUTED)
        self._button("white", player_label(players[Side.WHITE]) + "   >", 159)
        self._label("Czarne", 220, font=self.small, color=MUTED)
        self._button("black", player_label(players[Side.BLACK]) + "   >", 245)
        self._button("start", "Rozpocznij [Enter]", 330)
        self._button("back", "Wróć do partii [Esc]", 379)
