from uuid import UUID

from fastapi import APIRouter, Depends
from src.schema.patient_info_schema import PatientInfo
from src.schema.reports_schema import TreatmentType, TumorDynamic, SurvivalMonthReport


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/survival_month", response_model=SurvivalMonthReport)
async def get_survival_month(
    user: PatientInfo,
):
    return SurvivalMonthReport(month=10)


@router.post("/tumor_dynamic", response_model=TumorDynamic)
async def get_tumor_dynamic(
    user: PatientInfo,
):
    return TumorDynamic(t=list(range(10)), indicator=list(range(0, 100, 10)))