import numpy as np

PK_PD_PARAMS = {
    # ---------------------------------------------------------
    # ДОЦЕТАКСЕЛ (docetaxel) — mg/m²
    # ---------------------------------------------------------
    "docetaxel": {
        "dose_mg_per_m2": 75.0,   # mg/m2
        "schedule": "q3w",
        "CL": 15.0,
        "Q": 10.0,
        "V1": 15.0,
        "V2": 40.0,
        "E_max": 0.35,
        "EC50": 0.5
    },

    # ---------------------------------------------------------
    # ЦИКЛОФОСФАМИД — mg/m²
    # ---------------------------------------------------------
    "cyclophosphamide": {
        "dose_mg_per_m2": 600.0,   # mg/m2
        "schedule": "q3w",
        "CL": 10.0,
        "Q": 6.0,
        "V1": 20.0,
        "V2": 55.0,
        "E_max": 0.28,
        "EC50": 0.6
    },

    # ---------------------------------------------------------
    # ДОКСОРУБИЦИН — mg/m²
    # ---------------------------------------------------------
    "doxorubicin": {
        "dose_mg_per_m2": 60.0,   # mg/m2
        "schedule": "q3w",
        "CL": 12.0,
        "Q": 8.0,
        "V1": 20.0,
        "V2": 50.0,
        "E_max": 0.40,
        "EC50": 0.4
    },

    # ---------------------------------------------------------
    # ПАКЛИТАКСЕЛ — mg/m² weekly
    # ---------------------------------------------------------
    "paclitaxel": {
        "dose_mg_per_m2": 80.0,  # mg/m2 weekly
        "schedule": "weekly",
        "CL": 20.0,
        "Q": 10.0,
        "V1": 15.0,
        "V2": 35.0,
        "E_max": 0.30,
        "EC50": 0.7
    },

    # ---------------------------------------------------------
    # ТРАСТУЗУМАБ (П/К) — фиксированная доза mg
    # ---------------------------------------------------------
    "trastuzumab_sc": {
        "dose_mg_fixed": 600.0,   # мг
        "schedule": "q3w",
        "CL": 0.5,
        "Q": 0.3,
        "V1": 3.0,
        "V2": 4.0,
        "E_max": 0.15,
        "EC50": 0.2
    },

    # ---------------------------------------------------------
    # ЛЕТРОЗОЛ — фиксированная доза mg
    # ---------------------------------------------------------
    "letrozole": {
        "dose_mg_fixed": 2.5,    # mg daily
        "schedule": "daily",
        "CL": 0.25,
        "Q": 0.0,
        "V1": 100.0,
        "V2": 0.0,
        "E_max": 0.12,
        "EC50": 0.05
    },

    # ---------------------------------------------------------
    # ТАМОКСИФЕН — фиксированная доза mg
    # ---------------------------------------------------------
    "tamoxifen": {
        "dose_mg_fixed": 20.0,   # mg daily
        "schedule": "daily",
        "CL": 0.2,
        "Q": 0.0,
        "V1": 120.0,
        "V2": 0.0,
        "E_max": 0.10,
        "EC50": 0.03
    },

    # ---------------------------------------------------------
    # АНАСТРОЗОЛ — фиксированная доза mg
    # ---------------------------------------------------------
    "anastrozole": {
        "dose_mg_fixed": 1.0,    # mg daily
        "schedule": "daily",
        "CL": 0.15,
        "Q": 0.0,
        "V1": 80.0,
        "V2": 0.0,
        "E_max": 0.12,
        "EC50": 0.04
    },

    # ---------------------------------------------------------
    # ЗОЛЕДРОНОВАЯ КИСЛОТА — фиксированная доза mg
    # ---------------------------------------------------------
    "zoledronic_acid": {
        "dose_mg_fixed": 4.0,    # mg q6m
        "schedule": "q6m",
        "CL": 5.0,
        "Q": 2.0,
        "V1": 6.0,
        "V2": 12.0,
        "E_max": 0.05,
        "EC50": 0.3
    },

    "carboplatin": {
    "dose_mg_per_m2":600 ,   # или mg-fixed
    "schedule": "q3w",
    "CL": 10.0,
    "Q": 5.0,
    "V1": 20.0,
    "V2": 40.0,
    "E_max": 0.25,
    "EC50": 0.5
    }

}

# ---------------------------------------------------------
# ДОПОЛНИТЕЛЬНАЯ СЕТКА ДОЗ / ИНТЕРВАЛОВ ДЛЯ GRID SEARCH
# ---------------------------------------------------------
DOSE_INTERVAL_GRID = {
    # антрациклин
    "doxorubicin": {
        "type": "mg_per_m2",
        "doses": list(range(50, 71, 10)),      # 50, 60, 70
        "intervals": ["q3w", "q2w"],           # стандарт AC и dose-dense
    },
    # циклофосфамид
    "cyclophosphamide": {
        "type": "mg_per_m2",
        "doses": list(range(500, 701, 50)),    # 500–700 шаг 50
        "intervals": ["q3w", "q2w"],
    },
    # доцетаксел
    "docetaxel": {
        "type": "mg_per_m2",
        "doses": list(range(60, 101, 10)),     # 60–100
        "intervals": ["q3w"],
    },
    # паклитаксел (weekly и q2w)
    "paclitaxel": {
        "type": "mg_per_m2",
        "doses": [60, 80, 100, 150, 175],
        "intervals": ["weekly", "q2w"],
    },
    # трастузумаб SC – фиксированная доза
    "trastuzumab_sc": {
        "type": "fixed_mg",
        "doses": [600],
        "intervals": ["q3w"],
    },
    # гормонотерапия – фиксированные дозы
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
    # золедроновая – фиксированная
    "zoledronic_acid": {
        "type": "fixed_mg",
        "doses": [4.0],
        "intervals": ["q6m"],
    },
    # карбоплатин – диапазон по mg/m²
    "carboplatin": {
        "type": "mg_per_m2",
        "doses": list(range(300, 601, 50)),    # 300–600
        "intervals": ["q3w"],
    },
}

REGIMENS = {
    # 1) Доцетаксел + циклофосфамид (классический TC)
    "TC": {
        "description": "Docetaxel + Cyclophosphamide",
        "drugs": ["docetaxel", "cyclophosphamide"]
    },

    # 2) Доксорубицин + циклофосфамид (AC)
    "AC": {
        "description": "Doxorubicin + Cyclophosphamide",
        "drugs": ["doxorubicin", "cyclophosphamide"]
    },

    # 3) ФАЗНАЯ СХЕМА: AC → T (потом можно будет добавить HER2)
    "AC_T": {
        "description": "Doxorubicin + Cyclophosphamide followed by Paclitaxel",
        "phases": [
        {"duration": 84.0, "drugs": ["doxorubicin", "cyclophosphamide"]}, # 4 цикла по 21
        {"duration": 84.0, "drugs": ["paclitaxel"]}, # 12 weekly
        ],
    },


    # 4) Трастузумаб +/- паклитаксел (HER2-таргетная)
    "T_paclitaxel": {
        "description": "Trastuzumab + Paclitaxel",
        "drugs": ["trastuzumab_sc", "paclitaxel"]
    },

    # 5) Только трастузумаб (поддержка)
    "T_mono": {
        "description": "Trastuzumab monotherapy",
        "drugs": ["trastuzumab_sc"]
    },

    # 6) ГТ: летрозол
    "LET": {
        "description": "Letrozole monotherapy",
        "drugs": ["letrozole"]
    },

    # 7) ГТ: тамоксифен
    "TAM": {
        "description": "Tamoxifen monotherapy",
        "drugs": ["tamoxifen"]
    },

    # 8) ГТ: анастрозол
    "ANA": {
        "description": "Anastrozole monotherapy",
        "drugs": ["anastrozole"]
    },

    # 9) Поддержка костей: золедроновая кислота
    "BONE": {
        "description": "Zoledronic acid",
        "drugs": ["zoledronic_acid"]
    },

    "PLATINUM": {
    "description": "Carboplatin",
    "drugs": ["carboplatin"]
    }

}

RECOMMENDED_REGIMENS = {
    # ---------------------------------------------------------------
    # HR+ / HER2–  (люминальный В, HER2-отрицательный)
    # ---------------------------------------------------------------
    "HR+": [
        {
            "name": "LET",
            "comment": "Гормонотерапия — тамоксифен/ингибитор ароматазы ± овариальная супрессия"
        },
        {
            "name": "TC",
            "comment": "DC: доцетаксел + циклофосфамид, предпочтительный режим 4–6 циклов"
        },
        {
            "name": "AC",
            "comment": "AC/EC 4 цикла"
        },
        {
            "name": "AC_T",
            "comment": "AC/EC → доцетаксел 4 цикла или паклитаксел weekly 12 раз"
        }
    ],

    # ---------------------------------------------------------------
    # HER2+  (люминальный HER2+ и HER2+ нелюминальный)
    # ---------------------------------------------------------------
    "HER2+": [
        {
            "name": "T_paclitaxel",
            "comment": "Таксан + трастузумаб (± пертузумаб) одновременно"
        },
        {
            "name": "T_mono",
            "comment": "Поддерживающая HER2-терапия трастузумабом"
        },
        {
            "name": "AC_T",
            "comment": "AC → таксан → анти-HER2 (антрациклины отдельно от HER2)"
        }
    ],

    # ---------------------------------------------------------------
    # Тройной негативный / базальноподобный (TNBC)
    # ---------------------------------------------------------------
    "TNBC": [
        {
            "name": "AC",
            "comment": "Антрациклины (AC/EC)"
        },
        {
            "name": "TC",
            "comment": "Доцетаксел + циклофосфамид"
        },
        {
            "name": "AC_T",
            "comment": "AC → таксаны (паклитаксел weekly или доцетаксел)"
        },
        {
            "name": "PLATINUM",
            "comment": "Платина (например, карбоплатин) — рекомендовано при TNBC"
        }
    ]
}

# Время для описательной статистики (0,3,6,12,24 мес)
TIME_POINTS_MONTHS = np.array([0, 3, 6, 12, 24])


# Словарь длительности клеточного цикла по подтипам (дни)
T_cycle_dict = {
"HR+": 3.0,
"HER2+": 2.0,
"TNBC": 1.0,
}


# Время для описательной статистики (0,3,6,12,24 мес)
TIME_POINTS_MONTHS = np.array([0, 3, 6, 12, 24])


# Словарь длительности клеточного цикла по подтипам (дни)
T_cycle_dict = {
"HR+": 3.0,
"HER2+": 2.0,
"TNBC": 1.0,
}


# Популяционные параметры роста для подтипов
params_pop = {
"HR+": {
"d": 0.01, # спонтанная смерть
"k_clear": 0.001,
"K": 800.0, # популяционная несущая ёмкость
"f_N0": 0.2 # начальная доля некроза
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

TOXICITY_LIMITS = {
    # Кумулятивные максимумы в мг/м² за весь курс лечения
    "doxorubicin": {
        "max_cumulative_mg_per_m2": 500   # 450–550 мг/м²
    },
    "epirubicin": {
        "max_cumulative_mg_per_m2": 900
    },
    "carboplatin": {
        # Условный upper bound (AUC недоступна в модели)
        "max_cumulative_mg_per_m2": 800
    },
    # Нет известных строгих ограничений
    "docetaxel": None,
    "paclitaxel": None,
    "cyclophosphamide": None,
    "letrozole": None,
    "tamoxifen": None,
    "anastrozole": None,
    "trastuzumab_sc": None,
    "zoledronic_acid": None,
}

PROTOCOL_MAX_CYCLES = {
    "doxorubicin": 6,
    "cyclophosphamide": 6,
    "docetaxel": 6,
    "paclitaxel": 12,
    "carboplatin": 6,
}

# ---------------------------------------------------------
# ДОПОЛНИТЕЛЬНАЯ СЕТКА ДОЗ / ИНТЕРВАЛОВ ДЛЯ GRID SEARCH
# ---------------------------------------------------------
DOSE_INTERVAL_GRID = {
    # антрациклин
    "doxorubicin": {
        "type": "mg_per_m2",
        "doses": list(range(50, 71, 10)),      # 50, 60, 70
        "intervals": ["q3w", "q2w"],           # стандарт AC и dose-dense
    },
    # циклофосфамид
    "cyclophosphamide": {
        "type": "mg_per_m2",
        "doses": list(range(500, 701, 50)),    # 500–700 шаг 50
        "intervals": ["q3w", "q2w"],
    },
    # доцетаксел
    "docetaxel": {
        "type": "mg_per_m2",
        "doses": list(range(60, 101, 10)),     # 60–100
        "intervals": ["q3w"],
    },
    # паклитаксел (weekly и q2w)
    "paclitaxel": {
        "type": "mg_per_m2",
        "doses": [60, 80, 100, 150, 175],
        "intervals": ["weekly", "q2w"],
    },
    # трастузумаб SC – фиксированная доза
    "trastuzumab_sc": {
        "type": "fixed_mg",
        "doses": [600],
        "intervals": ["q3w"],
    },
    # гормонотерапия – фиксированные дозы
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
    # золедроновая – фиксированная
    "zoledronic_acid": {
        "type": "fixed_mg",
        "doses": [4.0],
        "intervals": ["q6m"],
    },
    # карбоплатин – диапазон по mg/m²
    "carboplatin": {
        "type": "mg_per_m2",
        "doses": list(range(300, 601, 50)),    # 300–600
        "intervals": ["q3w"],
    },
}

NON_PHASE_REGIMENS = {
    "TC", "AC", "T_paclitaxel", "LET", "TAM", "ANA", "BONE", "PLATINUM"
}