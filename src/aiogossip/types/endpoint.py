import dataclasses

from .address import Address


@dataclasses.dataclass(frozen=True, slots=True)
class Endpoint:
    """
    Dataclass that represents a network endpoint consisting of pair of addresses (source and destination).
    """

    saddr: Address | None = None
    daddr: Address | None = None

    def __post_init__(self):
        if self.saddr and not isinstance(self.saddr, Address):
            raise TypeError("saddr must be Address")

        if self.daddr and not isinstance(self.daddr, Address):
            raise TypeError("daddr must be Address")
