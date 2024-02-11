import aiogossip

peer = aiogossip.Peer(port=12345)


@peer.subscribe
async def handler(msg, addr):
    print(f"Handler received {msg} from {addr}")


if __name__ == "__main__":
    peer.run()
