import numpy as np
import matplotlib.pyplot as plt
from termcolor import colored
from model.constants import REGIMENS, TOXICITY_LIMITS, PROTOCOL_MAX_CYCLES, DOSE_INTERVAL_GRID, NON_PHASE_REGIMENS
from model.pkpd import build_single_drug_pkpd, simulate_patient, E_of_C
from model.patient_profiles import get_recommended_for_subtype

def choose_optimal_regimen(subtype: str, ki67: float, stage: int, lymph_nodes_pos: int):
    """Пример простой логики выбора оптимальной схемы.

    Это эвристика, её можно уточнять вместе с онкологом.
    """
    # TNBC
    if subtype == "TNBC":
        if stage >= 4:
            return "PLATINUM"
        if ki67 > 40:
            # агрессивный TNBC → AC_T
            return "AC_T"
        else:
            if stage == 1:
                return "TC"
            else:
                return "AC_T"

    # HER2+
    if subtype == "HER2+":
        if stage == 1:
            return "T_paclitaxel"
        if stage in [2, 3]:
            return "AC_T"
        if stage >= 4:
            return "T_mono"  # условно, можно заменить на T_paclitaxel
        return "T_paclitaxel"

    # HR+
    if subtype == "HR+":
        if ki67 < 15:
            return "LET"
        elif 15 <= ki67 <= 30:
            if stage >= 2:
                return "TC"
            return "LET"
        else:  # Ki67 > 30
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

    # расчёт количества введений
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

    # ограничение протоколом
    n = min(n, PROTOCOL_MAX_CYCLES.get(drug_name, n))

    # вычисление кумулятивной дозы
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

    # ограничиваем протоколом
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
        t_end = 365  # или get_default_t_end, если схема

    grid = DOSE_INTERVAL_GRID[drug_name]
    doses = grid["doses"]
    dose_type = grid["type"]

    intervals = [doctor_fixed_interval] if doctor_fixed_interval else grid["intervals"]

    best_score = np.inf
    best_result = None

    for interval in intervals:
        # вычисляем число циклов
        n_cycles = count_cycles(interval, t_end, drug_name)
        if n_cycles == 0:
            continue

        # реальное время лечения
        dt = {"q3w":21, "q2w":14, "weekly":7, "daily":1, "q6m":180}.get(interval, 21)
        t_local_end = n_cycles * dt

        for dose in doses:

            dose_abs = dose * bsa if dose_type=="mg_per_m2" else dose

            # токсичность
            if not check_toxicity(drug_name, dose_abs, interval, t_local_end, bsa):
                continue

            # PK
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
    """
    Новый grid search:
    • каждый препарат использует свой набор интервалов и доз
    • полный перебор всех комбинаций доз × интервалов по препаратам
    • НЕ требует общего интервала (в отличие от старой версии)
    """
    if regimen_name not in REGIMENS:
        raise ValueError(f"Схема {regimen_name} не найдена")

    reg = REGIMENS[regimen_name]

    if "phases" in reg:
        raise ValueError("Фазные схемы (AC→T) не оптимизируются через этот grid search.")

    drugs = reg["drugs"]

    # Сбор всех вариантов (intervals × doses) для каждого препарата
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

    # Полный перебор
    best_score = np.inf
    best_result = None

    def backtrack(idx, current_choices):
        nonlocal best_score, best_result

        # Все препараты перебраны
        if idx == len(options_per_drug):
            # Создаем список PK для выбранных комбинаций
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

            # Общий эффект
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
                    "choices": current_choices.copy(),  # [(drug, interval, dose_abs), ...]
                    "t": t_vec,
                    "V": V,
                    "score": score,
                }
            return

        # Идем по препаратам
        drug_name, options = options_per_drug[idx]
        for interval, dose_abs in options:
            if not check_toxicity(drug_name, dose_abs, interval, t_end, bsa):
                continue

            current_choices.append((drug_name, interval, dose_abs))
            backtrack(idx + 1, current_choices)
            current_choices.pop()

    backtrack(0, [])
    return best_result

def optimize_treatment(
        subtype: str,
        ki67: float,
        V0: float,
        stage: int,
        lymph_nodes_pos: int,
        mode: str = "auto_best",   # "single_drug", "single_regimen", "auto_best"
        drug_name: str | None = None,
        regimen_name: str | None = None,
        t_end: float = 365.0,
        use_resistance: bool = False,
        row_like_for_resistance=None,
        bsa: float = 1.7,
        objective: str = "min_final_volume"):
    """
    mode:
      - "single_drug"    — оптимизация по выбранному препарату (drug_name)
      - "single_regimen" — оптимизация по выбранной схеме (regimen_name)
      - "auto_best"      — ищем лучшую схему среди рекомендованных для subtype
    """

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
        # берём рекомендованные схемы для subtype и ищем среди них лучшую
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
                    print(f"⚠ Не удалось оптимизировать {reg}: {e}")

        if not results:
            return None

        # выбираем лучшую по objective
        best = min(results, key=lambda r: r["V"][-1] if objective=="min_final_volume" else np.min(r["V"]))
        return best

    raise ValueError("Неизвестный mode в optimize_treatment")

def plot_pk_pd_for_result(result, t_end=None, bsa=1.7):
    """
    Рисует PK (C(t)) и PD (E(t)) по результату grid-search.
    Ожидается:
      - для single_regimen/auto_best: result["choices"] = [(drug_name, dose_abs), ...], result["interval"]
      - для single_drug:            result["drug"], result["dose_abs"], result["interval"]
    """
    import matplotlib.pyplot as plt

    # определяем t_end
    if t_end is None:
        t_end = float(result["t"][-1])

    pk_profiles = {}

    # --- SINGLE DRUG CASE ---
    if "drug" in result and "choices" not in result:
        drug_specs = [(result["drug"], result["interval"], result["dose_abs"])]
    else:
        # choices: (drug_name, dose_abs), общий interval лежит в result["interval"]
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

    # ---------- PK ----------
    plt.figure(figsize=(10, 4))
    for drug, prof in pk_profiles.items():
        plt.plot(prof["t"], prof["C"], label=f"{drug}")
    plt.title("PK: концентрация препаратов C(t)")
    plt.xlabel("Days")
    plt.ylabel("C(t)")
    plt.grid(True)
    plt.legend()
    plt.show()

    # ---------- PD ----------
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
    """
    Универсальный вывод результата оптимизации.
    Поддерживает:
      - single_drug
      - single_regimen
      - auto_best
    """

    if result is None:
        print(colored("❌ Нет подходящих комбинаций (result = None)", "red"))
        return

    print(colored("\n" + "="*70, "yellow"))
    print(colored(f"РЕЗУЛЬТАТ ОПТИМИЗАЦИИ — режим: {mode}", "yellow", attrs=["bold"]))
    print(colored("="*70, "yellow"))

    # ------------------------------------------------------------------
    # 1) Основная информация по режимам
    # ------------------------------------------------------------------
    if mode == "single_drug":
        print(colored("🧪 Препарат:", "cyan"), result.get("drug", "?"))
        print(colored("⏱ Интервал:", "cyan"), result.get("interval", "?"))
        print(colored("💉 Доза:", "cyan"), f"{result.get('dose', '?')}  ({result.get('dose_abs', '?')} mg абсолютной)")

    elif mode == "single_regimen":
        print(colored("🧪 Схема лечения:", "cyan"), result.get("regimen", "?"))
        print(colored("⏱ Интервал:", "cyan"), result.get("interval", "?"))

    elif mode == "auto_best":
        print(colored("⭐ Лучшая схема среди рекомендованных:", "cyan"), result.get("regimen", "?"))
        print(colored("⏱ Интервал:", "cyan"), result.get("interval", "?"))

    # ------------------------------------------------------------------
    # 2) CHOICES — универсальный вывод для любого формата
    # ------------------------------------------------------------------
    if "choices" in result and isinstance(result["choices"], (list, tuple)):
        print(colored("\n💊 Препараты и дозы:", "cyan"))

        for item in result["choices"]:
            # Возможные форматы:
            # (drug, dose_abs)
            # (drug, interval, dose_abs)
            # (drug, interval, dose, dose_abs)
            # (drug, dose, dose_abs)
            # и любые похожие

            drug = item[0]
            # абсолютная доза — всегда последний элемент
            dose_abs = item[-1]

            # интервал (может отсутствовать)
            interval = None
            for v in item[1:-1]:
                if isinstance(v, str):
                    interval = v

            if interval:
                print(f" • {drug}: {dose_abs:.1f} mg  (интервал: {interval})")
            else:
                print(f" • {drug}: {dose_abs:.1f} mg")

    # ------------------------------------------------------------------
    # 3) ДИНАМИКА ОПУХОЛИ
    # ------------------------------------------------------------------
    t = result.get("t")
    V = result.get("V")

    if t is not None and V is not None:
        V0_real = V[0]
        V_final = V[-1]
        V_min = np.min(V)
        reduction_pct = (V0_real - V_final) / V0_real * 100

        print(colored("\n📊 Динамика опухоли", "magenta", attrs=["bold"]))

        # ------------------------------------------------------------------
        # 4) ПЛОТ
        # ------------------------------------------------------------------
        if plot:
            plt.figure(figsize=(8, 5))
            plt.plot(t, V, label="Tumor volume", linewidth=2)
            plt.xlabel("Days")
            plt.ylabel("Tumor volume")
            plt.title("Tumor dynamics — optimized regimen")
            plt.grid(True)
            plt.legend()
            plt.show()

    print(colored("="*70 + "\n", "yellow"))