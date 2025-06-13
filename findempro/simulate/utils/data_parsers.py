# utils/data_parsers.py
import ast
import re
import json
import logging
from typing import List, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from decimal import Decimal

logger = logging.getLogger(__name__)

class DataParser:
    """Utility class for parsing various data formats"""
    
    @staticmethod
    def parse_demand_history(data: Union[str, list, dict, Any]) -> List[float]:
        """
        Parse demand history from various formats
        
        Args:
            data: Demand data in string, list or dict format
            
        Returns:
            List of float values
        """
        try:
            # Handle questionary Answer objects
            if hasattr(data, '__class__') and 'Answer' in str(data.__class__):
                # Try to get the answer attribute
                if hasattr(data, 'answer'):
                    return DataParser.parse_demand_history(data.answer)
                
                # Extract from string representation
                str_repr = str(data)
                # Pattern: <Answer: [2450, 2380, 2520, ...]>
                match = re.search(r'<Answer:\s*(\[.*?\])>', str_repr)
                if match:
                    list_str = match.group(1)
                    try:
                        parsed_list = ast.literal_eval(list_str)
                        return DataParser.parse_demand_history(parsed_list)
                    except:
                        pass
            
            # Handle questionary Answer objects - try common attributes
            if hasattr(data, 'value'):
                return DataParser.parse_demand_history(data.value)
            
            # If already a list of numbers, validate and return
            if isinstance(data, list):
                result = []
                for x in data:
                    if DataParser._is_valid_number(x):
                        try:
                            # Handle string numbers with commas
                            if isinstance(x, str):
                                x = x.replace(',', '')
                            result.append(float(x))
                        except:
                            continue
                return result
            
            # If dict, try to extract values
            if isinstance(data, dict):
                if 'values' in data:
                    return DataParser.parse_demand_history(data['values'])
                elif 'data' in data:
                    return DataParser.parse_demand_history(data['data'])
                else:
                    raise ValueError("Dict format not recognized")
            
            # If string, parse it
            if isinstance(data, str):
                # Remove HTML tags
                data = re.sub(r'<[^>]+>', ' ', data)
                
                # Try to parse as JSON first
                try:
                    json_data = json.loads(data)
                    return DataParser.parse_demand_history(json_data)
                except json.JSONDecodeError:
                    pass
                
                # Check if it's a string representation of a list
                if data.strip().startswith('[') and data.strip().endswith(']'):
                    try:
                        parsed_list = ast.literal_eval(data.strip())
                        return DataParser.parse_demand_history(parsed_list)
                    except:
                        pass
                
                # Remove brackets and quotes
                data = data.replace('[', '').replace(']', '')
                data = data.replace('"', '').replace("'", '')
                
                # Extract numbers - handle comma-separated values properly
                numbers = []
                
                # First try splitting by comma
                if ',' in data:
                    tokens = data.split(',')
                else:
                    tokens = data.split()
                
                for token in tokens:
                    token = token.strip()
                    if DataParser._is_valid_number(token):
                        try:
                            # Remove any trailing comma
                            token = token.rstrip(',')
                            num = float(token)
                            if num > 0:  # Demand should be positive
                                numbers.append(num)
                        except ValueError:
                            continue
                
                return numbers
            
            # Try to convert single number
            if DataParser._is_valid_number(data):
                return [float(data)]
            
            raise ValueError(f"Unsupported data type: {type(data)}")
            
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
            logger.error(f"Data type: {type(data)}")
            logger.error(f"Data content: {str(data)[:200]}")  # Log first 200 chars
            raise
    
    @staticmethod
    def _is_valid_number(value: Any) -> bool:
        """Check if a value can be converted to a number"""
        if isinstance(value, (int, float, Decimal)):
            return True
        
        if isinstance(value, str):
            # Remove common number formatting
            cleaned = value.replace(',', '').replace(' ', '').strip()
            
            # Remove trailing comma if present
            cleaned = cleaned.rstrip(',')
            
            # Check for valid number pattern
            number_pattern = re.compile(r'^-?\d+\.?\d*$')
            return bool(number_pattern.match(cleaned))
        
        return False
    
    @staticmethod
    def parse_equation_expression(expression: str) -> Dict[str, Any]:
        """
        Parse mathematical equation expression
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Dict with parsed components
        """
        try:
            # Clean expression
            expression = expression.strip()
            
            # Extract left and right sides
            if '=' in expression:
                lhs, rhs = expression.split('=', 1)
            else:
                lhs, rhs = expression, ''
            
            # Extract variables (uppercase letters followed by optional letters/numbers)
            variable_pattern = re.compile(r'[A-Z][A-Z0-9]*')
            variables = list(set(variable_pattern.findall(expression)))
            
            # Extract operators
            operators = re.findall(r'[+\-*/^]', expression)
            
            # Extract numbers
            number_pattern = re.compile(r'\d+\.?\d*')
            numbers = [float(n) for n in number_pattern.findall(expression)]
            
            # Check if it's a summation
            has_summation = '∑' in expression or 'sum' in expression.lower()
            
            return {
                'original': expression,
                'lhs': lhs.strip(),
                'rhs': rhs.strip(),
                'variables': variables,
                'operators': operators,
                'numbers': numbers,
                'has_summation': has_summation,
                'is_valid': bool(lhs and variables)
            }
            
        except Exception as e:
            logger.error(f"Error parsing equation: {str(e)}")
            return {
                'original': expression,
                'error': str(e),
                'is_valid': False
            }
    
    @staticmethod
    def parse_csv_data(csv_content: str, delimiter: str = ',', 
                      has_header: bool = True) -> pd.DataFrame:
        """
        Parse CSV data into DataFrame
        
        Args:
            csv_content: CSV content as string
            delimiter: CSV delimiter
            has_header: Whether first row is header
            
        Returns:
            Pandas DataFrame
        """
        try:
            # Try to detect delimiter if not specified
            if delimiter == ',' and '\t' in csv_content[:1000]:
                delimiter = '\t'
            elif delimiter == ',' and ';' in csv_content[:1000]:
                delimiter = ';'
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(
                StringIO(csv_content),
                delimiter=delimiter,
                header=0 if has_header else None
            )
            
            # Clean column names
            if has_header:
                df.columns = df.columns.str.strip()
            
            # Convert numeric columns
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise
    
    @staticmethod
    def parse_time_series_data(data: Union[List, Dict, pd.DataFrame], 
                             date_column: Optional[str] = None,
                             value_column: Optional[str] = None) -> pd.Series:
        """
        Parse time series data into pandas Series
        
        Args:
            data: Time series data
            date_column: Name of date column
            value_column: Name of value column
            
        Returns:
            Pandas Series with DatetimeIndex
        """
        try:
            # Convert to DataFrame if needed
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame.from_dict(data)
            else:
                df = data.copy()
            
            # Identify columns if not specified
            if date_column is None:
                date_cols = [col for col in df.columns 
                           if 'date' in col.lower() or 'time' in col.lower()]
                date_column = date_cols[0] if date_cols else df.columns[0]
            
            if value_column is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                value_column = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1]
            
            # Parse dates
            df[date_column] = pd.to_datetime(df[date_column])
            
            # Create series
            series = pd.Series(
                data=df[value_column].values,
                index=df[date_column]
            )
            
            # Sort by date
            series = series.sort_index()
            
            return series
            
        except Exception as e:
            logger.error(f"Error parsing time series: {str(e)}")
            raise
    
    @staticmethod
    def safe_float_conversion(value: Any, default: float = 0.0) -> float:
        """
        Safely convert value to float
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value
        """
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, Decimal):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                cleaned = value.replace(',', '').replace(' ', '').strip()
                cleaned = cleaned.replace('$', '').replace('€', '')
                cleaned = cleaned.replace('%', '')
                
                # Remove trailing comma
                cleaned = cleaned.rstrip(',')
                
                if cleaned:
                    return float(cleaned)
            
            return default
            
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def parse_json_safely(json_string: str, default: Any = None) -> Any:
        """
        Safely parse JSON string
        
        Args:
            json_string: JSON string to parse
            default: Default value if parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            if not json_string:
                return default
            
            # Try to fix common JSON issues
            # Replace single quotes with double quotes
            json_string = json_string.replace("'", '"')
            
            # Fix trailing commas
            json_string = re.sub(r',\s*}', '}', json_string)
            json_string = re.sub(r',\s*]', ']', json_string)
            
            return json.loads(json_string)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {str(e)}")
            return default
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {str(e)}")
            return default
    
    @staticmethod
    def extract_numeric_values(text: str) -> List[float]:
        """
        Extract all numeric values from text
        
        Args:
            text: Text containing numbers
            
        Returns:
            List of float values
        """
        try:
            # Pattern to match numbers (including decimals and negatives)
            pattern = re.compile(r'-?\d+\.?\d*')
            matches = pattern.findall(text)
            
            numbers = []
            for match in matches:
                try:
                    num = float(match)
                    numbers.append(num)
                except ValueError:
                    continue
            
            return numbers
            
        except Exception as e:
            logger.error(f"Error extracting numbers: {str(e)}")
            return []