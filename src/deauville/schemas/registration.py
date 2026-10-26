from pydantic import BaseModel, Field


class WorkshopRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Participant name")