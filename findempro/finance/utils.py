def analyze_simulation_results(results):
    # Example: Calculate average demand mean and standard deviation
    # Guard: 'results' vacío (p.ej. simulación sin días completados) haría
    # ZeroDivisionError en vez de devolver un resultado neutro.
    n = len(results) or 1
    avg_demand_mean = sum(result.demand_mean for result in results) / n
    avg_demand_std_dev = sum(result.demand_std_deviation for result in results) / n

    # You can add more analysis based on your specific requirements

    return {
        'avg_demand_mean': avg_demand_mean,
        'avg_demand_std_dev': avg_demand_std_dev
        # Add more metrics as needed
    }

def decision_support(analysis_results):
    # Example: Decision support logic based on average demand mean
    if analysis_results['avg_demand_mean'] > 100:
        return "Consider increasing inventory levels for better service."
    else:
        return "Inventory levels seem sufficient."

def decision_support_product_diversification(analysis_results):
    # Add your decision logic here
    pass

def decision_support_production_cost_optimization(analysis_results):
    # Add your decision logic here
    pass

def decision_support_inventory_management(analysis_results):
    if analysis_results['avg_demand_mean'] > 100:
        return "Consider increasing inventory levels for better service."
    else:
        return "Inventory levels seem sufficient."

def decision_support_pricing_strategies(analysis_results):
    # Add your decision logic here
    pass

def decision_support_financial_planning(analysis_results):
    # Add your decision logic here
    pass

def decision_support_funding_search(analysis_results):
    # Add your decision logic here
    pass

def decision_support_technology_investment(analysis_results):
    # Add your decision logic here
    pass

def decision_support_risk_analysis(analysis_results):
    # Add your decision logic here
    pass

def decision_support_strategic_alliances_evaluation(analysis_results):
    # Add your decision logic here
    pass

def decision_support_customer_relationships_maintenance(analysis_results):
    # Add your decision logic here
    pass