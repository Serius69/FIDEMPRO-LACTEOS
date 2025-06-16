# utils/equation_validator.py
"""
Enhanced equation validator with daily demand support.
Ensures equations use current day's values, not averages.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional, Set
import ast

logger = logging.getLogger(__name__)


class EquationValidator:
    """Enhanced validator for simulation equations"""
    
    def __init__(self):
        # Variables that should use daily values, not averages
        self.daily_variables = {
            'DPH',  # Daily demand (NOT average!)
            'DE',   # Expected demand for the day
            'TPV',  # Daily sales
            'QPL',  # Daily production
            'IT',   # Daily income
            'GT',   # Daily profit
            # Add more as needed
        }
        
        # Known equation patterns that need correction
        self.problematic_patterns = {
            # Equations using fixed values instead of daily calculations
            r'VPC\s*=\s*30': 'VPC should be calculated based on daily demand and customers',
            r'TCAE\s*=\s*CPD': 'TCAE should consider daily demand constraints',
            r'TPPRO\s*=\s*CPROD': 'TPPRO should be actual production, not capacity',
            
            # Circular dependencies
            r'GT\s*=\s*IT\s*-\s*GT': 'Circular dependency in GT calculation',
            r'II\s*=\s*II\s*\+': 'Circular dependency in inventory calculation',
            
            # Using averages where daily values needed
            r'mean\(DH\)': 'Use current day demand (DPH), not historical average',
            r'average\(': 'Avoid averages in daily calculations',
        }
    
    def validate_and_fix_equations(self, equations_data: List[Dict]) -> List[Dict]:
        """Validate and fix equations for proper daily simulation"""
        fixed_equations = []
        issues_found = []
        
        for eq_data in equations_data:
            expression = eq_data.get('expression', '')
            original_expression = expression
            
            # Apply fixes
            fixed_expression, fixes_applied = self.fix_equation_expression(expression)
            
            # Validate the fixed expression
            is_valid, validation_errors = self.validate_equation(fixed_expression)
            
            if is_valid:
                eq_data['expression'] = fixed_expression
                fixed_equations.append(eq_data)
                
                if fixes_applied:
                    issues_found.append({
                        'equation': eq_data.get('name', 'Unknown'),
                        'original': original_expression,
                        'fixed': fixed_expression,
                        'fixes': fixes_applied
                    })
            else:
                logger.error(f"Invalid equation: {expression}")
                logger.error(f"Validation errors: {validation_errors}")
                
                # Try alternative fix
                alternative = self.suggest_alternative_equation(
                    eq_data.get('name', ''), expression, validation_errors
                )
                if alternative:
                    eq_data['expression'] = alternative
                    fixed_equations.append(eq_data)
                    issues_found.append({
                        'equation': eq_data.get('name', 'Unknown'),
                        'original': original_expression,
                        'fixed': alternative,
                        'fixes': ['Complete rewrite based on equation purpose']
                    })
        
        # Log summary of fixes
        if issues_found:
            logger.info(f"Fixed {len(issues_found)} equations:")
            for issue in issues_found[:5]:  # Show first 5
                logger.info(f"  - {issue['equation']}: {issue['fixes']}")
        
        return fixed_equations
    
    def fix_equation_expression(self, expression: str) -> Tuple[str, List[str]]:
        """Fix common issues in equations"""
        fixes_applied = []
        fixed = expression
        
        # Remove extra whitespace
        fixed = ' '.join(fixed.split())
        
        # Check for problematic patterns
        for pattern, issue in self.problematic_patterns.items():
            if re.search(pattern, fixed, re.IGNORECASE):
                fixes_applied.append(issue)
        
        # Specific fixes for daily calculations
        replacements = {
            # Replace static values with dynamic calculations
            'VPC = 30': 'VPC = DPH / max(CPD, 1)',
            'TCAE = CPD': 'TCAE = min(CPD, DPH / max(VPC, 1))',
            'TPPRO = CPROD': 'TPPRO = QPL',
            'PPL = CPROD * CPPL / 100': 'PPL = QPL',
            
            # Fix circular dependencies
            'GT = IT - GT': 'GT = IT - TG',
            'II = II + PI - UII': 'II = max(0, PI - UII)',
            'IPF = IPF + PPL - VPC': 'IPF = max(0, PPL - TPV)',
            
            # Replace averages with current values
            'mean(DH)': 'DPH',
            'average(DH)': 'DPH',
            'promedio(DH)': 'DPH',
            
            # Ensure demand-responsive calculations
            'CPROD': 'min(CPROD, DPH * 1.2)',  # Cap production by demand
            
            # Fix inventory calculations
            'SI': 'max(SI, DPH * DPL)',  # Safety stock based on current demand
        }
        
        for old, new in replacements.items():
            if old in fixed:
                fixed = fixed.replace(old, new)
                fixes_applied.append(f"Replaced '{old}' with '{new}'")
        
        # Ensure proper operator spacing
        fixed = re.sub(r'([+\-*/=])', r' \1 ', fixed)
        fixed = ' '.join(fixed.split())
        
        # Add bounds checking for critical variables
        if 'TPV' in fixed and 'TPV =' in fixed:
            if 'min(' not in fixed:
                # Ensure sales don't exceed demand or inventory
                fixed = fixed.replace('TPV =', 'TPV = min(DPH, ')
                fixed += ')'
                fixes_applied.append("Added demand constraint to sales")
        
        return fixed, fixes_applied
    
    def validate_equation(self, expression: str) -> Tuple[bool, List[str]]:
        """Validate equation structure and logic"""
        errors = []
        
        # Basic structure check
        if '=' not in expression:
            errors.append("Missing equals sign")
            return False, errors
        
        parts = expression.split('=')
        if len(parts) != 2:
            errors.append("Multiple equals signs")
            return False, errors
        
        lhs, rhs = parts[0].strip(), parts[1].strip()
        
        # Left side validation
        if not lhs:
            errors.append("Empty left-hand side")
        elif not re.match(r'^[A-Z][A-Z0-9_]*$', lhs):
            errors.append(f"Invalid variable name on left side: {lhs}")
        
        # Right side validation
        if not rhs:
            errors.append("Empty right-hand side")
        else:
            # Check for circular dependencies
            if lhs in self._extract_variables(rhs):
                errors.append(f"Circular dependency: {lhs} appears on both sides")
            
            # Validate expression syntax
            syntax_errors = self._validate_expression_syntax(rhs)
            errors.extend(syntax_errors)
            
            # Check for daily variable usage
            daily_usage_errors = self._check_daily_variable_usage(lhs, rhs)
            errors.extend(daily_usage_errors)
        
        return len(errors) == 0, errors
    
    def _extract_variables(self, expression: str) -> Set[str]:
        """Extract all variable names from expression"""
        # Pattern for variable names (uppercase letters followed by optional numbers/underscore)
        var_pattern = re.compile(r'\b[A-Z][A-Z0-9_]*\b')
        variables = set(var_pattern.findall(expression))
        
        # Remove function names
        functions = {'max', 'min', 'abs', 'round', 'ceil', 'floor', 'sqrt'}
        variables -= functions
        
        return variables
    
    def _validate_expression_syntax(self, expression: str) -> List[str]:
        """Validate expression syntax"""
        errors = []
        
        # Check parentheses balance
        if expression.count('(') != expression.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for common syntax errors
        if re.search(r'[+\-*/]{2,}', expression):
            errors.append("Consecutive operators found")
        
        # Try to parse as AST to check syntax
        try:
            # Replace variables with numbers for parsing
            test_expr = expression
            for var in self._extract_variables(expression):
                test_expr = test_expr.replace(var, '1')
            
            # Replace functions
            test_expr = test_expr.replace('max', 'max')
            test_expr = test_expr.replace('min', 'min')
            
            ast.parse(test_expr, mode='eval')
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        
        return errors
    
    def _check_daily_variable_usage(self, lhs: str, rhs: str) -> List[str]:
        """Check if daily variables are used correctly"""
        warnings = []
        
        # If calculating a daily variable, ensure inputs are also daily
        if lhs in self.daily_variables:
            rhs_vars = self._extract_variables(rhs)
            
            # Check for problematic patterns
            if 'mean' in rhs.lower() or 'average' in rhs.lower():
                warnings.append(f"{lhs} is a daily variable but uses averages")
            
            # Specific checks for key variables
            if lhs == 'TPV':  # Daily sales
                if 'DPH' not in rhs_vars and 'DE' not in rhs_vars:
                    warnings.append("TPV should be constrained by daily demand (DPH)")
            
            if lhs == 'QPL':  # Daily production
                if 'DPH' not in rhs_vars and 'POD' not in rhs_vars:
                    warnings.append("QPL should respond to daily demand (DPH)")
        
        return warnings
    
    def suggest_alternative_equation(self, name: str, expression: str, 
                                   errors: List[str]) -> Optional[str]:
        """Suggest alternative equation based on name and errors"""
        # Database of correct equations by name
        correct_equations = {
            # Demand and Sales
            "Demanda Promedio Histórica": "DPH = DH",  # Use current day's demand
            "Demanda Diaria Proyectada": "DDP = DPH * ED",
            "Ventas por Cliente": "VPC = DPH / max(CPD, 1)",
            "Total Productos Vendidos": "TPV = min(DPH, TCAE * VPC, IPF + PPL)",
            "Demanda Insatisfecha": "DI = max(0, DPH - TPV)",
            
            # Production
            "Producción Objetivo Diaria": "POD = DPH + max(SI - IPF, 0)",
            "Cantidad producida de productos lácteos": "QPL = min(POD, CPROD, II / CINSP)",
            "Productos Producidos por Lote": "PPL = QPL",
            "Total Productos Producidos": "TPPRO = QPL",
            
            # Financial
            "Ingresos Totales": "IT = TPV * PVP",
            "Gastos Operativos": "GO = CFD + (SE / 30) + CTAI",
            "Gastos Generales": "GG = (GMM / 30) + CTTL + CA + CTM",
            "Total Gastos": "TG = GO + GG",
            "Ganancias Totales": "GT = IT - TG",
            
            # Inventory
            "Inventario Productos Finales": "IPF = max(0, min(IPF + PPL - TPV, CMIPF))",
            "Inventario Insumos": "II = max(0, II + PI - UII)",
            "Pedido Insumos": "PI = max(0, (DPH * CINSP * (TR + DPL)) - II)",
            "Uso de Inventario Insumos": "UII = QPL * CINSP",
            
            # Efficiency
            "Factor Utilización": "FU = QPL / max(CPROD, 1)",
            "Productividad Empleados": "PE = QPL / max(NEPP, 1)",
            "Nivel Servicio al Cliente": "NSC = TPV / max(DPH, 1)",
        }
        
        # Try to find correct equation by name
        if name in correct_equations:
            return correct_equations[name]
        
        # Try to infer from errors
        if "Circular dependency" in str(errors):
            if "GT" in expression:
                return "GT = IT - TG"
            elif "II" in expression:
                return "II = max(0, II_previous + PI - UII)"
            elif "IPF" in expression:
                return "IPF = max(0, IPF_previous + PPL - TPV)"
        
        return None
    
    def get_equation_dependencies(self, expression: str) -> Dict[str, List[str]]:
        """Get dependencies for proper calculation order"""
        if '=' not in expression:
            return {}
        
        lhs, rhs = expression.split('=', 1)
        output_var = lhs.strip()
        input_vars = list(self._extract_variables(rhs))
        
        return {output_var: input_vars}
    
    def sort_equations_by_dependencies(self, equations: List[Dict]) -> List[Dict]:
        """Sort equations for proper calculation order"""
        # Build dependency graph
        dependencies = {}
        equation_map = {}
        
        for eq in equations:
            expr = eq.get('expression', '')
            deps = self.get_equation_dependencies(expr)
            for output, inputs in deps.items():
                dependencies[output] = inputs
                equation_map[output] = eq
        
        # Topological sort
        sorted_vars = []
        visited = set()
        temp_visited = set()
        
        def visit(var):
            if var in temp_visited:
                logger.warning(f"Circular dependency detected for variable: {var}")
                return
            if var in visited:
                return
            
            temp_visited.add(var)
            
            # Visit dependencies first
            if var in dependencies:
                for dep in dependencies[var]:
                    if dep in dependencies:  # Only visit output variables
                        visit(dep)
            
            temp_visited.remove(var)
            visited.add(var)
            sorted_vars.append(var)
        
        # Visit all variables
        for var in dependencies:
            if var not in visited:
                visit(var)
        
        # Build sorted equation list
        sorted_equations = []
        added = set()
        
        # Add equations in dependency order
        for var in sorted_vars:
            if var in equation_map and var not in added:
                sorted_equations.append(equation_map[var])
                added.add(var)
        
        # Add any remaining equations
        for eq in equations:
            if eq not in sorted_equations:
                sorted_equations.append(eq)
        
        return sorted_equations
    
    def validate_equation_set(self, equations: List[Dict]) -> Dict[str, Any]:
        """Validate complete set of equations"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'dependency_graph': {},
            'calculation_order': []
        }
        
        # Check individual equations
        for eq in equations:
            expression = eq.get('expression', '')
            is_valid, errors = self.validate_equation(expression)
            
            if not is_valid:
                results['valid'] = False
                results['errors'].append({
                    'equation': eq.get('name', 'Unknown'),
                    'expression': expression,
                    'errors': errors
                })
        
        # Check for missing critical equations
        critical_outputs = ['TPV', 'QPL', 'IT', 'GT', 'IPF', 'II']
        defined_outputs = set()
        
        for eq in equations:
            deps = self.get_equation_dependencies(eq.get('expression', ''))
            defined_outputs.update(deps.keys())
        
        missing = set(critical_outputs) - defined_outputs
        if missing:
            results['warnings'].append(f"Missing equations for critical variables: {missing}")
        
        # Generate dependency graph
        for eq in equations:
            deps = self.get_equation_dependencies(eq.get('expression', ''))
            results['dependency_graph'].update(deps)
        
        # Calculate proper order
        sorted_equations = self.sort_equations_by_dependencies(equations)
        results['calculation_order'] = [eq.get('name', 'Unknown') for eq in sorted_equations]
        
        return results