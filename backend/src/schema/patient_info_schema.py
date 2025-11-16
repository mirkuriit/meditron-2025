from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

harmon_type = Literal[
    "Летрозол",
    "Анастрозол", 
    "Фулвестрант",
    "Бусерелин",
    "Торемифен",
    "Тамоксифен → ингибиторы ароматазы"
]

HER2_type = Literal[
    "(DC + трастузумаб) × 4–6",
    "DCН × 6", 
    "DCН + пертузумаб × 6",
    "(Р + трастузумаб) × 12",
    "AC × 4 → (D + трастузумаб) × 4",
    "AC × 4 → (Р + трастузумаб) × 12",
    "ddAC × 4 → (Р + трастузумаб) × 12",
    "ddАС × 4 → (Р + трастузумаб) × 4",
    "АС × 4 → (таксаны+ трастузумаб + пертузумаб) × 4",
    "Трастузумаб эмтанзин × 14",
    "ddАС × 4 → ddP × 4 АС",
    "ddАC × 4 → P × 12 АС",
    "ddАC × 4 → P + С × 12 АС", 
    "DC × 4–6",
    "AC × 4",
    "AC × 4 → D × 4",
    "AC × 4 → P × 12",
    "Капецитабин (монотерапия)",
    "Олапариб"
]

HER2_treatment = Literal

class PatientInfo(BaseModel):
    first_name: str
    last_name: str
    patronymic: str
    age: int
    stage: Literal["1", "2", "3", "4"]
    menopausal_status: bool
    family_history: bool
    er_status: bool
    pr_status: bool
    her2_status: bool
    brca_mutation: bool
    ki67_level: float
    tnbc: bool
    harmon: bool
    surgery_type: bool
    HER2_treatment: HER2_type
    harmon_treatment: harmon_type
    tumor_size_before: int
    positive_lymph_nodes: int
    tumor_grade: int
    performance_status: int
    met_bone: bool
    met_brain: bool
    met_liver: bool
    met_lung: bool
    met_none: bool


    @field_validator('tumor_size_before')
    def tumor_size_before_validate(cls, value):
        if value not in list(range(0, 501)):
            raise ValueError('tumor_size_before must be in [0...500] range')
        return value
    

    @field_validator('positive_lymph_nodes')
    def positive_lymph_nodes_validate(cls, value):
        if value not in list(range(0, 17)):
            raise ValueError('positive_lymph_nodes must be in [0...15] range')
        return value
    
    @field_validator('tumor_grade')
    def tumor_grade_validate(cls, value):
        if value not in list(range(1, 4)):
            raise ValueError('tumor_grade must be in [1, 2, 3] range')
        return value

    @field_validator('performance_status')
    def performance_status_validate(cls, value):
        if value not in list(range(0, 5)):
            raise ValueError('performance_status must be in [0..4] range')
        return value





