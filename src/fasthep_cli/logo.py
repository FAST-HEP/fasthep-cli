"""FAST-HEP logo and welcome text for console output"""

from __future__ import annotations

import copy

# trying to imitate the font from
# https://fonts.google.com/specimen/Press+Start+2P?preview.text=FAST-HEP&preview.text_type=custom


logo_f: str = """
█████████╗
███╔═════╝
███║
███████╗
███╔═══╝
███║
███║
╚══╝
"""

logo_a: str = """
   █████╗
 ███╔══███╗
███╔╝   ███╗
███║    ███║
███████████║
███║    ███║
███║    ███║
╚══╝    ╚══╝

"""

logo_s: str = """
  ██████╗
███╔═══███╗
███║   ╚══╝
 ╚██████╗
  ╚════███╗
███    ███║
╚═██████╔═╝
  ╚═════╝
"""

logo_t: str = """
███████████╗
╚═══███╔═══╝
    ███║
    ███║
    ███║
    ███║
    ███║
    ╚══╝
"""

logo_h: str = """
███╗    ███╗
███║    ███║
███║    ███║
███████████║
███╔════███║
███║    ███║
███║    ███║
╚══╝    ╚══╝
"""

logo_e: str = """
██████████╗
███╔══════╝
███║
█████████╗
███╔═════╝
███║
██████████╗
╚═════════╝
"""

logo_p: str = """
█████████╗
███╔════███╗
███║    ███║
█████████╔═╝
███╔═════╝
███║
███║
╚══╝
"""

logo_stripes: str = "\n".join(
    [
        " ",
        " ",
        2 * " " + 58 * "=",
        " ",
        9 * " " + 16 * "=",
        " ",
        4 * " " + 18 * "=",
        " ",
        " ",
    ]
)


logo_runner: str = """
             ▄███▄
       ▄▄▄▄▄  ▀█▀ ▄
     ▄█▀  ████▄▄▄▀▀
     █   ███
       ▄███
 ▄▄▄▄▄██▀███▄
 ▐▀▀▀▀▀▀   ██
           █▀
           █
           ▀▀
"""


welcome_text: str = """
Welcome to the FAST-HEP command line interface
For more information, please visit https://fast-hep.github.io/
"""


class MultiLineText:
    """Class to represent multi-line text"""

    lines: list[str]

    def __init__(self, text: MultiLineText | str) -> None:
        if isinstance(text, MultiLineText):
            self.lines = copy.deepcopy(text.lines)
            return
        self.lines = text.split("\n")
        width = self.width
        self.lines = [line.ljust(width) for line in self.lines]

    def __getitem__(self, index: int) -> str:
        return self.lines[index]

    def __len__(self) -> int:
        """Return the length of the longest line (i.e. the width)"""
        return max(len(line) for line in self.lines)

    @property
    def height(self) -> int:
        """Return the number of lines (i.e. the height)"""
        return len(self.lines)

    @property
    def width(self) -> int:
        """Alias for __len__"""
        return len(self)

    def pad_height(self, top: int = 0, bottom: int = 0) -> None:
        """Pad the text with empty lines on top and/or bottom"""
        self.lines = [" " * self.width] * top + self.lines + [" " * self.width] * bottom

    def pad_width(self, left: int = 0, right: int = 0) -> None:
        """Pad the text with empty spaces on left and/or right"""
        self.lines = [
            line.ljust(self.width + right).rjust(self.width + left)
            for line in self.lines
        ]

    def append(self, text: MultiLineText, spacing: int = 2) -> None:
        """Append text to the current text"""
        diff_height = self.height - text.height
        if diff_height < 0:
            self.pad_height(bottom=abs(diff_height))

        lines = []
        for line1, line2 in zip(self.lines, text.lines):
            line1 += " " * spacing + line2
            lines.append(line1)
        self.lines = lines

    def overlay(self, text: MultiLineText, offset: int = 0) -> MultiLineText:
        """Overlay text on top of the current text"""
        result = MultiLineText(copy.deepcopy(self))
        diff_height = result.height - text.height

        if diff_height < 0:
            padding = abs(diff_height)
            # split padding in half for both top and bottom
            padding_top = padding // 2
            padding_bottom = padding - padding_top
            result.pad_height(top=padding_top, bottom=padding_bottom)

        diff_width = result.width - (text.width + offset)
        if diff_width < 0:
            padding = abs(diff_width)
            result.pad_width(right=padding)

        for i, line in enumerate(text.lines):
            start = offset
            end = offset + len(line)
            new_line = result[i][:start]
            for j, char in enumerate(line):
                if char != " ":
                    new_line += char
                else:
                    new_line += result.lines[i][start + j]
            if len(result.lines[i]) > end:
                new_line += result.lines[i][end:]
            result.lines[i] = new_line
        return result

    def __str__(self) -> str:
        """Return the text as a string"""
        return "\n".join(self.lines)


def merge_pieces(pieces: list[str], spacing: int = 2) -> MultiLineText:
    """
    Merges a list of ASCII art pieces into a single piece.
    """
    # Merge the pieces by overlaying them one by one
    result = MultiLineText(pieces[0])
    for piece in pieces[1:]:
        result.append(MultiLineText(piece), spacing=spacing)

    return result


def get_logo() -> str:
    """Return the FAST-HEP logo"""
    space = "\n".join([" " * 11] * 9)
    merged = merge_pieces(
        [space, logo_f, logo_a, logo_s, logo_t, space, logo_h, logo_e, logo_p]
    )
    logo = merged.overlay(MultiLineText(logo_runner), offset=59)
    stripes = MultiLineText(logo_stripes)
    logo = stripes.overlay(logo, offset=0)
    welcome = "\n".join([line.center(logo.width) for line in welcome_text.split("\n")])
    return str(logo) + welcome + "\n"


if __name__ == "__main__":
    print(get_logo())  # noqa: T201
