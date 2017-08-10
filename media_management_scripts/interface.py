import curses
from curses import wrapper


def main(stdscr):
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.getkey()


def exit():
    #curses.nocbreak()
    #stdscr.keypad(False)
    #curses.echo()
    pass


def do_interface():
    wrapper(main)
