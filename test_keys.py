import sys, tty, termios

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
            if ch == '\x1b[1':
                ch += sys.stdin.read(3)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

if __name__ == '__main__':
    print("Press a key (or q to quit)")
    # while True:
    #     ch = getch()
    #     print(repr(ch))
    #     if ch == 'q':
    #         break
