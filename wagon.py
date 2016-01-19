#!/usr/bin/env python

import curses
import datetime
import os
import pickle
import pyglet
import sys


def init_curses():
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    screen.keypad(True)
    screen.nodelay(True)
    return screen


def destroy_curses(screen):
    screen.nodelay(False)
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()


def pickle_name(path):
    ext = ".pkl"
    p = os.path.splitext(path)
    assert p[1] != ext
    return p[0] + ext


def load(path):
    try:
        with open(pickle_name(path), 'rb') as f:
            markers = pickle.load(f)
    except FileNotFoundError:
        markers = {}
    return markers


def store(markers, path):
    with open(pickle_name(path), 'wb') as f:
        pickle.dump(markers, f)


def draw_progress(screen, y,
                  left, right,
                  pos, duration,
                  markers):
    w = curses.COLS

    # left
    lw = len(left) + 2
    screen.addstr(y, 0, left + " [")

    # right
    rw = len(right) + 2
    screen.addstr(y, w - rw, "] " + right)

    # bar
    bw = w - lw - rw
    fw = max(1, int(bw * pos / duration))
    screen.addstr(y, lw, "=" * (fw - 1) + ">" + " " * (bw - fw))

    # markers
    screen.addstr(y + 1, 0, " " * w)
    for key, pos in markers.items():
        x = lw + int(bw * pos / duration)
        screen.addstr(y + 1, x, key)


def play(path):
    song = pyglet.media.load(path, streaming=False)
    end = song.duration

    player = pyglet.media.Player()
    player.queue(song)

    markers = load(path)

    try:
        screen = init_curses()
        player.play()
        running = True
        while running:
            ch = screen.getch()
            if (ch < 0): pass
            elif ch == ord(' '):
                player.pause() if player.playing else player.play()
            elif ch == curses.KEY_BACKSPACE:
                player.seek(0)
            elif ch == 27:  # esc
                running = False
            elif ch == curses.KEY_LEFT:
                player.seek(max(0, player.time - 1))
            elif ch == curses.KEY_DOWN:
                player.seek(max(0, player.time - 5))
            elif ch == curses.KEY_RIGHT:
                player.seek(min(end, player.time + 1))
            elif ch == curses.KEY_UP:
                player.seek(min(end, player.time + 5))
            elif chr(ch).isupper():
                key = chr(ch).lower()
                markers[key] = player.time
            elif chr(ch) in markers:
                player.seek(markers[chr(ch)])
            elif ch == ord('q'):
                # allow exit on 'q' if not bound
                running = False

            draw_progress(screen, 1,
                          str(datetime.timedelta(seconds=int(player.time))),
                          str(datetime.timedelta(seconds=int(end))),
                          player.time, end,
                          markers)
            screen.refresh()

        store(markers, path)

    finally:
        player.pause()
        destroy_curses(screen)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Play an audio file and allow adding persistent markers for "
              "quick jumping. Seek with arrow keys, use space bar to toggle "
              "playing, and esc to exit. Add/change marks with S-<letter>, "
              "and jump to mark with <letter>.")
        print("usage: {} <audio file>".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)
    play(sys.argv[1])
