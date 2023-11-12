import asyncio
import json
import os
import random
import socket
import time


class ServerNode:
    def __init__(self, address, peers):
        self.address = address
        self.peers = peers
        self.configuration = {"timestamp": time.time(), "data": {}}
        self.gossip_interval = 5  # seconds

        # Shared socket for sending and receiving
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.sock.setblocking(False)

    async def listen(self):
        loop = asyncio.get_running_loop()
        while True:
            data, addr = await loop.sock_recvfrom(self.sock, 1024)
            message = json.loads(data.decode())
            print(f"Received message from {addr}: {message}")
            await self.handle_incoming_message(message)

    async def gossip(self):
        while True:
            await asyncio.sleep(self.gossip_interval)
            message = {
                "type": "gossip",
                "timestamp": self.configuration["timestamp"],
                "data": self.configuration["data"],
            }
            selected_peers = random.sample(self.peers, k=len(self.peers))
            for peer in selected_peers:
                await self.send_message(message, peer)

    async def send_message(self, message, peer):
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(self.sock, json.dumps(message).encode(), peer)

    async def handle_incoming_message(self, message):
        # Update configuration if the incoming message is newer
        if message["timestamp"] > self.configuration["timestamp"]:
            self.configuration.update(message)


async def main():
    address = os.getenv("ADDRESS")
    assert address is not None, "ADDRESS environment variable must be set"
    address = address.split(":")
    address = (address[0], int(address[1]))
    print(f"Starting node at {address}")

    peer = os.getenv("PEER")
    if peer is None:
        peers = []
    else:
        peer = peer.split(":")
        peers = [(peer[0], int(peer[1]))]

    node = ServerNode(address, peers)
    listen_task = asyncio.create_task(node.listen())
    gossip_task = asyncio.create_task(node.gossip())

    await asyncio.gather(listen_task, gossip_task)


if __name__ == "__main__":
    asyncio.run(main())
