import numpy as np
import matplotlib.pyplot as plt
from termcolor import colored
from model.constants import REGIMENS, TOXICITY_LIMITS, PROTOCOL_MAX_CYCLES, DOSE_INTERVAL_GRID, NON_PHASE_REGIMENS
from model.pkpd import build_single_drug_pkpd, simulate_patient, E_of_C
from model.patient_profiles import get_recommended_for_subtype

def optimize_treatment(
        subtype: str,
        ki67: float,
        V0: float,
        stage: int,
        lymph_nodes_pos: int,
        mode: str = "auto_best", 
        drug_name: str | None = None,
        regimen_name: str | None = None,
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
                    print(f" Не удалось оптимизировать {reg}: {e}")

        if not results:
            return None

        best = min(results, key=lambda r: r["V"][-1] if objective=="min_final_volume" else np.min(r["V"]))
        return best

    raise ValueError("Неизвестный mode в optimize_treatment")

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

def grid_search_single_drug(subtype: str,
                            ki67: float,
                            V0: float,
                            drug_name: str,
                            t_end: float | None = None,
                            bsa: float = 1.7,
                            use_resistance: bool = False,
                            row_like_for_resistance=None,
                            objective: str = "min_final_volume",
                            doctor_fixed_interval: str | None = None):

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

      
        dt = {"q3w":21, "q2w":14, "weekly":7, "daily":1, "q6m":180}.get(interval, 21)
        t_local_end = n_cycles * dt

        for dose in doses:

            dose_abs = dose * bsa if dose_type=="mg_per_m2" else dose

          
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

            t, *rest = simulate_patient(
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
            score = V[-1] if objective=="min_final_volume" else np.min(V)

            if score < best_score:
                best_score = score
                best_result = {
                    "drug": drug_name,
                    "interval": interval,
                    "dose": dose,
                    "dose_abs": dose_abs,
                    "t": t,
                    "V": V,
                    "cycles": n_cycles
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
        objective: str = "min_final_volume"
):

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



def plot_pk_pd_for_result(result, t_end=None, bsa=1.7):

    import matplotlib.pyplot as plt


    if t_end is None:
        t_end = float(result["t"][-1])

    pk_profiles = {}

    if "drug" in result and "choices" not in result:
        drug_specs = [(result["drug"], result["interval"], result["dose_abs"])]
    else:
        interval = result.get("interval", "q3w")
        drug_specs = [(dname, interval, dose_abs) for (dname, dose_abs) in result["choices"]]

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
            "EC50": EC50
        }

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
    plt.ylabel("Effect (условн. ед.)")
    plt.grid(True)
    plt.legend()
    plt.show()

def print_grid_summary(result,
                       mode,
                       plot=True,
                       subtype=None,
                       ki67=None,
                       V0=None,
                       use_resistance=False,
                       row_like_for_resistance=None,
                       bsa=1.7):


    if result is None:
            return {
                "status": "error",
                "message": "Нет подходящих комбинаций"
            }

    response = {
        "status": "ok",
        "mode": mode,
        "summary": {},
        "drugs": [],
        "plot": {}
    }

    if mode == "single_drug":
        response["summary"] = {
            "type": "single_drug",
            "drug": result.get("drug"),
            "interval": result.get("interval"),
            "dose": result.get("dose"),
            "dose_abs": result.get("dose_abs"),
        }

    elif mode == "single_regimen":
        response["summary"] = {
            "type": "single_regimen",
            "regimen": result.get("regimen"),
            "interval": result.get("interval", None)  # может отсутствовать
        }

    elif mode == "auto_best":
        response["summary"] = {
            "type": "auto_best",
            "regimen": result.get("regimen"),
            "interval": result.get("interval", None)
        }


    if "choices" in result and isinstance(result["choices"], (list, tuple)):
        for item in result["choices"]:
            drug = item[0]
            dose_abs = item[-1]

            interval = None
            for v in item[1:-1]:
                if isinstance(v, str):
                    interval = v

            response["drugs"].append({
                "drug": drug,
                "dose_abs": float(dose_abs),
                "interval": interval
            })

    elif mode == "single_drug":
        response["drugs"].append({
            "drug": result.get("drug"),
            "dose_abs": float(result.get("dose_abs")),
            "interval": result.get("interval")
        })


    t = result.get("t")
    V = result.get("V")

    if isinstance(t, np.ndarray):
        t = t.tolist()
    if isinstance(V, np.ndarray):
        V = V.tolist()

    response["plot"] = {
        "x": t,
        "y": V
    }

    return response