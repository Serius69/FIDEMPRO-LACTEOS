# services/simulation_math.py
"""
Mathematical engine for daily business simulations.
Handles all equation calculations with proper daily demand usage.
"""
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class SimulationMathEngine:
    """
    Core mathematical engine for daily simulation calculations.
    All calculations are based on DAILY demand, not historical averages.
    """
    
    def __init__(self):
        self.MIN_DEMAND = 1.0  # Minimum demand to avoid division by zero
        self.SAFETY_FACTOR = 1.65  # Standard safety factor (95% confidence)
        
    def calculate_daily_demand_metrics(self, current_demand: float, 
                                     demand_history: List[float],
                                     seasonality: float = 1.0) -> Dict[str, float]:
        """
        Calculate demand-related metrics for current simulation day.
        
        Args:
            current_demand: Today's simulated demand (DPH)
            demand_history: List of previous demands (for trend analysis)
            seasonality: Seasonality factor (ED)
            
        Returns:
            Dictionary with demand metrics
        """
        # DPH is the CURRENT DAY'S demand, not an average!
        dph = max(current_demand, self.MIN_DEMAND)
        
        # Calculate moving statistics from recent history
        window_size = min(7, len(demand_history))
        if window_size > 0:
            recent_demands = demand_history[-window_size:]
            dsd = float(np.std(recent_demands)) if len(recent_demands) > 1 else dph * 0.1
            recent_mean = float(np.mean(recent_demands))
        else:
            dsd = dph * 0.1  # 10% estimated variation
            recent_mean = dph
        
        # Coefficient of variation
        cvd = dsd / max(recent_mean, self.MIN_DEMAND)
        
        # Daily projected demand (with seasonality and trend adjustment)
        trend_factor = 1.0
        if len(demand_history) >= 3:
            # Simple trend detection from last 3 days
            recent_3 = demand_history[-3:]
            if recent_3[-1] > recent_3[0]:
                trend_factor = 1.0 + min(0.1, (recent_3[-1] - recent_3[0]) / recent_3[0])
        
        ddp = dph * seasonality * trend_factor
        
        return {
            'DPH': dph,  # Current day's demand (NOT average!)
            'DSD': dsd,  # Recent standard deviation
            'CVD': cvd,  # Coefficient of variation
            'DDP': ddp,  # Projected demand with adjustments
            'RECENT_MEAN': recent_mean  # For reference only
        }
    
    def calculate_sales_metrics(self, demand_metrics: Dict[str, float],
                               customer_data: Dict[str, float],
                               inventory: float,
                               production: float) -> Dict[str, float]:
        """
        Calculate sales metrics based on current day's demand.
        """
        dph = demand_metrics['DPH']  # Today's demand
        ddp = demand_metrics['DDP']  # Adjusted demand
        cpd = customer_data.get('CPD', 85)  # Customers per day
        base_vpc = customer_data.get('VPC', 30)  # Base units per customer
        
        # Adjust VPC based on current demand vs typical demand
        vpc_adjustment = 1.0
        if 'RECENT_MEAN' in demand_metrics and demand_metrics['RECENT_MEAN'] > 0:
            demand_ratio = dph / demand_metrics['RECENT_MEAN']
            vpc_adjustment = 0.8 + 0.4 * min(1.5, demand_ratio)  # Between 0.8x and 1.2x
        
        vpc = base_vpc * vpc_adjustment
        
        # Customers served depends on demand and capacity
        max_customers_by_demand = ddp / max(vpc, 1)
        tcae = min(cpd, max_customers_by_demand, cpd * 1.2)  # Max 20% over normal
        
        # Actual sales limited by multiple factors
        max_sales_by_customers = tcae * vpc
        max_sales_by_inventory = inventory + production
        tpv = min(ddp, max_sales_by_customers, max_sales_by_inventory)
        
        # Unmet demand
        di = max(0, ddp - tpv)
        
        # Service level
        nsc = tpv / max(ddp, self.MIN_DEMAND)
        
        return {
            'VPC': vpc,
            'TCAE': tcae,
            'TPV': tpv,
            'DI': di,
            'NSC': nsc,
            'DEMAND_FULFILLMENT_RATE': tpv / dph if dph > 0 else 0
        }
    
    def calculate_production_metrics(self, demand_metrics: Dict[str, float],
                                   production_params: Dict[str, float],
                                   inventory_levels: Dict[str, float],
                                   workforce: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate production based on current day's demand and constraints.
        """
        dph = demand_metrics['DPH']  # Today's demand
        dsd = demand_metrics['DSD']
        ddp = demand_metrics['DDP']
        
        # Extract parameters
        cppl = production_params.get('CPPL', 500)  # Capacity per production lot
        tpe = production_params.get('TPE', 45)  # Time per unit (minutes)
        mlp = workforce.get('MLP', 480)  # Minutes available per day
        nepp = workforce.get('NEPP', 15)  # Number of employees
        cinsp = production_params.get('CINSP', 1.05)  # Input conversion factor
        
        ipf = inventory_levels.get('IPF', 0)  # Current finished goods inventory
        ii = inventory_levels.get('II', 0)  # Current raw materials inventory
        
        # Production target based on TODAY's demand plus safety stock
        safety_stock = dsd * self.SAFETY_FACTOR
        pod = dph + safety_stock + max(0, (ddp - dph) * 0.5)
        
        # Adjust for current inventory
        production_needed = max(pod - ipf, dph * 0.8)  # At least 80% of daily demand
        
        # Production capacity constraints
        capacity_by_time = (nepp * mlp / tpe) * 0.85  # 85% efficiency
        capacity_by_materials = (ii / cinsp) * 0.95  # 95% material efficiency
        capacity_by_equipment = production_params.get('CIP', 3000)  # Equipment limit
        
        # Actual production
        qpl = min(production_needed, capacity_by_time, capacity_by_materials, capacity_by_equipment)
        
        # Production in lots
        ppl = qpl  # Simplified: daily production equals QPL
        tppro = ppl  # Total produced today
        
        # Efficiency metrics
        fu = qpl / max(capacity_by_equipment, self.MIN_DEMAND)  # Facility utilization
        ep = qpl / max(dph * 1.1, self.MIN_DEMAND)  # Production efficiency vs demand
        
        return {
            'POD': pod,
            'QPL': qpl,
            'PPL': ppl,
            'TPPRO': tppro,
            'FU': fu,
            'EP': ep,
            'CPROD': capacity_by_equipment,
            'PRODUCTION_TO_DEMAND_RATIO': qpl / dph if dph > 0 else 0
        }
    
    def calculate_inventory_metrics(self, demand_metrics: Dict[str, float],
                                  production_metrics: Dict[str, float],
                                  sales_metrics: Dict[str, float],
                                  inventory_params: Dict[str, float],
                                  current_inventory: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate inventory movements and levels for the day.
        """
        dph = demand_metrics['DPH']
        dsd = demand_metrics['DSD']
        dpl = inventory_params.get('DPL', 3)  # Lead time days
        tr = inventory_params.get('TR', 3)  # Replenishment time
        cinsp = inventory_params.get('CINSP', 1.05)
        cmipf = inventory_params.get('CMIPF', 20000)  # Max inventory capacity
        
        # Current levels
        ipf_start = current_inventory.get('IPF', 0)
        ii_start = current_inventory.get('II', 0)
        
        # Production and sales
        ppl = production_metrics['PPL']
        tpv = sales_metrics['TPV']
        qpl = production_metrics['QPL']
        
        # Finished goods inventory movement
        ipf_end = max(0, min(ipf_start + ppl - tpv, cmipf))
        
        # Optimal inventory levels based on CURRENT demand
        iop = dph * dpl + dsd * np.sqrt(dpl) * self.SAFETY_FACTOR
        dci = ipf_end / max(dph, self.MIN_DEMAND)  # Days of coverage
        
        # Inventory turnover (monthly projection)
        average_inventory = (ipf_start + ipf_end) / 2
        rti = (dph * 30) / max(average_inventory, self.MIN_DEMAND)
        
        # Raw materials planning
        expected_consumption = dph * cinsp * (tr + dpl)
        safety_stock_rm = dsd * cinsp * np.sqrt(tr + dpl) * self.SAFETY_FACTOR
        ioi = expected_consumption + safety_stock_rm
        
        # Order calculation
        consumption_during_lead = dph * cinsp * tr
        pi = max(0, ioi - ii_start + consumption_during_lead)
        
        # Raw material usage
        uii = qpl * cinsp
        ii_end = max(0, ii_start + pi - uii)
        
        return {
            'IPF': ipf_end,
            'II': ii_end,
            'IOP': iop,
            'IOI': ioi,
            'DCI': dci,
            'RTI': rti,
            'PI': pi,
            'UII': uii,
            'INVENTORY_HEALTH': 1.0 if dci >= 1 and dci <= 5 else 0.5
        }
    
    def calculate_financial_metrics(self, demand_metrics: Dict[str, float],
                                  sales_metrics: Dict[str, float],
                                  production_metrics: Dict[str, float],
                                  inventory_metrics: Dict[str, float],
                                  cost_params: Dict[str, float],
                                  price_params: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate financial metrics based on actual daily operations.
        """
        dph = demand_metrics['DPH']
        tpv = sales_metrics['TPV']
        qpl = production_metrics['QPL']
        uii = inventory_metrics['UII']
        ipf = inventory_metrics['IPF']
        pi = inventory_metrics['PI']
        
        # Prices and base costs
        pvp = price_params.get('PVP', 15.50)
        cuip = cost_params.get('CUIP', 8.20)
        cfd = cost_params.get('CFD', 1800)
        se_monthly = cost_params.get('SE', 48000)
        gmm_monthly = cost_params.get('GMM', 3500)
        cutrans = cost_params.get('CUTRANS', 0.35)
        ctplv = cost_params.get('CTPLV', 1500)
        
        # Daily conversions
        se_daily = se_monthly / 30
        gmm_daily = gmm_monthly / 30
        
        # Revenue (based on actual sales)
        it = tpv * pvp
        
        # Expected revenue (for comparison)
        ie = dph * pvp
        
        # Direct costs
        volume_discount = 0.05 if pi > dph * 3 else 0  # 5% discount for large orders
        ctai = uii * cuip * (1 - volume_discount)
        
        # Variable unit cost (with scale penalties)
        production_efficiency = qpl / max(dph, self.MIN_DEMAND)
        scale_penalty = 0.1 * (1 - min(1, production_efficiency))
        cvu = (ctai / max(qpl, self.MIN_DEMAND)) * (1 + scale_penalty)
        
        # Operating costs (partially variable)
        fixed_portion = cfd * 0.7
        variable_portion = cfd * 0.3 * production_efficiency
        go = fixed_portion + variable_portion + se_daily + ctai
        
        # Transportation costs
        trips_needed = np.ceil(tpv / ctplv) if ctplv > 0 else 0
        volume_efficiency = 0.8 + 0.2 * min(1, tpv / dph)
        cttl = trips_needed * cutrans * 50 * volume_efficiency
        
        # Storage costs
        storage_base = ipf * pvp * 0.002 + 100 * (ipf > 0)
        excess_penalty = 50 * max(0, (ipf - dph * 3) / dph)
        ca = storage_base + excess_penalty
        
        # Losses and waste
        overproduction_factor = max(0, (qpl - dph * 1.2) / dph)
        mp = qpl * (0.015 + 0.005 * overproduction_factor)  # Production waste
        
        excess_inventory_factor = max(0, (ipf - dph * 2) / dph)
        mi = ipf * (0.005 + 0.01 * excess_inventory_factor)  # Inventory waste
        
        ctm = (mp + mi) * pvp * 0.7  # Cost of losses
        
        # General expenses
        marketing_efficiency = tpv / max(dph * 0.8, self.MIN_DEMAND)
        gg = gmm_daily * marketing_efficiency + cttl + ca + ctm
        
        # Totals
        tg = go + gg
        gt = it - tg
        
        # Margins and ratios
        ib = it - ctai
        mb = ib / max(it, self.MIN_DEMAND)
        nr = gt / max(it, self.MIN_DEMAND)
        
        # Performance vs expected
        rve = gt / max(ie * mb, self.MIN_DEMAND) if mb > 0 else 0
        
        # Break-even
        contribution_margin = pvp - cvu
        ped = (cfd + se_daily + gmm_daily) / max(contribution_margin, 0.01)
        
        # ROI adjusted for performance
        roi_base = gt / max(abs(tg), self.MIN_DEMAND)
        roi_adjusted = roi_base * (tpv / max(dph, self.MIN_DEMAND)) * sales_metrics['NSC']
        
        return {
            'IT': it,
            'IE': ie,
            'CTAI': ctai,
            'CVU': cvu,
            'GO': go,
            'CTTL': cttl,
            'CA': ca,
            'MP': mp,
            'MI': mi,
            'CTM': ctm,
            'GG': gg,
            'TG': tg,
            'GT': gt,
            'IB': ib,
            'MB': mb,
            'NR': nr,
            'RVE': rve,
            'PED': ped,
            'RI': roi_adjusted,
            'PROFIT_PER_UNIT': gt / tpv if tpv > 0 else 0,
            'COST_EFFICIENCY': 1 - (tg / it) if it > 0 else 0
        }
    
    def calculate_hr_metrics(self, production_metrics: Dict[str, float],
                           workforce_params: Dict[str, float],
                           financial_metrics: Dict[str, float],
                           demand_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate human resources and productivity metrics.
        """
        qpl = production_metrics['QPL']
        dph = demand_metrics['DPH']
        
        nepp = workforce_params.get('NEPP', 15)
        mlp = workforce_params.get('MLP', 480)
        tpe = workforce_params.get('TPE', 45)
        cppl = workforce_params.get('CPPL', 500)
        se_monthly = workforce_params.get('SE', 48000)
        se_daily = se_monthly / 30
        
        # Productivity metrics
        productivity_actual = qpl / max(nepp, 1)
        productivity_expected = dph / max(nepp, 1)
        pe = productivity_actual / max(productivity_expected, self.MIN_DEMAND)
        
        # Time calculations
        production_lots = dph / max(cppl, 1)
        hnp = production_lots * tpe  # Hours needed for expected production
        
        actual_time_used = (qpl / max(dph, self.MIN_DEMAND)) * hnp
        ho = max(0, mlp - actual_time_used)  # Idle time
        
        # Cost of idle time
        cost_per_minute = (se_daily / nepp) / mlp
        cho = ho * cost_per_minute
        
        # Efficiency metrics
        labor_efficiency = actual_time_used / mlp if mlp > 0 else 0
        cost_per_unit_produced = (se_daily / qpl) if qpl > 0 else 0
        
        return {
            'PE': pe,
            'HNP': hnp,
            'HO': ho,
            'CHO': cho,
            'LABOR_EFFICIENCY': labor_efficiency,
            'PRODUCTIVITY_ACTUAL': productivity_actual,
            'COST_PER_UNIT_LABOR': cost_per_unit_produced
        }
    
    def calculate_marketing_metrics(self, sales_metrics: Dict[str, float],
                                  financial_metrics: Dict[str, float],
                                  demand_metrics: Dict[str, float],
                                  marketing_params: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate marketing effectiveness and customer metrics.
        """
        tpv = sales_metrics['TPV']
        tcae = sales_metrics['TCAE']
        vpc = sales_metrics['VPC']
        dph = demand_metrics['DPH']
        
        gmm_monthly = marketing_params.get('GMM', 3500)
        gmm_daily = gmm_monthly / 30
        pvp = marketing_params.get('PVP', 15.50)
        cpd = marketing_params.get('CPD', 85)
        
        # Marketing effectiveness
        sales_growth = max(0, (tpv - dph) / max(dph, self.MIN_DEMAND))
        marketing_investment_ratio = gmm_daily / (dph * pvp) if dph > 0 else 0
        em = sales_growth / max(marketing_investment_ratio, 0.01)
        
        # Customer acquisition cost
        base_customers = dph / max(vpc, 1)
        new_customers = max(0, tcae - base_customers) * 0.5  # Assume 50% are new
        cuac = gmm_daily / max(new_customers, 1)
        
        # Purchase frequency
        expected_frequency = dph / (cpd * vpc) if cpd > 0 and vpc > 0 else 1
        actual_frequency = tcae / cpd if cpd > 0 else 0
        fc = actual_frequency / max(expected_frequency, self.MIN_DEMAND)
        
        # Customer lifetime value estimate (simplified)
        avg_purchase_value = pvp * vpc
        purchase_frequency_monthly = fc * 30
        clv_monthly = avg_purchase_value * purchase_frequency_monthly * financial_metrics.get('MB', 0.3)
        
        return {
            'EM': em,
            'CUAC': cuac,
            'FC': fc,
            'CLV_MONTHLY': clv_monthly,
            'MARKETING_ROI': (tpv * pvp - dph * pvp) / gmm_daily if gmm_daily > 0 else 0,
            'NEW_CUSTOMERS': new_customers
        }
    
    def calculate_competition_metrics(self, sales_metrics: Dict[str, float],
                                    demand_metrics: Dict[str, float],
                                    price_params: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate competitive position metrics.
        """
        tpv = sales_metrics['TPV']
        nsc = sales_metrics['NSC']
        dph = demand_metrics['DPH']
        
        pvp = price_params.get('PVP', 15.50)
        pc = price_params.get('PC', 15.80)
        
        # Market share (assuming market is 10x our historical average)
        market_size_estimate = dph * 10
        pm = tpv / max(market_size_estimate, self.MIN_DEMAND)
        
        # Price competitiveness
        price_difference = abs(pvp - pc) / max(pc, self.MIN_DEMAND)
        price_advantage = 1 - price_difference if pvp <= pc else 0.5 - price_difference
        
        # Competitiveness index
        ic = (0.3 * price_advantage + 
              0.4 * nsc + 
              0.3 * (tpv / max(dph, self.MIN_DEMAND)))
        
        # Competitive position
        if pvp < pc * 0.95:
            position = "PRICE_LEADER"
        elif pvp > pc * 1.05:
            position = "PREMIUM"
        else:
            position = "COMPETITIVE"
        
        return {
            'PM': pm,
            'IC': ic,
            'NCM': price_difference,
            'PRICE_POSITION': position,
            'PRICE_ADVANTAGE': price_advantage
        }
    
    def calculate_kpi_metrics(self, all_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate overall Key Performance Indicators.
        """
        # Extract key values from all metrics
        demand = all_metrics.get('demand', {})
        sales = all_metrics.get('sales', {})
        production = all_metrics.get('production', {})
        financial = all_metrics.get('financial', {})
        inventory = all_metrics.get('inventory', {})
        
        dph = demand.get('DPH', 1)
        ddp = demand.get('DDP', 1)
        tpv = sales.get('TPV', 0)
        nsc = sales.get('NSC', 0)
        qpl = production.get('QPL', 0)
        ep = production.get('EP', 0)
        gt = financial.get('GT', 0)
        ie = financial.get('IE', 1)
        mp = financial.get('MP', 0)
        mi = financial.get('MI', 0)
        
        # Demand total (for compatibility)
        dt = ddp
        
        # Overall Equipment Effectiveness (OEE)
        availability = ep
        performance = qpl / max(dph * 1.2, self.MIN_DEMAND)
        quality = 1 - (mp + mi) / max(qpl, self.MIN_DEMAND)
        eog = availability * performance * quality * nsc
        
        # Customer satisfaction index
        price_satisfaction = all_metrics.get('competition', {}).get('PRICE_ADVANTAGE', 0.5)
        service_satisfaction = nsc
        unmet_demand_impact = 1 - (sales.get('DI', 0) / max(ddp, self.MIN_DEMAND))
        isc = (0.5 * service_satisfaction + 
               0.3 * price_satisfaction + 
               0.2 * unmet_demand_impact)
        
        # Global performance index
        sales_performance = tpv / max(dph, self.MIN_DEMAND)
        operational_efficiency = eog
        customer_satisfaction = isc
        financial_performance = gt / max(ie * 0.15, self.MIN_DEMAND)  # Expect 15% margin
        
        idg = (0.3 * sales_performance + 
               0.2 * operational_efficiency + 
               0.2 * customer_satisfaction + 
               0.3 * financial_performance)
        
        # Health score (0-100)
        health_score = min(100, max(0, idg * 100))
        
        return {
            'DT': dt,
            'EOG': eog,
            'ISC': isc,
            'IDG': idg,
            'HEALTH_SCORE': health_score,
            'PERFORMANCE_RATING': self._get_performance_rating(health_score)
        }
    
    def _get_performance_rating(self, score: float) -> str:
        """Get performance rating based on health score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"
    
    def simulate_complete_day(self, 
                            current_demand: float,
                            previous_state: Dict[str, Any],
                            parameters: Dict[str, Any],
                            demand_history: List[float]) -> Dict[str, Any]:
        """
        Simulate a complete business day with all calculations.
        
        Args:
            current_demand: Today's simulated demand (DPH for this day)
            previous_state: Previous day's state (inventories, etc.)
            parameters: Business parameters from questionnaire
            demand_history: List of previous demands for trend analysis
            
        Returns:
            Complete simulation results for the day
        """
        # Initialize current inventory from previous state
        current_inventory = {
            'IPF': previous_state.get('IPF', parameters.get('IPF', 1000)),
            'II': previous_state.get('II', parameters.get('II', 5000))
        }
        
        # Step 1: Demand metrics (using TODAY's demand)
        demand_metrics = self.calculate_daily_demand_metrics(
            current_demand=current_demand,
            demand_history=demand_history,
            seasonality=parameters.get('ED', 1.0)
        )
        
        # Step 2: Sales based on current demand
        sales_metrics = self.calculate_sales_metrics(
            demand_metrics=demand_metrics,
            customer_data={
                'CPD': parameters.get('CPD', 85),
                'VPC': parameters.get('VPC', 30)
            },
            inventory=current_inventory['IPF'],
            production=0  # Will be updated after production calc
        )
        
        # Step 3: Production based on current demand
        production_metrics = self.calculate_production_metrics(
            demand_metrics=demand_metrics,
            production_params={
                'CPPL': parameters.get('CPPL', 500),
                'TPE': parameters.get('TPE', 45),
                'CINSP': parameters.get('CINSP', 1.05),
                'CIP': parameters.get('CPROD', 3000)
            },
            inventory_levels=current_inventory,
            workforce={
                'MLP': parameters.get('MLP', 480),
                'NEPP': parameters.get('NEPP', 15)
            }
        )
        
        # Step 4: Update sales with actual production
        sales_metrics = self.calculate_sales_metrics(
            demand_metrics=demand_metrics,
            customer_data={
                'CPD': parameters.get('CPD', 85),
                'VPC': parameters.get('VPC', 30)
            },
            inventory=current_inventory['IPF'],
            production=production_metrics['PPL']
        )
        
        # Step 5: Inventory movements
        inventory_metrics = self.calculate_inventory_metrics(
            demand_metrics=demand_metrics,
            production_metrics=production_metrics,
            sales_metrics=sales_metrics,
            inventory_params={
                'DPL': parameters.get('DPL', 3),
                'TR': parameters.get('TR', 3),
                'CINSP': parameters.get('CINSP', 1.05),
                'CMIPF': parameters.get('CMIPF', 20000)
            },
            current_inventory=current_inventory
        )
        
        # Step 6: Financial calculations
        financial_metrics = self.calculate_financial_metrics(
            demand_metrics=demand_metrics,
            sales_metrics=sales_metrics,
            production_metrics=production_metrics,
            inventory_metrics=inventory_metrics,
            cost_params={
                'CUIP': parameters.get('CUIP', 8.20),
                'CFD': parameters.get('CFD', 1800),
                'SE': parameters.get('SE', 48000),
                'GMM': parameters.get('GMM', 3500),
                'CUTRANS': parameters.get('CUTRANS', 0.35),
                'CTPLV': parameters.get('CTPLV', 1500)
            },
            price_params={
                'PVP': parameters.get('PVP', 15.50)
            }
        )
        
        # Step 7: HR metrics
        hr_metrics = self.calculate_hr_metrics(
            production_metrics=production_metrics,
            workforce_params={
                'NEPP': parameters.get('NEPP', 15),
                'MLP': parameters.get('MLP', 480),
                'TPE': parameters.get('TPE', 45),
                'CPPL': parameters.get('CPPL', 500),
                'SE': parameters.get('SE', 48000)
            },
            financial_metrics=financial_metrics,
            demand_metrics=demand_metrics
        )
        
        # Step 8: Marketing metrics
        marketing_metrics = self.calculate_marketing_metrics(
            sales_metrics=sales_metrics,
            financial_metrics=financial_metrics,
            demand_metrics=demand_metrics,
            marketing_params={
                'GMM': parameters.get('GMM', 3500),
                'PVP': parameters.get('PVP', 15.50),
                'CPD': parameters.get('CPD', 85)
            }
        )
        
        # Step 9: Competition metrics
        competition_metrics = self.calculate_competition_metrics(
            sales_metrics=sales_metrics,
            demand_metrics=demand_metrics,
            price_params={
                'PVP': parameters.get('PVP', 15.50),
                'PC': parameters.get('PC', 15.80)
            }
        )
        
        # Step 10: Overall KPIs
        all_metrics = {
            'demand': demand_metrics,
            'sales': sales_metrics,
            'production': production_metrics,
            'inventory': inventory_metrics,
            'financial': financial_metrics,
            'hr': hr_metrics,
            'marketing': marketing_metrics,
            'competition': competition_metrics
        }
        
        kpi_metrics = self.calculate_kpi_metrics(all_metrics)
        
        # Combine all results
        day_results = {
            **demand_metrics,
            **sales_metrics,
            **production_metrics,
            **inventory_metrics,
            **financial_metrics,
            **hr_metrics,
            **marketing_metrics,
            **competition_metrics,
            **kpi_metrics
        }
        
        # Add metadata
        day_results['_metadata'] = {
            'simulated_demand': current_demand,
            'demand_fulfillment': sales_metrics.get('TPV', 0) / current_demand if current_demand > 0 else 0,
            'profit_margin': financial_metrics.get('NR', 0),
            'service_level': sales_metrics.get('NSC', 0),
            'health_score': kpi_metrics.get('HEALTH_SCORE', 0)
        }
        
        # Store state for next day
        day_results['_state'] = {
            'IPF': inventory_metrics['IPF'],
            'II': inventory_metrics['II'],
            'last_demand': current_demand,
            'last_sales': sales_metrics['TPV'],
            'last_production': production_metrics['QPL']
        }
        
        return day_results