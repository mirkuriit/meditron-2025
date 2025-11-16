import numpy as np
from scipy.optimize import minimize
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from model.constants import REGIMENS, PK_PD_PARAMS, T_cycle_dict, params_pop

def r_from_ki67(ki67_fraction: float, T_cycle_days: float) -> float:
    return (np.log(2) / T_cycle_days) * ki67_fraction

def E_of_C(C, E_max, EC50):
    return E_max * C / (C + EC50 + 1e-12)

def pk_input_bolus(t, dose_time=0.0, dose_amount=100.0):
    if abs(t - dose_time) < 1e-6:
        return dose_amount 
    return 0.0

def pk_input_infusion(t, start=0.0, end=1.0, rate=50.0):
    if start <= t <= end:
        return rate 
    return 0.0

def pk_input_cycles(t, cycle_len=21, dose_amount=100.0):
    if abs(t % cycle_len) < 1e-6:
        return dose_amount
    return 0.0

def pk_one_comp_ode(t, y, CL, V1, input_func=None):
    A = y[0]
    I = input_func(t) if input_func else 0.0
    dA_dt = -(CL / V1) * A + I
    return [dA_dt]

def pk_two_comp_ode(t, y, CL, Q, V1, V2, input_func=None):
    """Двухкомпартментная модель PK.


    y = [A1, A2] — количество вещества в каждом компартменте (мг).
    input_func(t) → мг/сут.
    """
    A1, A2 = y
    I = input_func(t) if input_func else 0.0


    dA1dt = -(CL / V1) * A1 - (Q / V1) * A1 + (Q / V2) * A2 + I
    dA2dt = (Q / V1) * A1 - (Q / V2) * A2
    return [dA1dt, dA2dt]

def simulate_pk_two_comp(CL, Q, V1, V2,
    y0, t_end, n_points=2000,
    input_func=None):
    """Чистая PK: возвращает функцию C(t) для центрального компартмента."""
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
    dose_abs_override: float | None = None,
    schedule_override: str | None = None,
):
    """
    Строит PK для одного препарата и возвращает (C_func, E_max, EC50).

    dose_abs_override — абсолютная доза в мг (уже с учётом BSA, если нужно)
    schedule_override — 'q3w', 'weekly', 'daily', ...
    """
    if drug_name not in PK_PD_PARAMS:
        raise ValueError(f"Препарат {drug_name} отсутствует в PK_PD_PARAMS")

    p = PK_PD_PARAMS[drug_name]
    CL, Q, V1, V2 = p["CL"], p["Q"], p["V1"], p["V2"]
    # --- если препарат однокомпартментный ---
    is_one_comp = (p["Q"] == 0 or p["V2"] == 0)


    E_max, EC50 = p["E_max"], p["EC50"]

    schedule = schedule_override if schedule_override is not None else p["schedule"]

    # --- выбор дозы ---
    if dose_abs_override is not None:
        dose_abs = dose_abs_override
    else:
        if "dose_mg_per_m2" in p:
            dose_abs = p["dose_mg_per_m2"] * bsa
        elif "dose_mg_fixed" in p:
            dose_abs = p["dose_mg_fixed"]
        else:
            raise ValueError(f"Не найдена доза для препарата {drug_name}")

    # --- ввод по расписанию ---
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
        # fallback: болюс в 0
        input_func = None
        y0 = [dose_abs, 0.0]

        # --- Выбор PK модели ---
    if is_one_comp:
        # однокомпартментная PK
        def pk_ode(tt, yy):
            return pk_one_comp_ode(tt, yy, CL, V1, input_func)

        t_eval = np.linspace(0, t_end, 2000)
        sol = solve_ivp(pk_ode, [0, t_end], [0.0], t_eval=t_eval)
        C = sol.y[0] / V1
        C_func = interp1d(t_eval, C, fill_value="extrapolate")

    else:
        # двухкомпартментная PK
        C_func = simulate_pk_two_comp(
            CL, Q, V1, V2,
            y0=y0,
            t_end=t_end,
            n_points=2000,
            input_func=input_func
        )

    return C_func, E_max, EC50

def make_regimen_drug_effect(regimen_name: str, t_end: float = 365.0, bsa: float = 1.7):
    """Строит суммарный drug_effect(t) для схемы (фазной или нет).

    Возвращает функцию drug_effect(t) = Σ_i E_i(C_i(t)).
    """
    reg = REGIMENS[regimen_name]

    # --------------------------------------------------
    # НЕФАЗНАЯ СХЕМА (просто список drugs)
    # --------------------------------------------------
    if "phases" not in reg:
        drug_names = reg["drugs"]
        pk_list = []  # список (C_func, E_max, EC50)

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


    # --------------------------------------------------
    # ФАЗНАЯ СХЕМА (AC_T и подобные)
    # --------------------------------------------------
    phases = reg["phases"]

    # Для простоты: моделируем PK каждого препарата на весь t_end,
    # но "выключаем" ввод за пределами своей фазы.

    pk_list = []  # список (C_func_global, E_max, EC50)

    t_shift = 0.0
    for ph in phases:
        duration = ph["duration"]
        drugs = ph["drugs"]

        for dname in drugs:
            # Строим PK только на интервале фазы [0, duration],
            # затем упаковываем его в глобальную функцию через сдвиг.
            C_phase, E_max, EC50 = build_single_drug_pkpd(
                dname, t_end=duration, bsa=bsa
            )

            def make_shifted(C_local, shift, dur):
                # Замыкание, чтобы избежать проблем с late binding
                def C_global(t):
                    tau = t - shift
                    if tau < 0:
                        return 0.0
                    # PK после окончания фазы не обрываем искусственно,
                    # а даём естественное вымывание: продолжаем вызывать C_local.
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

def get_resistance_params(row_like,
                          manual_mutation_rate=None,
                          manual_resistance_strength=None):
    """Правило для параметров резистентности.

    row_like: dict/pd.Series с полем 'treatment_response'.
    Если manual_* заданы — они в приоритете.
    """
    if manual_mutation_rate is not None and manual_resistance_strength is not None:
        return manual_mutation_rate, manual_resistance_strength

    response = None
    if hasattr(row_like, "get"):
        response = row_like.get("treatment_response", None)
    else:
        try:
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
    """2-компартментная модель без явной резистентности.

    y = [U, N]
    U — жизнеспособная часть опухоли
    N — некротическая часть
    """
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
    """Модель с чувствительными и резистентными клетками.

    y = [Ns, Nr, N]
    Ns — чувствительные
    Nr — резистентные
    N  — некротические массы
    """
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
                     regimen_name: str | None = None,
                     t_end: float = 365.0,
                     use_resistance: bool = False,
                     mutation_rate: float | None = None,
                     resistance_strength: float | None = None,
                     row_like_for_resistance=None,
                     bsa: float = 1.7,
                     drug_effect_override=None):
    """
    Если drug_effect_override не None — используем его.
    Иначе строим эффект по regimen_name как раньше.
    """

    pop = params_pop[subtype]
    T_cycle = T_cycle_dict[subtype]

    d_base = pop["d"]
    k_clear = pop["k_clear"]
    K = pop["K"]
    f_N0 = pop["f_N0"]

    r = r_from_ki67(ki67_percent / 100.0, T_cycle)

    # ---- источник эффекта препарата ----
    if drug_effect_override is not None:
        drug_effect_func = drug_effect_override
    elif regimen_name is not None:
        drug_effect_func = make_regimen_drug_effect(
            regimen_name, t_end=t_end, bsa=bsa
        )
    else:
        drug_effect_func = lambda t: 0.0

    t_eval = np.linspace(0.0, t_end, 600)

    # дальше твой код без изменений...
    # (всё, что ниже, можешь оставить как было — я его не менял)
    # --------------------------------------------------
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

    # --- с резистентностью (тоже без изменений) ---
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
                    drug_effect_override=drug_effect_override
                )
        else:
            return simulate_patient(
                subtype, ki67_percent, V0,
                regimen_name=regimen_name,
                t_end=t_end,
                use_resistance=False,
                bsa=bsa,
                drug_effect_override=drug_effect_override
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

def get_pk_profiles(regimen_name: str, t_end: float = 365.0, bsa: float = 1.7):
    """Возвращает PK-профили всех препаратов в схеме с учётом фазности.

    Возвращает dict: drug_name → {"t", "C", "E_max", "EC50"}.
    """
    reg = REGIMENS[regimen_name]
    profiles: dict[str, dict] = {}

    # -----------------------------
    # НЕФАЗНАЯ СХЕМА
    # -----------------------------
    if "phases" not in reg:
        drugs = reg["drugs"]
        for d in drugs:
            C_func, E_max, EC50 = build_single_drug_pkpd(d, t_end=t_end, bsa=bsa)
            t = np.linspace(0, t_end, 800)
            C = np.array([float(C_func(tt)) for tt in t])
            profiles[d] = {"t": t, "C": C, "E_max": E_max, "EC50": EC50}
        return profiles

    # -----------------------------
    # ФАЗНАЯ СХЕМА
    # -----------------------------
    t_global = np.linspace(0.0, t_end, 800)
    t_shift = 0.0

    for phase in reg["phases"]:
        duration = phase["duration"]
        drugs = phase["drugs"]

        for d in drugs:
            C_phase, E_max, EC50 = build_single_drug_pkpd(d, t_end=duration, bsa=bsa)

            C_global = []
            for tt in t_global:
                tau = tt - t_shift
                if tau < 0:
                    C_global.append(0.0)
                else:
                    C_global.append(float(C_phase(max(tau, 0.0))))

            C_global = np.array(C_global)

            if d not in profiles:
                profiles[d] = {
                    "t": t_global,
                    "C": np.zeros_like(t_global),
                    "E_max": E_max,
                    "EC50": EC50,
                }

            profiles[d]["C"] += C_global

        t_shift += duration

    return profiles

def compute_pd_effect(pk_profiles: dict):
    """По PK-профилям считает суммарный PD-эффект и эффекты по препаратам."""
    any_prof = next(iter(pk_profiles.values()))
    t = any_prof["t"]

    total_effect = np.zeros_like(t)
    details = {}

    for drug, prof in pk_profiles.items():
        C = prof["C"]
        E = E_of_C(C, prof["E_max"], prof["EC50"])
        details[drug] = E
        total_effect += E

    return t, total_effect, details