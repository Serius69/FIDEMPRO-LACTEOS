# utils/data_parsers.py
"""
Enhanced data parsing utilities for simulation system.
Handles various data formats from questionnaires and user inputs.
"""
import re
import json
import logging
from typing import List, Any, Optional, Union, Dict
import numpy as np

logger = logging.getLogger(__name__)


class DataParser:
    """Unified data parser for simulation inputs"""
    
    def __init__(self):
        self.number_pattern = re.compile(r'-?\d+\.?\d*')
        self.whitespace_pattern = re.compile(r'\s+')
        
    def parse_demand_history(self, demand_data: Any) -> List[float]:
        """
        Parse demand history from various formats into list of floats.
        
        Args:
            demand_data: Can be string, list, JSON, or other formats
            
        Returns:
            List of float values representing demand history
        """
        try:
            # Case 1: Already a list
            if isinstance(demand_data, list):
                return self._clean_numeric_list(demand_data)
            
            # Case 2: JSON string
            if isinstance(demand_data, str):
                # Try JSON parse first
                try:
                    parsed = json.loads(demand_data)
                    if isinstance(parsed, list):
                        return self._clean_numeric_list(parsed)
                except json.JSONDecodeError:
                    pass
                
                # Clean string and extract numbers
                return self._parse_string_data(demand_data)
            
            # Case 3: Single numeric value
            if isinstance(demand_data, (int, float)):
                return [float(demand_data)]
            
            # Case 4: Dictionary with 'data' key
            if isinstance(demand_data, dict) and 'data' in demand_data:
                return self.parse_demand_history(demand_data['data'])
            
            logger.warning(f"Unknown demand data format: {type(demand_data)}")
            return []
            
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
            return []
    
    def _parse_string_data(self, data_str: str) -> List[float]:
        """Parse string data with various delimiters and formats"""
        # Remove common artifacts
        cleaned = data_str.strip()
        cleaned = re.sub(r'[\[\]{}()]', ' ', cleaned)  # Remove brackets
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)     # Remove HTML tags
        cleaned = cleaned.replace('\\n', ' ')           # Remove escaped newlines
        cleaned = cleaned.replace('\n', ' ')            # Remove newlines
        
        # Try different delimiter strategies
        numbers = []
        
        # Strategy 1: Look for comma-separated values
        if ',' in cleaned:
            parts = cleaned.split(',')
            for part in parts:
                nums = self._extract_numbers(part)
                numbers.extend(nums)
        
        # Strategy 2: Look for semicolon-separated values
        elif ';' in cleaned:
            parts = cleaned.split(';')
            for part in parts:
                nums = self._extract_numbers(part)
                numbers.extend(nums)
        
        # Strategy 3: Look for space-separated values
        elif ' ' in cleaned:
            nums = self._extract_numbers(cleaned)
            numbers.extend(nums)
        
        # Strategy 4: Try to extract all numbers
        else:
            nums = self._extract_numbers(cleaned)
            numbers.extend(nums)
        
        return numbers
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all valid numbers from text"""
        numbers = []
        
        # Find all number-like patterns
        matches = self.number_pattern.findall(text)
        
        for match in matches:
            try:
                # Handle decimal separator variations
                cleaned_match = match.replace(',', '.')
                value = float(cleaned_match)
                
                # Validate reasonable demand values
                if 0 <= value <= 1000000:  # Reasonable range
                    numbers.append(value)
                else:
                    logger.warning(f"Skipping unreasonable value: {value}")
                    
            except ValueError:
                continue
        
        return numbers
    
    def _clean_numeric_list(self, data_list: List[Any]) -> List[float]:
        """Clean and convert list elements to floats"""
        clean_values = []
        
        for item in data_list:
            if item is None:
                continue
            
            try:
                # Handle nested lists
                if isinstance(item, list):
                    clean_values.extend(self._clean_numeric_list(item))
                
                # Handle strings
                elif isinstance(item, str):
                    # Try direct conversion first
                    try:
                        value = float(item.replace(',', '.'))
                        if 0 <= value <= 1000000:
                            clean_values.append(value)
                    except:
                        # Extract numbers from string
                        nums = self._extract_numbers(item)
                        clean_values.extend(nums)
                
                # Handle numeric values
                elif isinstance(item, (int, float)):
                    value = float(item)
                    if 0 <= value <= 1000000:
                        clean_values.append(value)
                
            except Exception as e:
                logger.debug(f"Could not parse item {item}: {e}")
                continue
        
        return clean_values
    
    def parse_numeric_answer(self, answer: Any, 
                           expected_type: Optional[str] = None) -> Optional[float]:
        """
        Parse a single numeric answer from questionnaire.
        
        Args:
            answer: The answer value in any format
            expected_type: Optional hint about expected data type
            
        Returns:
            Float value or None if cannot parse
        """
        if answer is None:
            return None
        
        try:
            # Direct numeric
            if isinstance(answer, (int, float)):
                return float(answer)
            
            # Boolean answers
            if isinstance(answer, bool):
                return 1.0 if answer else 0.0
            
            # String answers
            if isinstance(answer, str):
                # Clean string
                cleaned = answer.strip().lower()
                
                # Handle yes/no for certain types
                if expected_type in ['boolean', 'seasonality']:
                    if cleaned in ['sí', 'si', 'yes', 'true', '1']:
                        return 1.0
                    elif cleaned in ['no', 'false', '0']:
                        return 0.0
                
                # Extract numeric value
                numbers = self._extract_numbers(answer)
                if numbers:
                    return numbers[0]  # Return first valid number
            
            # List answers - return average
            if isinstance(answer, list) and answer:
                values = self._clean_numeric_list(answer)
                if values:
                    return float(np.mean(values))
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not parse numeric answer {answer}: {e}")
            return None
    
    def parse_time_period(self, time_value: Any, 
                         time_unit: str) -> int:
        """
        Parse time period to days.
        
        Args:
            time_value: Numeric time value
            time_unit: Unit (days, weeks, months)
            
        Returns:
            Number of days
        """
        try:
            # Parse numeric value
            if isinstance(time_value, str):
                time_value = self.parse_numeric_answer(time_value)
            
            time_value = int(time_value) if time_value else 1
            
            # Convert to days
            unit_lower = time_unit.lower()
            if unit_lower in ['días', 'dias', 'days', 'day']:
                return time_value
            elif unit_lower in ['semanas', 'weeks', 'week']:
                return time_value * 7
            elif unit_lower in ['meses', 'months', 'month']:
                return time_value * 30
            else:
                logger.warning(f"Unknown time unit: {time_unit}, assuming days")
                return time_value
                
        except Exception as e:
            logger.error(f"Error parsing time period: {e}")
            return 1
    
    def parse_currency_value(self, value: Any) -> Optional[float]:
        """
        Parse currency values, removing symbols and formatting.
        
        Args:
            value: Currency value in any format
            
        Returns:
            Float value without currency symbols
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove currency symbols and formatting
                cleaned = value.strip()
                cleaned = re.sub(r'[Bb][Ss]\.?', '', cleaned)  # Remove Bs/BS
                cleaned = re.sub(r'[$€£¥₹]', '', cleaned)      # Remove currency symbols
                cleaned = cleaned.replace(',', '')              # Remove thousand separators
                cleaned = cleaned.replace(' ', '')              # Remove spaces
                
                # Extract number
                numbers = self._extract_numbers(cleaned)
                if numbers:
                    return numbers[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not parse currency value {value}: {e}")
            return None
    
    def parse_percentage(self, value: Any) -> Optional[float]:
        """
        Parse percentage values to decimal (0-1 range).
        
        Args:
            value: Percentage value in any format
            
        Returns:
            Float value between 0 and 1
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                # If already in decimal form (0-1)
                if 0 <= value <= 1:
                    return float(value)
                # If in percentage form (0-100)
                elif 0 <= value <= 100:
                    return float(value) / 100
                else:
                    logger.warning(f"Percentage value out of range: {value}")
                    return None
            
            if isinstance(value, str):
                # Remove percentage symbol
                cleaned = value.strip().replace('%', '')
                
                # Extract number
                numbers = self._extract_numbers(cleaned)
                if numbers:
                    num = numbers[0]
                    # Convert to decimal if needed
                    if num > 1:
                        return num / 100
                    else:
                        return num
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not parse percentage {value}: {e}")
            return None
    
    def validate_parsed_data(self, data: List[float], 
                           data_type: str = 'demand') -> Dict[str, Any]:
        """
        Validate parsed data for common issues.
        
        Args:
            data: List of parsed values
            data_type: Type of data for context-specific validation
            
        Returns:
            Validation results with warnings and corrections
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'corrections': [],
            'stats': {}
        }
        
        if not data:
            validation['is_valid'] = False
            validation['warnings'].append("No data found")
            return validation
        
        # Calculate statistics
        data_array = np.array(data)
        validation['stats'] = {
            'count': len(data),
            'mean': float(np.mean(data_array)),
            'std': float(np.std(data_array)),
            'min': float(np.min(data_array)),
            'max': float(np.max(data_array)),
            'cv': float(np.std(data_array) / np.mean(data_array)) if np.mean(data_array) > 0 else 0
        }
        
        # Check for common issues
        if data_type == 'demand':
            # Check for too few data points
            if len(data) < 30:
                validation['warnings'].append(
                    f"Only {len(data)} data points found. Minimum 30 recommended for reliable analysis."
                )
            
            # Check for zero or negative values
            negative_count = sum(1 for x in data if x <= 0)
            if negative_count > 0:
                validation['warnings'].append(
                    f"Found {negative_count} non-positive values. Demand should be positive."
                )
                # Correct by removing
                data = [x for x in data if x > 0]
                validation['corrections'].append("Removed non-positive values")
            
            # Check for extreme outliers
            q1, q3 = np.percentile(data_array, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr
            
            outliers = [x for x in data if x < lower_bound or x > upper_bound]
            if outliers:
                validation['warnings'].append(
                    f"Found {len(outliers)} extreme outliers: {outliers[:5]}..."
                )
            
            # Check for unrealistic coefficient of variation
            cv = validation['stats']['cv']
            if cv > 1.0:
                validation['warnings'].append(
                    f"Very high variability (CV={cv:.2f}). Data might be inconsistent."
                )
            elif cv < 0.01:
                validation['warnings'].append(
                    f"Very low variability (CV={cv:.2f}). Data might be too uniform."
                )
        
        return validation
    
    def parse_questionnaire_answers(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse all questionnaire answers into a structured format.
        
        Args:
            answers: List of answer dictionaries from database
            
        Returns:
            Dictionary mapping variable names to parsed values
        """
        parsed_data = {}
        
        for answer in answers:
            try:
                var_initials = answer.get('fk_question__fk_variable__initials')
                answer_value = answer.get('answer')
                question_text = answer.get('fk_question__question', '')
                
                if not answer_value:
                    continue
                
                # Determine parsing strategy based on variable or question
                if var_initials:
                    parsed_value = self._parse_by_variable_type(var_initials, answer_value)
                    if parsed_value is not None:
                        parsed_data[var_initials] = parsed_value
                
                # Also try to map by question text
                if question_text:
                    mapped_var = self._map_question_to_variable(question_text)
                    if mapped_var and mapped_var not in parsed_data:
                        parsed_value = self._parse_by_variable_type(mapped_var, answer_value)
                        if parsed_value is not None:
                            parsed_data[mapped_var] = parsed_value
                            
            except Exception as e:
                logger.debug(f"Error parsing answer: {e}")
                continue
        
        return parsed_data
    
    def _parse_by_variable_type(self, var_name: str, value: Any) -> Any:
        """Parse value based on variable type"""
        # Special handling for specific variables
        if var_name == 'DH':  # Demand history
            return self.parse_demand_history(value)
        
        elif var_name == 'ED':  # Seasonality
            return self.parse_numeric_answer(value, 'seasonality')
        
        elif var_name in ['PVP', 'CUIP', 'CFD', 'CUTRANS']:  # Currency values
            return self.parse_currency_value(value)
        
        elif var_name in ['MB', 'NR', 'FU', 'PE']:  # Percentage values
            return self.parse_percentage(value)
        
        else:  # Default numeric parsing
            return self.parse_numeric_answer(value)
    
    def _map_question_to_variable(self, question_text: str) -> Optional[str]:
        """Map question text to variable name (simplified)"""
        question_lower = question_text.lower()
        
        # Simple keyword mapping
        if 'precio' in question_lower and 'venta' in question_lower:
            return 'PVP'
        elif 'demanda' in question_lower and 'históric' in question_lower:
            return 'DH'
        elif 'cliente' in question_lower and 'día' in question_lower:
            return 'CPD'
        elif 'empleado' in question_lower and 'número' in question_lower:
            return 'NEPP'
        # Add more mappings as needed
        
        return None


class DataValidator:
    """Validator for parsed data"""
    
    @staticmethod
    def validate_demand_data(data: List[float]) -> bool:
        """Validate demand data meets requirements"""
        if not data:
            return False
        
        if len(data) < 30:
            logger.warning(f"Insufficient demand data: {len(data)} points (minimum 30)")
            return False
        
        if any(x <= 0 for x in data):
            logger.warning("Demand data contains non-positive values")
            return False
        
        # Check for reasonable variation
        cv = np.std(data) / np.mean(data) if np.mean(data) > 0 else 0
        if cv > 2.0:
            logger.warning(f"Demand data shows extreme variation (CV={cv:.2f})")
            return False
        
        return True
    
    @staticmethod
    def validate_parameters(params: Dict[str, float]) -> Dict[str, List[str]]:
        """Validate simulation parameters"""
        errors = {}
        
        # Check required parameters
        required = ['PVP', 'CPD', 'NEPP', 'CUIP', 'CFD']
        for param in required:
            if param not in params or params[param] is None:
                if param not in errors:
                    errors[param] = []
                errors[param].append(f"{param} is required")
        
        # Validate ranges
        if 'PVP' in params and params['PVP'] <= 0:
            errors.setdefault('PVP', []).append("Price must be positive")
        
        if 'CPD' in params and params['CPD'] <= 0:
            errors.setdefault('CPD', []).append("Customers per day must be positive")
        
        if 'NEPP' in params and params['NEPP'] < 1:
            errors.setdefault('NEPP', []).append("Must have at least 1 employee")
        
        # Check relationships
        if all(k in params for k in ['SE', 'NEPP']) and params['NEPP'] > 0:
            salary_per_employee = params['SE'] / params['NEPP']
            if salary_per_employee < 1000:  # Assuming monthly salary
                errors.setdefault('SE', []).append("Salary per employee seems too low")
        
        return errors


class DataFormatter:
    """Formatter for output data"""
    
    @staticmethod
    def format_currency(value: float, symbol: str = 'Bs') -> str:
        """Format value as currency"""
        return f"{symbol} {value:,.2f}"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format value as percentage"""
        return f"{value * 100:.{decimal_places}f}%"
    
    @staticmethod
    def format_number(value: float, decimal_places: int = 2) -> str:
        """Format number with thousand separators"""
        return f"{value:,.{decimal_places}f}"
    
    @staticmethod
    def format_simulation_results(results: Dict[str, float]) -> Dict[str, str]:
        """Format simulation results for display"""
        formatted = {}
        
        # Currency fields
        currency_fields = ['IT', 'GT', 'GO', 'TG', 'CTAI', 'PVP', 'CFD', 'CUIP']
        for field in currency_fields:
            if field in results:
                formatted[field] = DataFormatter.format_currency(results[field])
        
        # Percentage fields
        percentage_fields = ['MB', 'NR', 'FU', 'PE', 'NSC', 'PM']
        for field in percentage_fields:
            if field in results:
                formatted[field] = DataFormatter.format_percentage(results[field])
        
        # Quantity fields
        quantity_fields = ['TPV', 'QPL', 'DPH', 'IPF', 'II']
        for field in quantity_fields:
            if field in results:
                formatted[field] = DataFormatter.format_number(results[field], 0) + ' L'
        
        # Other numeric fields
        for key, value in results.items():
            if key not in formatted and isinstance(value, (int, float)):
                formatted[key] = DataFormatter.format_number(value)
        
        return formatted