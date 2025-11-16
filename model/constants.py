import numpy as np

PK_PD_PARAMS = {
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


DOSE_INTERVAL_GRID = {

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
        "doses": list(range(300, 601, 50)),    # 300–600
        "intervals": ["q3w"],
    },
}

REGIMENS = {

    "TC": {
        "description": "Docetaxel + Cyclophosphamide",
        "drugs": ["docetaxel", "cyclophosphamide"]
    },

    "AC": {
        "description": "Doxorubicin + Cyclophosphamide",
        "drugs": ["doxorubicin", "cyclophosphamide"]
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
        "drugs": ["trastuzumab_sc", "paclitaxel"]
    },


    "T_mono": {
        "description": "Trastuzumab monotherapy",
        "drugs": ["trastuzumab_sc"]
    },


    "LET": {
        "description": "Letrozole monotherapy",
        "drugs": ["letrozole"]
    },


    "TAM": {
        "description": "Tamoxifen monotherapy",
        "drugs": ["tamoxifen"]
    },


    "ANA": {
        "description": "Anastrozole monotherapy",
        "drugs": ["anastrozole"]
    },


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

TIME_POINTS_MONTHS = np.array([0, 3, 6, 12, 24])


T_cycle_dict = {
"HR+": 3.0,
"HER2+": 2.0,
"TNBC": 1.0,
}


TIME_POINTS_MONTHS = np.array([0, 3, 6, 12, 24])


T_cycle_dict = {
"HR+": 3.0,
"HER2+": 2.0,
"TNBC": 1.0,
}


params_pop = {
"HR+": {
"d": 0.01,
"k_clear": 0.001,
"K": 800.0,
"f_N0": 0.2
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
    "doxorubicin": {
        "max_cumulative_mg_per_m2": 500  
    },
    "epirubicin": {
        "max_cumulative_mg_per_m2": 900
    },
    "carboplatin": {
        "max_cumulative_mg_per_m2": 800
    },
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


DOSE_INTERVAL_GRID = {

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

NON_PHASE_REGIMENS = {
    "TC", "AC", "T_paclitaxel", "LET", "TAM", "ANA", "BONE", "PLATINUM"
}