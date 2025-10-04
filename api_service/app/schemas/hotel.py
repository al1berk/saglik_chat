# Otel Pydantic şemaları (veri doğrulama)
from pydantic import BaseModel
from typing import Optional

class HotelBase(BaseModel):
    name: str
    city: str
    address: str
    rating: Optional[float] = None
    price_per_night: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    distance_to_clinic: Optional[float] = None

class HotelCreate(HotelBase):
    pass

class Hotel(HotelBase):
    id: int

    class Config:
        orm_mode = True
