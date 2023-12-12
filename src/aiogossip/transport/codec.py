from ..types_pb2 import Message


def decode(data: bytes) -> Message:
    """
    Decode the given data using the Message.FromString method.

    Args:
        data (bytes): The data to be decoded.

    Returns:
        Message: The decoded message object.
    """
    return Message.FromString(data)


def encode(data: Message) -> bytes:
    """
    Encodes the given data object into a serialized byte string.

    Args:
        data: The data object to be encoded.

    Returns:
        str: The serialized string representation of the data object.
    """
    return data.SerializeToString()
