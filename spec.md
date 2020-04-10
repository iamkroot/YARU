# Yet Another Reliable UDP (YARU)

## Introduction

An application layer transport protocol built on top of UDP to add properties of ARQ (Automatic Repeat reQuest). It is designed to be small and easy to implement, while still providing the minimum functionality to enable reliable transmission of data. Therefore, it lacks most of the features of a regular TCP, such as handshakes, flow control, and congestion control.

## Features
### Error Detection
Uses a simple MD5 checksum to detect bit errors in a transmitted packet.

### Sequence numbers
Used for sequential numbering of packets of data flowing from sender to receiver and allowing the receiver to detect duplicate packets.

### Acknowledgements
Special packets sent by receiver to indicate that a particular packet has been received correctly.

### Pipelining
Allows multiple packets to be transmitted concurrently, so that sender utilization can be increased over a stop-and-wait mode of operation. YARU follows the Selective Repeat scheme for sending acknowledgements, so each packet gets ACK'ed individually.

### Timeouts
Timers are used by the sender to protect against lost packets, where each packet has its own timer. If timeout occurs, the packet has to be retransmitted.

## Packet layout
bitrange|0...15|16..79|80...207|
--------|------|------|--------|
   field|length|seqnum|checksum|

* **length:** 16-bit number, which is the length in octets of this packet including this header and the data. Should be at least `208` (size of header), and at most `65507` (maximum allowed for UDP over IP). If this value is `0`, it is an ACK packet.
* **seqnum:** 64-bit sequence number of the current packet.
* **checksum:** 128-bit checksum of the YARU packet, calculated by first creating the entire packet with checksum field as `0`, and then storing its md5 hash into the correct location. 

## Interface to UDP

YARU is designed to build on top of the unreliable properties of UDP such as packet dropping. 
