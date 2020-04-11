# Yet Another Reliable UDP (YARU)

## Introduction

YARU is an application layer transport protocol built on top of UDP to add properties of ARQ (Automatic Repeat reQuest). It is designed to be small and easy to implement, while still providing the minimum functionality to enable reliable transmission of data.

## Specification

See [`spec.md`](spec.md) for the specification of the protocol.

## Implementation

The implementation is done using Python 3, using only the standard library modules for ease of portability. 

* See [`YARU.py`](YARU.py) for the implementation of a socket capable of handling this protocol.
* See [`examples`](examples) folder for details on how to use the `YARUSocket` class.

## Running

You need at least Python 3.7 installed in your system to be able to run the code.

Each example is given in a Client/Server architecture, which can be selected using a command line argument. So, you will need two terminals to run the examples. Always run the server first.

Steps:
1. Copy [`YARU.py`](YARU.py) file into the [`examples`](examples) folder.
2. In a terminal, just enter `python3 <filename>.py server` or `python3 <filename>.py client` to run the example.

## Testing

[`file_transfer.py`](examples/file_transfer.py) contains a very naive file transfer application code that uses the `YARUSocket` class to communicate over UDP and to demonstrate the reliability features of the protocol.

It's execution can be cutomized via command line parameters like:
* `address`: What interface to bind/connect to (default: localhost)
* `port`: Port of the receiver (default: 1060)
* `file`: (*required*) Which file to send
* `directory`: Where to store the received file (default: `Received`)
* `loglevel`: To set the cutoff for the logs to be displayed (default: DEBUG)

Pass either `receiver` or `sender` as role (`python file_transfer.py <role> <other arguments>`).  
`address`, `port` and `loglevel` should be specified before the role.

## Author

[Krut Patel](https://github.com/iamkroot)
