import argparse
import ipaddress
import logging
import time
from pathlib import Path
from YARU import YARUSocket


NAME_MARKER = b":name:"
END_MARKER = b":end:"


def receiver(address: ipaddress.IPv4Address, port: int, directory: Path, **kwargs):
    sock = YARUSocket()
    sock.bind((str(address), port))
    logging.info(f"Receiver bound to {address=}, {port=}")
    directory.mkdir(exist_ok=True)

    file_name = None
    file = None

    while True:
        data = sock.read()
        if not data:
            if not file_name:
                time.sleep(1)  # Idle mode
            else:
                time.sleep(0.1)  # active connection
            continue
        if data.startswith(NAME_MARKER):  # first packet has filename
            file_name = data[len(NAME_MARKER) :].decode()
            file = open(directory / file_name, "wb")
            logging.info(f"Receiving {file_name}")
            size, start_time = 0, time.time()
        elif data == END_MARKER:  # finished sending data
            delta_time = time.time() - start_time
            file.close()
            break
        else:  # file contents received, store to file
            size += len(data)
            file.write(data)
    sock.close()
    logging.info(
        f"Completed receiving {file_name}, {size} bytes, "
        f"{delta_time:.3f} seconds, speed={size / delta_time:.3f}BPS"
    )


def sender(address: ipaddress.IPv4Address, port: int, file: Path, **kwargs):
    sock = YARUSocket()
    sock.connect((str(address), port))

    logging.info(f"Sending {file.name}")
    sock.write(NAME_MARKER + str(file.name).encode("utf-8"))
    file_data = file.read_bytes()
    total_size = len(file_data)
    pkt_size = YARUSocket.MAX_DATA_SIZE
    offset = 0

    while offset < total_size:
        try:
            sock.write(file_data[offset : offset + pkt_size])
        except Exception:
            time.sleep(1)
        else:
            offset += pkt_size
    sock.write(END_MARKER)
    sock.close()
    logging.info(f"Completed sending {file.name}, {total_size} bytes")


if __name__ == "__main__":
    log_choices = {}
    for level in range(logging.CRITICAL + 1):
        name = logging.getLevelName(level)
        if name.startswith("Level"):
            continue
        log_choices[name] = level

    parser = argparse.ArgumentParser(
        description="Send and Receive files over YARU.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        type=ipaddress.IPv4Address,
        default="127.0.0.1",
        help="Which IP address to bind/connect to",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=1060, help="Receiver port",
    )
    parser.add_argument("--loglevel", choices=log_choices, default="DEBUG")
    subparser = parser.add_subparsers(help="Which role to play")
    parser_sender = subparser.add_parser("sender")
    parser_sender.add_argument("file", type=Path, help="The file to send")
    parser_sender.set_defaults(func=sender)
    parser_receiver = subparser.add_parser("receiver")
    parser_receiver.add_argument(
        "-d",
        "--directory",
        type=Path,
        default="Received",
        help="Where to store received file",
    )
    parser_receiver.set_defaults(func=receiver)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        raise argparse.ArgumentError(None, "Invalid role chosen")
    logging.basicConfig(level=args.loglevel)
    args.func(**vars(args))
