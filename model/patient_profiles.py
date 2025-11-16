from model.constants import REGIMENS, PK_PD_PARAMS, RECOMMENDED_REGIMENS, REGIMEN_DURATION

def get_recommended_for_subtype(subtype: str):
    """Список имён схем, рекомендованных для данного подтипа."""
    return [item["name"] for item in RECOMMENDED_REGIMENS.get(subtype, [])]




def choose_optimal_regimen(subtype: str, ki67: float, stage: int, lymph_nodes_pos: int):
    """Пример простой логики выбора оптимальной схемы.

    Это эвристика, её можно уточнять вместе с онкологом.
    """

    if subtype == "TNBC":
        if stage >= 4:
            return "PLATINUM"
        if ki67 > 40:

            return "AC_T"
        else:
            if stage == 1:
                return "TC"
            else:
                return "AC_T"


    if subtype == "HER2+":
        if stage == 1:
            return "T_paclitaxel"
        if stage in [2, 3]:
            return "AC_T"
        if stage >= 4:
            return "T_mono"  
        return "T_paclitaxel"


    if subtype == "HR+":
        if ki67 < 15:
            return "LET"
        elif 15 <= ki67 <= 30:
            if stage >= 2:
                return "TC"
            return "LET"
        else: 
            if lymph_nodes_pos > 0:
                return "AC_T"
            return "TC"

    return None

def select_regimen_for_patient(subtype: str,
                               ki67: float,
                               stage: int,
                               lymph_nodes_pos: int,
                               doctor_choice: str | None = None,
                               drug_choice: str | None = None):
    """
    subtype: 'HR+', 'HER2+', 'TNBC'
    doctor_choice: выбранная схема (например 'AC_T')
    drug_choice: выбранный препарат (например 'paclitaxel')
    """

    recommended_regimens = get_recommended_for_subtype(subtype)
    available_drugs = list(PK_PD_PARAMS.keys())


    if drug_choice is not None:
        if drug_choice in available_drugs:
            print(f"Врач выбрал препарат {drug_choice} — создаём моно-схему.")

            REGIMENS[f"mono_{drug_choice}"] = {
                "description": f"Monotherapy: {drug_choice}",
                "drugs": [drug_choice]
            }
            return f"mono_{drug_choice}"
        else:
            print("Препарат не найден в базе — проигнорировано.")

    if doctor_choice is not None:
        if doctor_choice in recommended_regimens:
            return doctor_choice
        else:
            print(" Схема не в рекомендациях, но принимаем.")
            return doctor_choice


    auto = choose_optimal_regimen(subtype, ki67, stage, lymph_nodes_pos)
    return auto

def get_default_t_end(regimen_name):
    return REGIMEN_DURATION.get(regimen_name, 365)