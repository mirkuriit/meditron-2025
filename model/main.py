# main.py
from pkpd import simulate_patient
from optimization import optimize_treatment
from patient_profiles import select_regimen_for_patient
from constants import REGIMENS

def test_model():
    # Пример пациента
    patient = {
        "age": 55,
        "weight": 70.0,
        "cancer_type": "TNBC",
        "tumor_size": 40.0,
        "ki67": 0.45,
        "treatment_response": "PD"
    }

    print("📋 Доступные схемы:", REGIMENS.keys())

    # Запуск оптимизации
    result = optimize_treatment(
        cancer_type=patient["cancer_type"],
        weight=patient["weight"],
        ki67=patient["ki67"],
        treatment_response=patient["treatment_response"],
        mode="auto_best"
    )

    print("✅ Результат оптимизации:", result["summary"])

if __name__ == "__main__":
    test_model()
