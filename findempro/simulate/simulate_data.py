pdf_data= [
    {
        "name": "Distribution1",
        "distribution_type": 1,
        "lambda_param": 0.5,
        "cumulative_distribution_function": 0.7,
    },
    {
        "name": "Distribution2",
        "distribution_type": 2,
        "lambda_param": 0.8,
        "cumulative_distribution_function": 0.5,
    },
    {
        "name": "LogarithmicDistribution",
        "distribution_type": 3,
    }
]

simulation_data = {
    "unit_time": "day",
    "fk_fdp": 1,  # You may replace this with the actual foreign key value
    "demand_history": [513, 820, 648, 720, 649, 414, 704, 814, 647, 934, 483, 882, 220, 419, 254, 781, 674, 498, 518, 948, 983, 154, 649, 625, 865, 800, 848, 783, 218, 906],  # Replace with your actual demand history data
    "fk_questionary_result": 21,
}

# Sample data for ResultSimulation
result_simulation_data = {
    "demand_mean": 100.0,
    "demand_std_deviation": 10.0,
    "date": ["2023-11-24", "2023-11-25", "2023-11-26", "2023-11-27", "2023-11-28", "2023-11-29", "2023-11-30", "2023-12-01", "2023-12-02", "2023-12-03", "2023-12-04", "2023-12-05", "2023-12-06", "2023-12-07", "2023-12-08", "2023-12-09", "2023-12-10", "2023-12-11", "2023-12-12", "2023-12-13", "2023-12-14", "2023-12-15", "2023-12-16", "2023-12-17", "2023-12-18", "2023-12-19", "2023-12-20", "2023-12-21", "2023-12-22", "2023-12-23"],  # Added more dates
    "variables": 
        {
        "TPV": [],
        "TCAE": [],  
        "VPC": [],
        "TPP": [],
        "CP": [],
        "NEPP": [],
        "DI": [],
        "DE": [],
        "IT": [], 
        "GT": [],
        "GO": [],
        "CFD": [],
        "SE": [],
        "CTAI": [],
        "GG": [],
        "GMM": [],
        "CUP": [],
        "PI": [],
        "UII": [],
        "II": [],
        "IPF": [],
        "NR": [],
        "TCA": [],
        "NMD": [],
        "CUI": [], 
        "FU": [],
        "ALEP": [],
        "TG": [],
        "IB": [],
        "MB": [],
        "RI": [],
        "RTI": [],
        "RTC": [],
        "DH": [],
        "SE": [],
        "HO": [],
        "CPMO": [],
        "CA": [],
        "CUI": []  
        } ,
    "unit": {"measurement": "kg", "value": 2},
    "unit_time": {"time_unit": "day", "value": 1},
    "results": {"result1": 30, "result2": 40, "result3": 50, "result4": 60},  # Added more results data
    "fk_simulation": 1, 
}