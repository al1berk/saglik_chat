# Klinik Pydantic şemaları (veri doğrulama)
from pydantic import BaseModel
from typing import Optional

class ClinicBase(BaseModel):
    name: str
    city: str
    address: str
    specialty: str
    rating: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None

class ClinicCreate(ClinicBase):
    pass

class Clinic(ClinicBase):
    id: int

    class Config:
        orm_mode = True
