from uuid import UUID
from typing import Literal

from loguru import logger

from fastapi import APIRouter, Depends
from src.schema.patient_info_schema import PatientInfo
from src.schema.reports_schema import TreatmentType, SurvivalMonthReport
from src.schema.reports_schema import DoseGraphReport

from src.ml.model import predictor as survivor_predictor
from src.math_models.core import run_simulation, subtype_from_markers


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/survival_month", response_model=SurvivalMonthReport)
async def get_survival_month(
    user: PatientInfo,
):  
    user_dict = user.model_dump()
    stage = int(user_dict["stage"])
    user_dict = {k: v for k, v in user_dict.items()} | {"treatment":"surgery_chemo"}
    model_response = survivor_predictor.predict(stage=stage, patient_data=user_dict)

    return SurvivalMonthReport(month=round(model_response.get("predicted_survival_months")))


### Честное слово я бы отделил ручки по назначению отдельно для получения графиков, отдельно для получения рекомендуемых доз
### если бы нашим фронтендером не был оператор чатагпт
### можно добавление нового поля не будет часовым аттракционом по попытке что-то сгенерить и не сломать все остальное?
### памагите, у меня ощущение, что я тут единственный кто понимает что в его коде происходит
### кстати, вот мое резюме https://docs.google.com/document/d/1YF_cgOvo5mpiIx7_0mhIQP8dA1k8nsL5OY0Hh1EP3gs/edit?usp=sharing
@router.post("/tumor_dynamic", response_model=DoseGraphReport)
async def get_tumor_dynamic(
    user: PatientInfo,
):  
    subtype: Literal["HR+", "HER2+", "TNBC"] = subtype_from_markers(er_status=user.er_status,
                                   pr_status=user.pr_status,
                                   her2_status=user.her2_status)
    params = {
        "subtype": subtype,          
        "ki67": user.ki67_level,
        "tumor_size_cm": user.tumor_size_before,
        "regimen": user.HER2_treatment,
    }
    results = run_simulation(params=params)
    #DoseGraphReport()
    #logger.info(results)
    return results