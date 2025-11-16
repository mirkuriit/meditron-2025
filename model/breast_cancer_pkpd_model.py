
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Callable, Optional

from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d

# =============================================================
# 1. Популяционные параметры роста опухоли
# =============================================================

TIME_POINTS_MONTHS = np.array([0, 3, 6, 12, 24])

T_cycle_dict = {
    "HR+": 3.0,
    "HER2+": 2.0,
    "TNBC": 1.0,
}

params_pop: Dict[str, Dict[str, float]] = {
    "HR+": {
        "d": 0.01,
        "k_clear": 0.001,
        "K": 800.0,
        "f_N0": 0.2,
    },
    "HER2+": {
        "d": 0.012,
        "k_clear": 0.001,
        "K": 700.0,
        "f_N0": 0.25,
    },
    "TNBC": {
        "d": 0.015,
        "k_clear": 0.0015,
        "K": 600.0,
        "f_N0": 0.3,
    },
}


def r_from_ki67(ki67_fraction: float, T_cycle_days: float) -> float:
    return (np.log(2) / T_cycle_days) * ki67_fraction


# =============================================================
# 2. PK/PD ПАРАМЕТРЫ ПРЕПАРАТОВ
# =============================================================

PK_PD_PARAMS: Dict[str, Dict[str, float]] = {
    "docetaxel": {
        "dose_mg_per_m2": 75.0,
        "schedule": "q3w",
        "CL": 15.0,
        "Q": 10.0,
        "V1": 15.0,
        "V2": 40.0,
        "E_max": 0.35,
        "EC50": 0.5,
    },
    "cyclophosphamide": {
        "dose_mg_per_m2": 600.0,
        "schedule": "q3w",
        "CL": 10.0,
        "Q": 6.0,
        "V1": 20.0,
        "V2": 55.0,
        "E_max": 0.28,
        "EC50": 0.6,
    },
    "doxorubicin": {
        "dose_mg_per_m2": 60.0,
        "schedule": "q3w",
        "CL": 12.0,
        "Q": 8.0,
        "V1": 20.0,
        "V2": 50.0,
        "E_max": 0.40,
        "EC50": 0.4,
    },
    "paclitaxel": {
        "dose_mg_per_m2": 80.0,
        "schedule": "weekly",
        "CL": 20.0,
        "Q": 10.0,
        "V1": 15.0,
        "V2": 35.0,
        "E_max": 0.30,
        "EC50": 0.7,
    },
    "trastuzumab_sc": {
        "dose_mg_fixed": 600.0,
        "schedule": "q3w",
        "CL": 0.5,
        "Q": 0.3,
        "V1": 3.0,
        "V2": 4.0,
        "E_max": 0.15,
        "EC50": 0.2,
    },
    "letrozole": {
        "dose_mg_fixed": 2.5,
        "schedule": "daily",
        "CL": 0.25,
        "Q": 0.0,
        "V1": 100.0,
        "V2": 0.0,
        "E_max": 0.12,
        "EC50": 0.05,
    },
    "tamoxifen": {
        "dose_mg_fixed": 20.0,
        "schedule": "daily",
        "CL": 0.2,
        "Q": 0.0,
        "V1": 120.0,
        "V2": 0.0,
        "E_max": 0.10,
        "EC50": 0.03,
    },
    "anastrozole": {
        "dose_mg_fixed": 1.0,
        "schedule": "daily",
        "CL": 0.15,
        "Q": 0.0,
        "V1": 80.0,
        "V2": 0.0,
        "E_max": 0.12,
        "EC50": 0.04,
    },
    "zoledronic_acid": {
        "dose_mg_fixed": 4.0,
        "schedule": "q6m",
        "CL": 5.0,
        "Q": 2.0,
        "V1": 6.0,
        "V2": 12.0,
        "E_max": 0.05,
        "EC50": 0.3,
    },
    "carboplatin": {
        "dose_mg_per_m2": 600.0,
        "schedule": "q3w",
        "CL": 10.0,
        "Q": 5.0,
        "V1": 20.0,
        "V2": 40.0,
        "E_max": 0.25,
        "EC50": 0.5,
    },
}


# Сетка доз и интервалов для грид-поиска
DOSE_INTERVAL_GRID: Dict[str, Dict] = {
    "doxorubicin": {
        "type": "mg_per_m2",
        "doses": list(range(50, 71, 10)),
        "intervals": ["q3w", "q2w"],
    },
    "cyclophosphamide": {
        "type": "mg_per_m2",
        "doses": list(range(500, 701, 50)),
        "intervals": ["q3w", "q2w"],
    },
    "docetaxel": {
        "type": "mg_per_m2",
        "doses": list(range(60, 101, 10)),
        "intervals": ["q3w"],
    },
    "paclitaxel": {
        "type": "mg_per_m2",
        "doses": [60, 80, 100, 150, 175],
        "intervals": ["weekly", "q2w"],
    },
    "trastuzumab_sc": {
        "type": "fixed_mg",
        "doses": [600],
        "intervals": ["q3w"],
    },
    "letrozole": {
        "type": "fixed_mg",
        "doses": [2.5],
        "intervals": ["daily"],
    },
    "tamoxifen": {
        "type": "fixed_mg",
        "doses": [20],
        "intervals": ["daily"],
    },
    "anastrozole": {
        "type": "fixed_mg",
        "doses": [1.0],
        "intervals": ["daily"],
    },
    "zoledronic_acid": {
        "type": "fixed_mg",
        "doses": [4.0],
        "intervals": ["q6m"],
    },
    "carboplatin": {
        "type": "mg_per_m2",
        "doses": list(range(300, 601, 50)),
        "intervals": ["q3w"],
    },
}


# Базовые схемы (для оптимизации)
REGIMENS: Dict[str, Dict] = {
    "TC": {
        "description": "Docetaxel + Cyclophosphamide",
        "drugs": ["docetaxel", "cyclophosphamide"],
    },
    "AC": {
        "description": "Doxorubicin + Cyclophosphamide",
        "drugs": ["doxorubicin", "cyclophosphamide"],
    },
    "AC_T": {
        "description": "Doxorubicin + Cyclophosphamide followed by Paclitaxel",
        "phases": [
            {"duration": 84.0, "drugs": ["doxorubicin", "cyclophosphamide"]},
            {"duration": 84.0, "drugs": ["paclitaxel"]},
        ],
    },
    "T_paclitaxel": {
        "description": "Trastuzumab + Paclitaxel",
        "drugs": ["trastuzumab_sc", "paclitaxel"],
    },
    "T_mono": {
        "description": "Trastuzumab monotherapy",
        "drugs": ["trastuzumab_sc"],
    },
    "LET": {
        "description": "Letrozole monotherapy",
        "drugs": ["letrozole"],
    },
    "TAM": {
        "description": "Tamoxifen monotherapy",
        "drugs": ["tamoxifen"],
    },
    "ANA": {
        "description": "Anastrozole monotherapy",
        "drugs": ["anastrozole"],
    },
    "BONE": {
        "description": "Zoledronic acid",
        "drugs": ["zoledronic_acid"],
    },
    "PLATINUM": {
        "description": "Carboplatin",
        "drugs": ["carboplatin"],
    },
}

NON_PHASE_REGIMENS = {"TC", "AC", "T_paclitaxel", "LET", "TAM", "ANA", "BONE", "PLATINUM"}


# Рекомендованные схемы по подтипу (для режима auto_best)
RECOMMENDED_REGIMENS: Dict[str, List[Dict[str, str]]] = {
    "HR+": [
        {"name": "LET", "comment": "ГТ ± овариальная супрессия"},
        {"name": "TC", "comment": "Доцетаксел + циклофосфамид 4–6 циклов"},
        {"name": "AC", "comment": "AC/EC 4 цикла"},
        {"name": "AC_T", "comment": "AC/EC → таксан"},
    ],
    "HER2+": [
        {"name": "T_paclitaxel", "comment": "Таксан + трастузумаб"},
        {"name": "T_mono", "comment": "Поддерживающий трастузумаб"},
        {"name": "AC_T", "comment": "AC → таксан → анти-HER2"},
    ],
    "TNBC": [
        {"name": "AC", "comment": "Антрациклины"},
        {"name": "TC", "comment": "Доцетаксел + циклофосфамид"},
        {"name": "AC_T", "comment": "AC → таксаны"},
        {"name": "PLATINUM", "comment": "Платина (карбоплатин)"},
    ],
}


def get_recommended_for_subtype(subtype: str) -> List[str]:
    return [item["name"] for item in RECOMMENDED_REGIMENS.get(subtype, [])]


# =============================================================
# 3. PK ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================

def E_of_C(C: np.ndarray, E_max: float, EC50: float) -> np.ndarray:
    return E_max * C / (C + EC50 + 1e-12)


def pk_input_cycles(t: float, cycle_len: float = 21.0, dose_amount: float = 100.0) -> float:
    if abs(t % cycle_len) < 1e-6:
        return dose_amount
    return 0.0


def pk_one_comp_ode(t, y, CL, V1, input_func=None):
    A = y[0]
    I = input_func(t) if input_func else 0.0
    dA_dt = -(CL / V1) * A + I
    return [dA_dt]


def pk_two_comp_ode(t, y, CL, Q, V1, V2, input_func=None):
    A1, A2 = y
    I = input_func(t) if input_func else 0.0

    dA1dt = -(CL / V1) * A1 - (Q / V1) * A1 + (Q / V2) * A2 + I
    dA2dt = (Q / V1) * A1 - (Q / V2) * A2
    return [dA1dt, dA2dt]


def simulate_pk_two_comp(
    CL: float,
    Q: float,
    V1: float,
    V2: float,
    y0: List[float],
    t_end: float,
    n_points: int = 2000,
    input_func: Optional[Callable[[float], float]] = None,
) -> Callable[[float], float]:

    t_eval = np.linspace(0.0, t_end, n_points)

    sol = solve_ivp(
        lambda tt, yy: pk_two_comp_ode(tt, yy, CL, Q, V1, V2, input_func),
        [0.0, t_end],
        y0,
        t_eval=t_eval,
    )

    A1 = sol.y[0]
    C1 = A1 / V1
    C_interp = interp1d(t_eval, C1, fill_value="extrapolate")
    return C_interp


def build_single_drug_pkpd(
    drug_name: str,
    t_end: float = 365.0,
    bsa: float = 1.7,
    dose_abs_override: Optional[float] = None,
    schedule_override: Optional[str] = None,
):
    if drug_name not in PK_PD_PARAMS:
        raise ValueError(f"Препарат {drug_name} отсутствует в PK_PD_PARAMS")

    p = PK_PD_PARAMS[drug_name]
    CL, Q, V1, V2 = p["CL"], p["Q"], p["V1"], p["V2"]
    is_one_comp = (Q == 0 or V2 == 0)

    E_max, EC50 = p["E_max"], p["EC50"]
    schedule = schedule_override if schedule_override is not None else p["schedule"]

    if dose_abs_override is not None:
        dose_abs = dose_abs_override
    else:
        if "dose_mg_per_m2" in p:
            dose_abs = p["dose_mg_per_m2"] * bsa
        elif "dose_mg_fixed" in p:
            dose_abs = p["dose_mg_fixed"]
        else:
            raise ValueError(f"Не найдена доза для препарата {drug_name}")

    if schedule == "q3w":
        cycle = 21.0
        input_func = lambda tt, d=dose_abs, c=cycle: pk_input_cycles(tt, c, d)
        y0 = [0.0, 0.0]
    elif schedule == "q2w":
        cycle = 14.0
        input_func = lambda tt, d=dose_abs, c=cycle: pk_input_cycles(tt, c, d)
        y0 = [0.0, 0.0]
    elif schedule == "weekly":
        cycle = 7.0
        input_func = lambda tt, d=dose_abs, c=cycle: pk_input_cycles(tt, c, d)
        y0 = [0.0, 0.0]
    elif schedule == "daily":
        cycle = 1.0
        input_func = lambda tt, d=dose_abs, c=cycle: pk_input_cycles(tt, c, d)
        y0 = [0.0, 0.0]
    elif schedule == "q6m":
        cycle = 180.0
        input_func = lambda tt, d=dose_abs, c=cycle: pk_input_cycles(tt, c, d)
        y0 = [0.0, 0.0]
    else:
        input_func = None
        y0 = [dose_abs, 0.0]

    if is_one_comp:
        def pk_ode(tt, yy):
            return pk_one_comp_ode(tt, yy, CL, V1, input_func)

        t_eval = np.linspace(0, t_end, 2000)
        sol = solve_ivp(pk_ode, [0, t_end], [0.0], t_eval=t_eval)
        C = sol.y[0] / V1
        C_func = interp1d(t_eval, C, fill_value="extrapolate")
    else:
        C_func = simulate_pk_two_comp(
            CL, Q, V1, V2,
            y0=y0,
            t_end=t_end,
            n_points=2000,
            input_func=input_func
        )

    return C_func, E_max, EC50


# =============================================================
# 4. ODE МОДЕЛЬ ОПУХОЛИ И РЕЗИСТЕНТНОСТЬ
# =============================================================

def get_resistance_params(row_like,
                          manual_mutation_rate=None,
                          manual_resistance_strength=None):
    if manual_mutation_rate is not None and manual_resistance_strength is not None:
        return manual_mutation_rate, manual_resistance_strength

    response = None
    try:
        if hasattr(row_like, "get"):
            response = row_like.get("treatment_response", None)
        else:
            response = row_like["treatment_response"]
    except Exception:
        response = None

    if response is None:
        return None

    response = str(response).upper().strip()

    if response == "PD":
        return 0.02, 0.2
    elif response == "SD":
        return 0.01, 0.5
    elif response in ["PR", "PARTIAL RESPONSE"]:
        return 0.007, 0.7
    elif response in ["CR", "COMPLETE RESPONSE"]:
        return 0.005, 0.8
    else:
        return 0.01, 0.5


def tumor_ode_no_resistance(t, y,
                            r, K, d_base, k_clear,
                            drug_effect_func):
    U, N = y
    drug = drug_effect_func(t) if drug_effect_func is not None else 0.0
    d_eff = d_base + drug

    dUdt = r * U * (1 - (U + N) / K) - d_eff * U
    dNdt = d_eff * U - k_clear * N
    return [dUdt, dNdt]


def tumor_ode_with_resistance(t, y,
                              r, K, d_base, k_clear,
                              drug_effect_func,
                              mutation_rate, resistance_strength):
    Ns, Nr, N = y
    drug = drug_effect_func(t) if drug_effect_func is not None else 0.0

    death_s = (d_base + drug) * Ns
    death_r = (d_base + drug * resistance_strength) * Nr

    mut = mutation_rate * Ns
    U_total = Ns + Nr

    growth_s = r * Ns * (1 - (U_total + N) / K)
    growth_r = r * Nr * (1 - (U_total + N) / K)

    dNsdt = growth_s - death_s - mut
    dNrdt = growth_r - death_r + mut
    dNdt = death_s + death_r - k_clear * N

    return [dNsdt, dNrdt, dNdt]


def simulate_patient(subtype: str,
                     ki67_percent: float,
                     V0: float,
                     regimen_name: Optional[str] = None,
                     t_end: float = 365.0,
                     use_resistance: bool = False,
                     mutation_rate: Optional[float] = None,
                     resistance_strength: Optional[float] = None,
                     row_like_for_resistance=None,
                     bsa: float = 1.7,
                     drug_effect_override=None):
    pop = params_pop[subtype]
    T_cycle = T_cycle_dict[subtype]

    d_base = pop["d"]
    k_clear = pop["k_clear"]
    K = pop["K"]
    f_N0 = pop["f_N0"]

    r = r_from_ki67(ki67_percent / 100.0, T_cycle)

    if drug_effect_override is not None:
        drug_effect_func = drug_effect_override
    elif regimen_name is not None:
        drug_effect_func = make_regimen_drug_effect(
            regimen_name, t_end=t_end, bsa=bsa
        )
    else:
        drug_effect_func = lambda t: 0.0

    t_eval = np.linspace(0.0, t_end, 600)

    if not use_resistance:
        U0 = (1.0 - f_N0) * V0
        N0 = f_N0 * V0
        y0 = [U0, N0]

        sol = solve_ivp(
            lambda tt, yy: tumor_ode_no_resistance(
                tt, yy,
                r=r, K=K,
                d_base=d_base, k_clear=k_clear,
                drug_effect_func=drug_effect_func,
            ),
            [0.0, t_end],
            y0,
            t_eval=t_eval,
        )

        U, N = sol.y
        V = U + N
        return t_eval, V, U, N

    if mutation_rate is None or resistance_strength is None:
        if row_like_for_resistance is not None:
            params_res = get_resistance_params(row_like_for_resistance)
            if params_res is not None:
                mutation_rate, resistance_strength = params_res
            else:
                return simulate_patient(
                    subtype, ki67_percent, V0,
                    regimen_name=regimen_name,
                    t_end=t_end,
                    use_resistance=False,
                    bsa=bsa,
                    drug_effect_override=drug_effect_override,
                )
        else:
            return simulate_patient(
                subtype, ki67_percent, V0,
                regimen_name=regimen_name,
                t_end=t_end,
                use_resistance=False,
                bsa=bsa,
                drug_effect_override=drug_effect_override,
            )

    U0 = (1.0 - f_N0) * V0
    Ns0 = U0 * 0.95
    Nr0 = U0 * 0.05
    N0 = f_N0 * V0
    y0 = [Ns0, Nr0, N0]

    sol = solve_ivp(
        lambda tt, yy: tumor_ode_with_resistance(
            tt, yy,
            r=r, K=K,
            d_base=d_base, k_clear=k_clear,
            drug_effect_func=drug_effect_func,
            mutation_rate=mutation_rate,
            resistance_strength=resistance_strength,
        ),
        [0.0, t_end],
        y0,
        t_eval=t_eval,
    )

    Ns, Nr, N = sol.y
    V = Ns + Nr + N
    return t_eval, V, Ns, Nr, N


def simulate_patient_with_stage(
    subtype: str,
    ki67_percent: float,
    V0: float,
    stage: int,
    regimen_name: Optional[str] = None,
    t_end: float = 365.0,
    use_resistance: bool = False,
    row_like_for_resistance=None,
    bsa: float = 1.7,
    drug_effect_override=None,
):
    pop = params_pop[subtype].copy()
    K_base = pop["K"]
    f_N0_base = pop["f_N0"]

    if V0 > 0.7 * K_base:
        K_eff = max(K_base, V0 * 1.5)
    else:
        K_eff = K_base

    if stage == 3:
        K_eff *= 1.2
    elif stage >= 4:
        K_eff *= 1.4

    f_N0 = f_N0_base
    if stage == 3:
        f_N0 = min(f_N0 + 0.10, 0.60)
    elif stage >= 4:
        f_N0 = min(f_N0 + 0.20, 0.70)

    old_K = params_pop[subtype]["K"]
    old_fN = params_pop[subtype]["f_N0"]

    params_pop[subtype]["K"] = K_eff
    params_pop[subtype]["f_N0"] = f_N0

    try:
        result = simulate_patient(
            subtype=subtype,
            ki67_percent=ki67_percent,
            V0=V0,
            regimen_name=regimen_name,
            t_end=t_end,
            use_resistance=use_resistance,
            row_like_for_resistance=row_like_for_resistance,
            bsa=bsa,
            drug_effect_override=drug_effect_override,
        )
    finally:
        params_pop[subtype]["K"] = old_K
        params_pop[subtype]["f_N0"] = old_fN

    return result


# =============================================================
# 5. МОДЕЛЬ СХЕМ ЛЕЧЕНИЯ: MAKE_REGIMEN_DRUG_EFFECT, PK/PD
# =============================================================

def make_regimen_drug_effect(regimen_name: str, t_end: float = 365.0, bsa: float = 1.7):
    reg = REGIMENS[regimen_name]

    if "phases" not in reg:
        drug_names = reg["drugs"]
        pk_list = []

        for dname in drug_names:
            C_func, E_max, EC50 = build_single_drug_pkpd(dname, t_end=t_end, bsa=bsa)
            pk_list.append((C_func, E_max, EC50))

        def drug_effect(t: float) -> float:
            total = 0.0
            for C_func, E_max, EC50 in pk_list:
                C = float(C_func(t))
                total += E_of_C(C, E_max, EC50)
            return total

        return drug_effect

    phases = reg["phases"]
    pk_list = []
    t_shift = 0.0

    for phase in phases:
        duration = phase["duration"]
        drugs = phase["drugs"]

        for dname in drugs:
            C_phase, E_max, EC50 = build_single_drug_pkpd(dname, t_end=duration, bsa=bsa)

            def make_shifted(C_local, shift, dur):
                def C_global(t):
                    tau = t - shift
                    if tau < 0:
                        return 0.0
                    return float(C_local(max(tau, 0.0)))
                return C_global

            C_shifted = make_shifted(C_phase, t_shift, duration)
            pk_list.append((C_shifted, E_max, EC50))

        t_shift += duration

    def drug_effect(t: float) -> float:
        total = 0.0
        for C_func, E_max, EC50 in pk_list:
            C = C_func(t)
            total += E_of_C(C, E_max, EC50)
        return total

    return drug_effect


# =============================================================
# 6. ТОКСИЧНОСТЬ И ЧИСЛО ЦИКЛОВ
# =============================================================

TOXICITY_LIMITS: Dict[str, Optional[Dict[str, float]]] = {
    "doxorubicin": {"max_cumulative_mg_per_m2": 500},
    "epirubicin": {"max_cumulative_mg_per_m2": 900},
    "carboplatin": {"max_cumulative_mg_per_m2": 800},
    "docetaxel": None,
    "paclitaxel": None,
    "cyclophosphamide": None,
    "letrozole": None,
    "tamoxifen": None,
    "anastrozole": None,
    "trastuzumab_sc": None,
    "zoledronic_acid": None,
}

PROTOCOL_MAX_CYCLES: Dict[str, int] = {
    "doxorubicin": 6,
    "cyclophosphamide": 6,
    "docetaxel": 6,
    "paclitaxel": 12,
    "carboplatin": 6,
}


def check_toxicity(drug_name, dose_abs, interval, t_end, bsa):
    limits = TOXICITY_LIMITS.get(drug_name)
    if limits is None:
        return True

    max_mg_per_m2 = limits.get("max_cumulative_mg_per_m2")
    if max_mg_per_m2 is None:
        return True

    if interval == "q3w":
        n = int(t_end // 21)
    elif interval == "q2w":
        n = int(t_end // 14)
    elif interval == "weekly":
        n = int(t_end // 7)
    elif interval == "daily":
        n = int(t_end)
    elif interval == "q6m":
        n = int(t_end // 180)
    else:
        n = 1

    n = min(n, PROTOCOL_MAX_CYCLES.get(drug_name, n))

    dose_mg_per_m2 = dose_abs / bsa
    cumulative_dose = dose_mg_per_m2 * n

    return cumulative_dose <= max_mg_per_m2


def count_cycles(interval, t_end, drug_name):
    if interval == "q3w":
        n = int(t_end // 21)
    elif interval == "q2w":
        n = int(t_end // 14)
    elif interval == "weekly":
        n = int(t_end // 7)
    elif interval == "daily":
        n = int(t_end)
    elif interval == "q6m":
        n = int(t_end // 180)
    else:
        n = 1

    n = min(n, PROTOCOL_MAX_CYCLES.get(drug_name, n))
    return n


# =============================================================
# 7. GRID SEARCH: ОДИН ПРЕПАРАТ И СХЕМА
# =============================================================

def grid_search_single_drug(subtype: str,
                            ki67: float,
                            V0: float,
                            drug_name: str,
                            t_end: Optional[float] = None,
                            bsa: float = 1.7,
                            use_resistance: bool = False,
                            row_like_for_resistance=None,
                            objective: str = "min_final_volume",
                            doctor_fixed_interval: Optional[str] = None):
    if t_end is None:
        t_end = 365

    grid = DOSE_INTERVAL_GRID[drug_name]
    doses = grid["doses"]
    dose_type = grid["type"]

    intervals = [doctor_fixed_interval] if doctor_fixed_interval else grid["intervals"]

    best_score = np.inf
    best_result = None

    for interval in intervals:
        n_cycles = count_cycles(interval, t_end, drug_name)
        if n_cycles == 0:
            continue

        dt = {"q3w": 21, "q2w": 14, "weekly": 7, "daily": 1, "q6m": 180}.get(interval, 21)
        t_local_end = n_cycles * dt

        for dose in doses:
            dose_abs = dose * bsa if dose_type == "mg_per_m2" else dose

            if not check_toxicity(drug_name, dose_abs, interval, t_local_end, bsa):
                continue

            C_func, E_max, EC50 = build_single_drug_pkpd(
                drug_name,
                t_end=t_local_end,
                bsa=bsa,
                dose_abs_override=dose_abs,
                schedule_override=interval
            )

            def drug_eff(t):
                return E_of_C(C_func(t), E_max, EC50)

            t_vec, *rest = simulate_patient(
                subtype=subtype,
                ki67_percent=ki67,
                V0=V0,
                regimen_name=None,
                drug_effect_override=drug_eff,
                t_end=t_local_end,
                use_resistance=use_resistance,
                row_like_for_resistance=row_like_for_resistance,
                bsa=bsa
            )

            V = rest[0]
            score = V[-1] if objective == "min_final_volume" else np.min(V)

            if score < best_score:
                best_score = score
                best_result = {
                    "drug": drug_name,
                    "interval": interval,
                    "dose": dose,
                    "dose_abs": dose_abs,
                    "t": t_vec,
                    "V": V,
                    "cycles": n_cycles,
                }

    return best_result


def grid_search_regimen(
        subtype: str,
        ki67: float,
        V0: float,
        regimen_name: str,
        t_end: float = 365.0,
        bsa: float = 1.7,
        use_resistance: bool = False,
        row_like_for_resistance=None,
        objective: str = "min_final_volume"):
    if regimen_name not in REGIMENS:
        raise ValueError(f"Схема {regimen_name} не найдена")

    reg = REGIMENS[regimen_name]

    if "phases" in reg:
        raise ValueError("Фазные схемы (AC→T) не оптимизируются через этот grid search.")

    drugs = reg["drugs"]

    options_per_drug = []
    for d in drugs:
        if d not in DOSE_INTERVAL_GRID:
            raise ValueError(f"Нет сетки доз/интервалов для {d}")

        grid = DOSE_INTERVAL_GRID[d]
        dose_type = grid["type"]

        dose_abs_list = []
        for dose in grid["doses"]:
            if dose_type == "mg_per_m2":
                dose_abs_list.append(dose * bsa)
            else:
                dose_abs_list.append(dose)

        options = []
        for interval in grid["intervals"]:
            for dose_abs in dose_abs_list:
                options.append((interval, dose_abs))

        options_per_drug.append((d, options))

    best_score = np.inf
    best_result = None

    def backtrack(idx, current_choices):
        nonlocal best_score, best_result

        if idx == len(options_per_drug):
            pk_cache = []

            for drug_name, interval, dose_abs in current_choices:
                C_func, E_max, EC50 = build_single_drug_pkpd(
                    drug_name,
                    t_end=t_end,
                    bsa=bsa,
                    dose_abs_override=dose_abs,
                    schedule_override=interval
                )
                pk_cache.append((C_func, E_max, EC50))

            def drug_eff(t):
                total = 0.0
                for C_func, E_max, EC50 in pk_cache:
                    total += E_of_C(C_func(t), E_max, EC50)
                return total

            t_vec, *rest = simulate_patient(
                subtype=subtype,
                ki67_percent=ki67,
                V0=V0,
                regimen_name=None,
                drug_effect_override=drug_eff,
                t_end=t_end,
                use_resistance=use_resistance,
                row_like_for_resistance=row_like_for_resistance,
                bsa=bsa
            )

            V = rest[0]

            score = V[-1] if objective == "min_final_volume" else np.min(V)

            if score < best_score:
                best_score = score
                best_result = {
                    "regimen": regimen_name,
                    "choices": current_choices.copy(),
                    "t": t_vec,
                    "V": V,
                    "score": score,
                }
            return

        drug_name, options = options_per_drug[idx]
        for interval, dose_abs in options:
            if not check_toxicity(drug_name, dose_abs, interval, t_end, bsa):
                continue

            current_choices.append((drug_name, interval, dose_abs))
            backtrack(idx + 1, current_choices)
            current_choices.pop()

    backtrack(0, [])
    return best_result


# =============================================================
# 8. ВЫБОР СХЕМЫ (AUTO_BEST) И ОБЕРТКА optimize_treatment
# =============================================================

def choose_optimal_regimen(subtype: str, ki67: float, stage: int, lymph_nodes_pos: int):
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


def optimize_treatment(
        subtype: str,
        ki67: float,
        V0: float,
        stage: int,
        lymph_nodes_pos: int,
        mode: str = "auto_best",
        drug_name: Optional[str] = None,
        regimen_name: Optional[str] = None,
        t_end: float = 365.0,
        use_resistance: bool = False,
        row_like_for_resistance=None,
        bsa: float = 1.7,
        objective: str = "min_final_volume"):
    if mode == "single_drug":
        if drug_name is None:
            raise ValueError("Для режима 'single_drug' нужно указать drug_name")
        return grid_search_single_drug(
            subtype=subtype,
            ki67=ki67,
            V0=V0,
            drug_name=drug_name,
            t_end=t_end,
            bsa=bsa,
            use_resistance=use_resistance,
            row_like_for_resistance=row_like_for_resistance,
            objective=objective,
        )

    if mode == "single_regimen":
        if regimen_name is None:
            raise ValueError("Для режима 'single_regimen' нужно указать regimen_name")
        return grid_search_regimen(
            subtype=subtype,
            ki67=ki67,
            V0=V0,
            regimen_name=regimen_name,
            t_end=t_end,
            bsa=bsa,
            use_resistance=use_resistance,
            row_like_for_resistance=row_like_for_resistance,
            objective=objective,
        )

    if mode == "auto_best":
        cand_regimens = get_recommended_for_subtype(subtype)
        results = []
        for reg in cand_regimens:
            if reg in NON_PHASE_REGIMENS:
                try:
                    res = grid_search_regimen(
                        subtype=subtype,
                        ki67=ki67,
                        V0=V0,
                        regimen_name=reg,
                        t_end=t_end,
                        bsa=bsa,
                        use_resistance=use_resistance,
                        row_like_for_resistance=row_like_for_resistance,
                        objective=objective,
                    )
                    if res is not None:
                        results.append(res)
                except Exception as e:
                    print(f"Не удалось оптимизировать {reg}: {e}")

        if not results:
            return None

        best = min(results, key=lambda r: r["V"][-1] if objective == "min_final_volume" else np.min(r["V"]))
        return best

    raise ValueError("Неизвестный mode в optimize_treatment")


# =============================================================
# 9. ВИЗУАЛИЗАЦИЯ: PK/PD И ДИНАМИКА ОПУХОЛИ
# =============================================================

def plot_pk_pd_for_result(result, t_end=None, bsa: float = 1.7):
    if t_end is None:
        t_end = float(result["t"][-1])

    pk_profiles = {}

    if "drug" in result and "choices" not in result:
        drug_specs = [(result["drug"], result["interval"], result["dose_abs"])]
    else:
        interval_default = result.get("interval", "q3w")
        choices = result.get("choices", [])
        if choices:
            drug_specs = [(dname, interval, dose_abs) for (dname, interval, dose_abs) in choices]
        else:
            drug_specs = []

    for drug, interval, dose_abs in drug_specs:
        C_func, E_max, EC50 = build_single_drug_pkpd(
            drug_name=drug,
            t_end=t_end,
            bsa=bsa,
            dose_abs_override=dose_abs,
            schedule_override=interval,
        )

        t = np.linspace(0, t_end, 800)
        C = np.array([float(C_func(tt)) for tt in t])
        E = E_of_C(C, E_max, EC50)

        pk_profiles[drug] = {
            "t": t,
            "C": C,
            "E": E,
            "E_max": E_max,
            "EC50": EC50,
        }

    if not pk_profiles:
        print("Нет PK-профилей для отображения.")
        return

    plt.figure(figsize=(10, 4))
    for drug, prof in pk_profiles.items():
        plt.plot(prof["t"], prof["C"], label=f"{drug}")
    plt.title("PK: концентрация препаратов C(t)")
    plt.xlabel("Days")
    plt.ylabel("C(t)")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(10, 4))
    total_E = np.zeros_like(next(iter(pk_profiles.values()))["E"])
    t = next(iter(pk_profiles.values()))["t"]

    for drug, prof in pk_profiles.items():
        plt.plot(prof["t"], prof["E"], "--", label=f"{drug} (E)")
        total_E += prof["E"]

    plt.plot(t, total_E, label="Суммарный эффект", linewidth=2)
    plt.title("PD: цитотоксический эффект")
    plt.xlabel("Days")
    plt.ylabel("Effect (усл. ед.)")
    plt.grid(True)
    plt.legend()
    plt.show()


def print_grid_summary(result,
                       mode: str,
                       plot: bool = True):
    if result is None:
        print("Нет подходящих комбинаций (result = None)")
        return

    print("\n" + "=" * 70)
    print(f"РЕЗУЛЬТАТ ОПТИМИЗАЦИИ — режим: {mode}")
    print("=" * 70)

    if mode == "single_drug":
        print("Препарат:", result.get("drug", "?"))
        print("Интервал:", result.get("interval", "?"))
        print("Доза:", f'{result.get("dose", "?")}  ({result.get("dose_abs", "?")} mg абсолютной)')

    elif mode == "single_regimen":
        print("Схема лечения:", result.get("regimen", "?"))
        print("Интервал:", result.get("interval", "?"))

    elif mode == "auto_best":
        print("Лучшая схема среди рекомендованных:", result.get("regimen", "?"))
        print("Интервал:", result.get("interval", "?"))

    if "choices" in result and isinstance(result["choices"], (list, tuple)):
        print("\nПрепараты и дозы:")
        for item in result["choices"]:
            drug = item[0]
            dose_abs = item[-1]
            interval = None
            for v in item[1:-1]:
                if isinstance(v, str):
                    interval = v

            if interval:
                print(f" • {drug}: {dose_abs:.1f} mg  (интервал: {interval})")
            else:
                print(f" • {drug}: {dose_abs:.1f} mg")

    t = result.get("t")
    V = result.get("V")

    if t is not None and V is not None:
        V0_real = V[0]
        V_final = V[-1]
        V_min = np.min(V)
        reduction_pct = (V0_real - V_final) / V0_real * 100 if V0_real > 0 else np.nan

        print("\nДинамика опухоли")
        print(f"Начальный объём: {V0_real:.2f}")
        print(f"Финальный объём: {V_final:.2f}")
        print(f"Минимальный объём: {V_min:.2f}")
        print(f"Изменение: {reduction_pct:.1f}%")

        if plot:
            plt.figure(figsize=(8, 5))
            plt.plot(t, V, label="Tumor volume", linewidth=2)
            plt.xlabel("Days")
            plt.ylabel("Tumor volume")
            plt.title("Tumor dynamics — optimized regimen")
            plt.grid(True)
            plt.legend()
            plt.show()

    print("=" * 70 + "\n")
