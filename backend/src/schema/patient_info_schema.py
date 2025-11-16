from pydantic import BaseModel, Field, field_validator
from typing import Optional

# {
#   "first_name": "string",
#   "last_name": "string", 
#   "patronymic": "string",
#   "age": 45,
#   "menopausal_status": true,
#   "family_history": false,
#   "er_status": true,
#   "pr_status": false,
#   "her2_status": true,
#   "brca_mutation": false,
#   "ki67_level": 8.6,
#   "tumor_size_before": Optional[0...500],
#   "positive_lymph_nodes": Optional[0...15],
#   "has_metastasis": false, 
#   "tumor_grade": Optional[1, 2, 3],
#   "performance_status": Optional[0, 1, 2, 3, 4]
# }


class PatientInfo(BaseModel):
    first_name: str
    last_name: str
    patronymic: str
    age: int
    menopausal_status: bool
    family_history: bool
    er_status: bool
    pr_status: bool
    her2_status: bool
    brca_mutation: bool
    ki67_level: float
    tumor_size_before: int
    positive_lymph_nodes: int
    has_metastasis: bool
    tumor_grade: int
    performance_status: int


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





