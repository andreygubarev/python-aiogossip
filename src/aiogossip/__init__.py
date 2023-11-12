import asyncio
import json
import os
import random
import socket
import uuid


class Node:
    GOSSIP_INTERVAL = 5

    def __init__(self, port=50000, loop=None):
        self.loop = loop or asyncio.get_running_loop()

        self.id = uuid.uuid4()
        self.address = ("0.0.0.0", port)

        self.peers = {}

        # Shared socket for sending and receiving
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.sock.setblocking(False)

    async def listen(self):
        while True:
            data, addr = await self.loop.sock_recvfrom(self.sock, 1024)
            message = json.loads(data.decode())
            await self.handle(addr, message)

    async def connect(self, seed):
        message = {
            "id": str(self.id),
            "peers": self.peers,
        }
        await self.send(message, seed)

    async def gossip(self):
        while True:
            await asyncio.sleep(self.GOSSIP_INTERVAL)
            message = {
                "id": str(self.id),
                "peers": self.peers,
            }

            peers = set(self.peers) - {self.id}
            peers = random.sample(sorted(peers), k=len(peers))
            peers = [self.peers[p] for p in peers]
            print(f"Selected peers: {peers}")

            for peer in peers:
                await self.send(message, peer)

    async def send(self, message, peer):
        await self.loop.sock_sendto(self.sock, json.dumps(message).encode(), peer)

    async def handle(self, addr, message):
        self.peers[message["id"]] = addr
        for p in message["peers"]:
            self.peers[p] = tuple(message["peers"][p])


async def main():
    port = os.getenv("PORT")
    assert port is not None, "PORT environment variable must be set"
    port = int(port)

    node = Node(port=port)
    listen_task = asyncio.create_task(node.listen())
    gossip_task = asyncio.create_task(node.gossip())

    seed = os.getenv("SEED")
    if seed is not None:
        seed = seed.split(":")
        seeds = [(seed[0], int(seed[1]))]
        await node.connect(seeds[0])

    await asyncio.gather(listen_task, gossip_task)


if __name__ == "__main__":
    asyncio.run(main())
