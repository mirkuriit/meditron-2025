from pydantic import BaseModel


class PatientInfo(BaseModel):
    first_name: str
    last_anme: str
    patronymic: str



