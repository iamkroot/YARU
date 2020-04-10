import argparse
import socket
from YARU import YARUSocket
MAX_BYTES = 65535


def server(port=1600):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    print("Listening at {}".format(sock.getsockname()))
    data, address = sock.recvfrom(MAX_BYTES)
    text = YARUSocket.parse_packet(data)
    print(text)


def client(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = YARUSocket.make_packet(4, b"S" * 65481)
    sock.sendto(data, ("127.0.0.1", port))


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
