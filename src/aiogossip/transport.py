import asyncio
import socket

import typeguard

from . import codec
from .address import Address, to_address
from .message import Message


class Transport:
    PACKET_SIZE = 4096

    @typeguard.typechecked
    def __init__(self, addr: Address, loop: asyncio.AbstractEventLoop):
        self.loop = loop

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((addr.ip.exploded, addr.port))
        self.sock.setblocking(False)

        self.addr = to_address(self.sock.getsockname())

        self.rx_bytes = 0
        self.rx_packets = 0
        self.tx_bytes = 0
        self.tx_packets = 0

    @typeguard.typechecked
    async def send(self, message: Message, addr: Address):
        """
        Sends a message to the specified address.

        Args:
            message: The message to send.
            addr: The address to send the message to.

        Raises:
            TypeError: If the address is not of type Address.
            ValueError: If the message size exceeds the packet size.

        Returns:
            None
        """
        data = codec.packb(message)
        if len(data) > self.PACKET_SIZE:
            raise ValueError(f"Message size exceeds packet size of {self.PACKET_SIZE} bytes: {len(data)}")

        await self.loop.sock_sendto(self.sock, data, (addr.ip.exploded, addr.port))
        self.tx_packets += 1
        self.tx_bytes += len(data)

    @typeguard.typechecked
    async def recv(self) -> tuple[Message, Address]:
        """
        Receives a message from the transport.

        Returns:
            A tuple containing the received message and the address it was received from.
        """
        data, addr = await self.loop.sock_recvfrom(self.sock, self.PACKET_SIZE)
        self.rx_packets += 1
        self.rx_bytes += len(data)

        addr = to_address(addr)
        message = codec.unpackb(data)
        return message, addr

    def close(self):
        """
        Closes the transport.
        """
        self.sock.close()
