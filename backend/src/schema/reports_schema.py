from pydantic import BaseModel


class SurvivalMonthReport(BaseModel):
    month: int


class TumorDynamic(BaseModel):
    t: list[int]
    indicator: list[int]


class TreatmentType(BaseModel):
    pass