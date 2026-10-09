from dataclasses import dataclass

from helpers.slug import slugify


@dataclass
class Venue:
    name: str
    capacity: int
    address: str

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }