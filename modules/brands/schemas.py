from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    logo_url: str | None = None


class BrandOut(BaseModel):
    id: int
    name: str
    logo_url: str | None

    class Config:
        from_attributes = True
