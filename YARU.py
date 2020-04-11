import hashlib
import logging
import socket
import select
from threading import Thread, Timer

logging.basicConfig(level=logging.DEBUG)


class YARUSocket:
    """Represents a socket for YARU protocol."""

    WINDOW_SIZE = 1024
    TIMEOUT = 30

    # packet constants
    SEQNUM_SIZE = 8
    LENGTH_SIZE = 2
    CHECKSUM_SIZE = 16
    _checksum_start = SEQNUM_SIZE + LENGTH_SIZE
    _checksum_end = _checksum_start + CHECKSUM_SIZE
    MAX_IP_SIZE = 65535  # (2 ** 16) - 1
    MAX_DATA_SIZE = 65481  # MAX_IP_SIZE - 20[IP head] - 8[UDP head] - 26[YARU head]

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_buf = {}
        self.recv_buf = {}
        self.acked_pkts = set()
        self.timers = {}
        self.send_base = 0
        self.recv_base = 0
        self.send_seqnum = 0
        self.recv_thread = Thread(target=self._recv_loop, name="recv_thread")
        self.recv_thread.start()

    @classmethod
    def make_packet(cls, seq_num: int, data: bytes) -> bytes:
        """Attach YARU header to given data, ready to be sent via UDP."""
        length = len(data)
        if length > cls.MAX_DATA_SIZE:
            logging.debug("Length: %d", length)
            raise ValueError("Data too long")

        # fill headers and data
        pkt = bytearray()
        pkt += seq_num.to_bytes(cls.SEQNUM_SIZE, "big")
        pkt += length.to_bytes(cls.LENGTH_SIZE, "big")
        pkt += bytearray(cls.CHECKSUM_SIZE)  # initialized to 0
        pkt += data

        # store checksum
        pkt[cls._checksum_start : cls._checksum_end] = hashlib.md5(pkt).digest()
        return bytes(pkt)

    @classmethod
    def parse_packet(cls, packet: bytes) -> (int, bytes):
        """Parse the incoming UDP packet data into YARU packet seq_num and data"""
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

    def _start_timer(self, seq_num):
        timer = Timer(self.TIMEOUT, self._handle_timeout, (seq_num,))
        timer.start()
        self.timers[self.send_seqnum] = timer

    def _handle_timeout(self, seq_num):
        logging.debug(f"Timed out for {seq_num=}")
        try:
            self._sock.send(self.send_buf[seq_num])
        except KeyError:
            raise Exception(f"Sequence num {seq_num} not in send buffer.")
        self._start_timer(seq_num)

    def _recv_loop(self):
        while True:
            r, _, _ = select.select([self._sock], [], [], 0.1)
            pkt, address = self._sock.recvfrom(self.MAX_IP_SIZE)
            self._handle_pkt(pkt, address)

    def _send_ack(self, seq_num, address):
        logging.debug(f"Sending ack for {seq_num=}")
        self._sock.sendto(self.make_packet(seq_num, b""), address)

    def _handle_pkt(self, pkt, address):
        try:
            seq_num, data = self.parse_packet(pkt)
            logging.trace(f"Received: {seq_num=} {data=}")
        except AssertionError:
            logging.info("Corrupted packet received")
            return
        if not data:  # packet is an ACK
            self.acked_pkts.add(seq_num)
            while self.send_base in self.acked_pkts:
                self.timers[self.send_base].cancel()
                del self.timers[self.send_base]
                del self.send_buf[self.send_base]
                self.acked_pkts.remove(self.send_base)
                logging.debug(f"Removed {self.send_base=} from send buffer.")
                self.send_base += 1
            logging.debug(f"Updated {self.send_base=}")

        elif self.recv_base <= seq_num < self.recv_base + self.WINDOW_SIZE:
            self._send_ack(seq_num, address)
            self.recv_buf[seq_num] = data
            logging.debug(f"Received new packet with {seq_num=}.")
        elif self.recv_base - self.WINDOW_SIZE <= seq_num < self.recv_base:
            self._send_ack(seq_num, address)
        else:
            logging.warning(f"Outside window: {self.recv_base=}, {seq_num=}, {data=}")

    def bind(self, address):
        """Bind the socket to the given interface and port."""
        self._sock.bind(address)

    def connect(self, address):
        """Establish a connection to another YARU socket."""
        self._sock.connect(address)

    def read(self):
        """Read the data sent by the connected socket, present in the buffer.

        If no data is available, it returns an empty string.
        """
        buf = bytearray()
        while self.recv_base in self.recv_buf:
            buf += self.recv_buf[self.recv_base]
            self.recv_base += 1
            logging.debug(f"Updated {self.recv_base=}")
        return bytes(buf)

    def write(self, data):
        """Send the data (of type bytes) to the connected socket.

        The data should be less than 65481 bytes long.
        """
        if self.send_seqnum >= self.send_base + self.WINDOW_SIZE:
            raise Exception("Send buffer full")
        pkt = self.make_packet(self.send_seqnum, data)
        self.send_buf[self.send_seqnum] = pkt
        self._start_timer(self.send_seqnum)
        self._sock.sendall(pkt)
        self.send_seqnum += 1
