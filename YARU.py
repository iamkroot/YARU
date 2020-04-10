import hashlib
import socket


class YARUSocket:
    WINDOW_SIZE = 2 ** 63
    TIMEOUT = 30

    # packet constants
    MAX_BYTES = 65507
    SEQNUM_SIZE = 8
    LENGTH_SIZE = 2
    CHECKSUM_SIZE = 16
    _checksum_start = SEQNUM_SIZE + LENGTH_SIZE
    _checksum_end = _checksum_start + CHECKSUM_SIZE

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_buf = {}
        self.rcv_buf = {}
        self.timers = {}
        self.send_base = 0
        self.rcv_base = 0
        self.send_seqnum = 0

    @classmethod
    def make_packet(cls, seq_num: int, data: bytes) -> bytes:
        length = len(data)
        if length > cls.MAX_BYTES:
            raise ValueError("Data too long")

        # fill headers and data
        b = bytearray(seq_num.to_bytes(cls.SEQNUM_SIZE, "big"))
        b += length.to_bytes(cls.LENGTH_SIZE, "big")
        b += bytearray(cls.CHECKSUM_SIZE)  # initialized to 0
        b += data

        # store checksum
        b[cls._checksum_start : cls._checksum_end] = hashlib.md5(b).digest()
        return bytes(b)

    @classmethod
    def parse_packet(cls, packet: bytes) -> (int, bytes):
        packet = bytearray(packet)

        # validate checksum
        checksum = packet[cls._checksum_start : cls._checksum_end]
        packet[cls._checksum_start : cls._checksum_end] = bytearray(cls.CHECKSUM_SIZE)
        assert hashlib.md5(packet).digest() == checksum, "Checksum mismatch"

        # extract values
        seq_num = int.from_bytes(packet[: cls.SEQNUM_SIZE], "big")
        length = int.from_bytes(
            packet[cls.SEQNUM_SIZE : cls.SEQNUM_SIZE + cls.LENGTH_SIZE], "big"
        )
        data = bytes(packet[cls._checksum_end : cls._checksum_end + length])
        return seq_num, data

    def write(self, data, dest_addr, max_bytes=None):
        pass


if __name__ == '__main__':
    b = YARUSocket.make_packet(3, b"supp")
    seq_num, data = YARUSocket.parse_packet(b)
    print(seq_num, data)
