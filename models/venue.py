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
        """Storage representation matching data/festival.json schema."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }

    def to_view(self) -> dict:
        """Public representation returned by the API."""
        return {
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }