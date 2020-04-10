import argparse
from YARU import YARUSocket
import time

YARUSocket.WINDOW_SIZE = 4
YARUSocket.TIMEOUT = 3


def server(port):
    sock = YARUSocket()
    sock._sock.bind(("127.0.0.1", port))
    while True:
        time.sleep(1)
        print(sock.read())


def client(port):
    sock = YARUSocket()
    sock.connect(("localhost", port))
    sock.write(b"supp")
    time.sleep(0.25)
    sock.write(b"bois1")
    time.sleep(1)
    sock.write(b"bois2")
    sock.write(b"bois3")
    time.sleep(2)
    sock.write(b"bois4")


if __name__ == "__main__":
    choices = {"client": client, "server": server}
    parser = argparse.ArgumentParser(description="Send and Receive UDP locally")
    parser.add_argument("role", choices=choices, help="which role to play")
    parser.add_argument(
        "-p", metavar="PORT", type=int, default=1060, help="UDP port (default 53)"
    )
    args = parser.parse_args()
    function = choices[args.role]
    function(args.p)
