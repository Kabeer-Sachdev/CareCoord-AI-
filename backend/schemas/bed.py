from typing import Optional, Literal
from pydantic import BaseModel, Field

BED_TYPES = Literal["General", "ICU", "Emergency", "Private"]
BED_STATUS_TYPES = Literal["available", "occupied", "maintenance"]

class BedBase(BaseModel):
    ward: str = Field(..., example="Ward A")
    bed_type: BED_TYPES = Field(..., example="ICU")
    status: BED_STATUS_TYPES = Field(default="available", example="available")
    floor: int = Field(..., ge=0, example=2)
    patient_id: Optional[str] = Field(None, example="P001")


class BedCreate(BedBase):
    bed_id: Optional[str] = Field(None, example="B001")


class BedUpdate(BaseModel):
    ward: Optional[str] = None
    bed_type: Optional[BED_TYPES] = None
    status: Optional[BED_STATUS_TYPES] = None
    floor: Optional[int] = Field(None, ge=0)
    patient_id: Optional[str] = None


class BedResponse(BedBase):
    id: int
    bed_id: str

    class Config:
        from_attributes = True
