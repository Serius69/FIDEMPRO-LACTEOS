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
    "date": ["2023-11-24", "2023-11-25"],  # Replace with your actual date data
    "variables": 
        {
        "CPVD": 455, 
        "PVP": 1.59,
        "CPVD": 234, 
        "PVP": 639,
        "CPVD": 2.62, 
        "PVP": 240,
        "CPVD": "No", 
        "PVP": 1.16,
        "CPVD": "Medianamente competitivo", 
        "PVP": 9,
        "CPVD": "Mensual", 
        "PVP": 0.59,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
        "CPVD": 50, 
        "PVP": 75,
         
         },  # Replace with your actual variables data
    "unit": {"measurement": "kg", "value": 2},
    "unit_time": {"time_unit": "day", "value": 1},
    "results": {"result1": 30, "result2": 40},  # Replace with your actual results data
    "fk_simulation": 1, 
}