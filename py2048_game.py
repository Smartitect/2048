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

    move_counter = 0
    move = None
    move_result = False
    
    while True:
        print("Number of moves:{}, Last move:{}:, Move status:{}".format(move_counter, move, move_result))
        print(board)
        key = getchar()

        if key == b'q':
            quit()

        if key == b'w':
            move = 'UP'
        elif key == b'a':
            move = 'LEFT'
        elif key == b's':
            move = 'DOWN'
        elif key == b'd':
            move = 'RIGHT'
        else:
            move = None

        if move is not None:
            move_result = board.make_move(move)
            if move_result:
                add_tile_result = board.add_random_tiles(1)
                move_counter = move_counter + 1

if __name__ == "__main__":
    main()
