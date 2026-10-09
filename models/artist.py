from dataclasses import dataclass

from helpers.slug import slugify


@dataclass
class Artist:
    name: str
    bio: str = ""
    photo_url: str = ""

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Artist):
            return False
        return self.slug == other.slug

    def to_dict(self) -> dict:
        """Storage representation matching data/festival.json schema."""
        return {
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }

    def to_view(self) -> dict:
        """Public representation returned by the API."""
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }