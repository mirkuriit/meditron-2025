from pydantic import BaseModel


class SurvivalMonthReport(BaseModel):
    month: int


class DrugDrug(BaseModel):
    base_dose: float
    optimized_dose: float


class DoseGraphReport(BaseModel):
    ok: bool
    t: list[float]
    V: list[float]
    Ns: list[float]
    Nr: list[float]
    N: list[float]
    doses: dict[str, DrugDrug]


class TreatmentType(BaseModel):
    pass