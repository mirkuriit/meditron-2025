from uuid import UUID

from loguru import logger

from fastapi import APIRouter, Depends
from src.schema.patient_info_schema import PatientInfo
from src.schema.reports_schema import TreatmentType, TumorDynamic, SurvivalMonthReport
from src.ml.model import global_predictor

router = APIRouter(prefix="/reports", tags=["reports"])



@router.post("/survival_month", response_model=SurvivalMonthReport)
async def get_survival_month(
    user: PatientInfo,
):  
    user_dict = user.model_dump()
    stage = int(user_dict["stage"])
    user_dict = {k: v for k, v in user_dict.items()} | {"treatment":"surgery_chemo"}
    model_response = global_predictor.predict(stage=stage, patient_data=user_dict)

    return SurvivalMonthReport(month=round(model_response.get("predicted_survival_months")))


@router.post("/tumor_dynamic", response_model=TumorDynamic)
async def get_tumor_dynamic(
    user: PatientInfo,
):
    return TumorDynamic(t=list(range(10)), indicator=list(range(0, 100, 10)))