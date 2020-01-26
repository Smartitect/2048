from py2048_classes import Board


def getchar():
    try:
        # for Windows-based systems
        import msvcrt # If successful, we are on Windows
        return msvcrt.getch()

    except ImportError:
        # for POSIX-based systems (with termios & tty support)
        import tty, sys, termios  # raises ImportError if unsupported

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)
            answer = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return answer


def main():
    board = Board()
    board.add_random_tiles(2)
    print("main code")
    board.print_board()

    result = True
    while result:
        board.print_board()
        key = getchar()

        if key == b'q':
            quit()

        move = None

        if key == b'w':
            move = 'UP'

        if key == b'a':
            move = 'LEFT'

        if key == b's':
            move = 'DOWN'

        if key == b'd':
            move = 'RIGHT'

        if move is not None:
            temp = board.make_move(move)
            if temp:
                result = board.add_random_tiles(1)


if __name__ == "__main__":
    main()