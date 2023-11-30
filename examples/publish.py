"""
Usage:
    GOSSIP_SEEDS=4aed4f3c6900462baa1413fb7ef4f814@127.0.0.1:58295 python examples/members.py
"""
import os

import aiogossip

peer = aiogossip.Peer()


async def main():
    await peer.publish("topic", {"metadata": {}, "payload": "payload"})


if __name__ == "__main__":
    print("dsn:", peer.dsn)
    seeds = os.getenv("GOSSIP_SEEDS")
    peer.connect(seeds)
    peer.run_forever(main=main)
