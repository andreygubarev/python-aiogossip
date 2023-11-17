import asyncio
import os
import uuid

from . import channel, transport


class GossipOperation:
    PING = 1
    ACK = 2
    QUERY = 3

    def __init__(self, gossip):
        self.gossip = gossip

    async def ack(self, addr, topic):
        await self.gossip.send(self.ACK, {}, addr, topic=topic)
        return topic

    async def ping(self, addr):
        topic = str(uuid.uuid4())
        recv = self.gossip.loop.create_task(self.gossip.channel.recv(topic))
        await self.gossip.send(self.PING, {}, addr, topic=topic)
        await recv
        await self.gossip.channel.close(topic)
        return topic

    async def query(self, addr, data):
        topic = str(uuid.uuid4())

        recv = self.gossip.channel.recv(topic)
        recv = self.gossip.loop.create_task(recv)
        await self.gossip.send(self.QUERY, data, addr, topic=topic)

        r = []
        while len(r) <= len(self.gossip.node_peers):
            r.append(await recv)

        await self.gossip.channel.close(topic)

        print("Query result:", r)
        return r


class Gossip:
    TRANSPORT = transport.Transport
    INTERVAL = 1
    TIMEOUT = 5

    def __init__(self, bind, loop=None):
        self.loop = loop or asyncio.get_running_loop()
        self.transport = self.TRANSPORT(bind, loop=self.loop)

        self.node_id = uuid.uuid4()
        self.node_peers = {}
        self.channel = channel.Channel()

        self.tasks = []
        self.tasks.append(self.loop.create_task(self._recv()))
        self.tasks.append(self.loop.create_task(self._ping()))

        self.op = GossipOperation(self)

    async def _recv(self):
        while True:
            message, addr = await self.transport.recv()
            message["metadata"]["sender_addr"] = addr

            metadata = message["metadata"]
            if metadata["sender_id"] not in self.node_peers:
                self.node_peers[metadata["sender_id"]] = metadata["sender_addr"]

            await self.channel.send("gossip", message)

    async def _ping(self):
        # Round-Robin Probe Target Selection
        # https://en.wikipedia.org/wiki/SWIM_Protocol#Extensions
        while True:
            if not self.node_peers:
                await asyncio.sleep(self.INTERVAL)
                continue

            for peer_id in self.node_peers:
                await asyncio.sleep(self.INTERVAL)
                addr = self.node_peers[peer_id]
                await self.op.ping(addr)

    async def recv(self):
        while True:
            message = await self.channel.recv("gossip")
            # print(f"Received message: {message}")
            metadata = message["metadata"]

            if metadata.get("sender_topic") in self.channel:
                await self.channel.send(metadata["sender_topic"], message)

            message_type = metadata["message_type"]
            if message_type == GossipOperation.PING:
                await self.op.ack(
                    metadata["sender_addr"], topic=metadata["sender_topic"]
                )
                continue
            elif message_type == GossipOperation.ACK:
                continue

            yield message

    async def send(self, message_type, data, addr, topic=None):
        data = {
            "metadata": {
                "sender_id": str(self.node_id),
                "sender_topic": topic,
                "message_id": str(uuid.uuid4()),
                "message_type": message_type,
            },
            "data": data,
        }
        await self.transport.send(data, addr)


class Node:
    def __init__(self, host="0.0.0.0", port=49152, loop=None):
        self.loop = loop or asyncio.get_running_loop()
        self.gossip = Gossip((host, port), loop=self.loop)
        self.channel = channel.Channel()

    async def recv(self):
        async for message in self.gossip.recv():
            await self.handle(message)

    async def handle(self, message):
        print(f"Handling message: {message}")
        await self.gossip.op.ack(
            message["metadata"]["sender_addr"],
            topic=message["metadata"]["sender_topic"],
        )


async def query(node, peer):
    await asyncio.sleep(3)
    await node.gossip.op.query(peer, {"foo": "bar"})


async def main():
    print("Starting node...")
    port = os.getenv("PORT")
    assert port is not None, "PORT environment variable must be set"
    port = int(port)

    node = Node(port=port)
    recv_task = asyncio.create_task(node.recv())

    seed = os.getenv("SEED")
    if seed is not None:
        seed = seed.split(":")
        seed = (seed[0], int(seed[1]))
        await node.gossip.op.ping(seed)
        asyncio.create_task(query(node, seed))

    await asyncio.gather(recv_task, *node.gossip.tasks)


if __name__ == "__main__":
    asyncio.run(main())
