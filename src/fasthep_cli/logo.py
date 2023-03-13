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

logo_stripes: str = """

▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

      ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

"""

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
For more information, please visit https://fast-hep.web.cern.ch/fast-hep/
"""


class MultiLineText:
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
        return max(len(line) for line in self.lines)

    @property
    def height(self) -> int:
        return len(self.lines)

    @property
    def width(self) -> int:
        return len(self)

    def pad_height(self, top: int = 0, bottom: int = 0) -> None:
        self.lines = [" " * self.width] * top + self.lines + [" " * self.width] * bottom

    def append(self, text: MultiLineText, spacing: int = 2) -> None:
        diff_height = self.height - text.height
        if diff_height < 0:
            self.pad_height(bottom=abs(diff_height))

        lines = []
        for l1, l2 in zip(self.lines, text.lines):
            l1 += " " * spacing + l2
            lines.append(l1)
        self.lines = lines

    def overlay(self, text: MultiLineText, offset: int = 0) -> MultiLineText:
        result = MultiLineText(copy.deepcopy(self))
        diff_height = result.height - text.height

        if diff_height < 0:
            padding = abs(diff_height)
            # split padding in half for both top and bottom
            padding_top = padding // 2
            padding_bottom = padding - padding_top
            result.pad_height(top=padding_top, bottom=padding_bottom)

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
    space = "\n".join([" " * 11] * 9)
    merged = merge_pieces(
        [space, logo_f, logo_a, logo_s, logo_t, space, logo_h, logo_e, logo_p]
    )
    logo = merged.overlay(MultiLineText(logo_runner), offset=59)
    welcome = "\n".join([line.center(logo.width) for line in welcome_text.split("\n")])
    return str(logo) + welcome + "\n"


def main() -> None:
    print(get_logo())  # noqa: T201


if __name__ == "__main__":
    main()
