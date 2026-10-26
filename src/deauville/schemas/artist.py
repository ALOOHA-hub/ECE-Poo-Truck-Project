from pydantic import BaseModel, Field


class ArtistCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full artist name")
    bio: str = Field(default="", description="Artist biography")
    photo_url: str = Field(default="", description="Artist photo URL")