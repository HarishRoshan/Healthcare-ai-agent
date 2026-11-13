from pydantic import BaseModel, Field


class PatientInput(BaseModel):
    patient_id: int = Field(gt=0, strict=True)