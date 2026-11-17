#!/usr/bin/env python3

"""Display normal input and underlined preedit together, wrapping across lines.

Run with: python3 test/preedit.py

Enables the proposed mode 2035 and OSC 2035 preedit protocol when supported.
Otherwise, the terminal displays preedit. Each OSC payload sets the entire
preedit, including empty text. Ctrl-C exits.
"""

import codecs
import curses
import os
import re
import select
import sys


def parse_input(pending: str) -> tuple[list[tuple[str, str]], str]:
    events = []
    while pending:
        if not pending.startswith("\x1b"):
            end = pending.find("\x1b")
            if end == -1:
                end = len(pending)
            events.append(("text", pending[:end]))
        elif len(pending) == 1:
            break
        elif pending.startswith("\x1b]"):
            end = pending.find("\x1b\\", 2)
            if end == -1:
                break
            if pending.startswith("\x1b]2035;"):
                events.append(("preedit", pending[7:end]))
            end += 2
        elif pending.startswith("\x1b["):
            sequence = re.match(r"\x1b\[[0-?]*[ -/]*[@-~]", pending)
            if sequence is None:
                break
            report = re.fullmatch(r"\x1b\[\?2035;([0-4])\$y", sequence[0])
            if report is not None:
                events.append(("mode", report[1]))
            end = sequence.end()
        elif pending.startswith("\x1bO"):
            if len(pending) < 3:
                break
            end = 3
        else:
            end = 2
        pending = pending[end:]
    return events, pending


def draw(screen: curses.window, committed: str, preedit: str) -> None:
    size = os.get_terminal_size(sys.stdout.fileno())
    if curses.is_term_resized(size.lines, size.columns):
        curses.resizeterm(size.lines, size.columns)
    height, width = screen.getmaxyx()
    screen.erase()
    if height >= 2 and width >= 2:
        screen.addnstr(0, 0, "Preedit test | Ctrl-C exits", width - 1)
        text = screen.derwin(height - 1, width, 1, 0)
        text.scrollok(True)
        text.addstr(committed)
        text.addstr(preedit, curses.A_UNDERLINE)
        row, column = text.getyx()
        screen.move(row + 1, column)
    screen.refresh()


def run(screen: curses.window) -> None:
    curses.cbreak()
    curses.nonl()
    curses.curs_set(1)
    decoder = codecs.getincrementaldecoder("utf-8")()
    pending = ""
    committed = ""
    preedit = ""
    mode = None
    sys.stdout.write("\x1b[?2035$p")
    sys.stdout.flush()
    try:
        while True:
            events, pending = parse_input(pending)
            for event, value in events:
                if event == "mode" and mode is None:
                    mode = value
                    if mode in ("1", "2"):
                        sys.stdout.write("\x1b[?2035h")
                        sys.stdout.flush()
                elif event == "preedit":
                    preedit = value
                elif event == "text":
                    for char in value:
                        if char == "\x03":
                            raise KeyboardInterrupt
                        if char in ("\x08", "\x7f"):
                            committed = committed[:-1]
                        elif char == "\r":
                            committed += "\n"
                        elif char >= " " or char in ("\n", "\t"):
                            committed += char
            draw(screen, committed, preedit)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                chunk = os.read(sys.stdin.fileno(), 4096)
                if not chunk:
                    return
                pending += decoder.decode(chunk)
    finally:
        if mode in ("1", "2"):
            sys.stdout.write("\x1b[?2035l")
            sys.stdout.flush()


def main() -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Run this program directly in a terminal.", file=sys.stderr)
        return 1
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        return 130
    except (OSError, UnicodeError, curses.error) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
