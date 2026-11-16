from typing import Optional, Literal
from pydantic import BaseModel, Field

BED_TYPES = Literal["General", "ICU", "Emergency", "Private"]
BED_STATUS_TYPES = Literal["available", "occupied", "maintenance", "reserved"]

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


class BedStatusUpdate(BaseModel):
    status: BED_STATUS_TYPES = Field(..., example="occupied")
    patient_id: Optional[str] = Field(None, example="P001")
    notes: Optional[str] = Field(None, example="Patient admitted to ICU")


class BedTransferRequest(BaseModel):
    patient_id: str = Field(..., example="P001")
    from_bed_id: str = Field(..., example="B001")
    to_bed_id: str = Field(..., example="B002")
    reason: Optional[str] = Field(None, example="Step-down transfer from ICU to General ward")


class BedResponse(BedBase):
    id: int
    bed_id: str

    class Config:
        from_attributes = True
