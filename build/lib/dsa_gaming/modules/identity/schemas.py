from pydantic import BaseModel


class AdminSignup(BaseModel):
    name: str = ""
    email: str
    password: str
    secret: str
