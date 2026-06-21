from pydantic import BaseModel, Field
from uuid import uuid4

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    username: str
    hashed_password: str
    emailaddress: str

    class Config:
        allow_population_by_field_name = True