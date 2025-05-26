# services/statistical_service.py
import base64
import math
import re
import statistics
from io import BytesIO

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import kstest, norm, expon, lognorm, gaussian_kde
from scipy.optimize import minimize

from django.shortcuts import get_object_or_404

from questionary.models import Answer
from ..models import ProbabilisticDensityFunction

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')


class StatisticalService:
    """Service for handling statistical analysis and probability distributions"""
    
    def analyze_demand_history(self, questionary_result_id, user):
        """Analyze demand history and find best probability distribution"""
        # Get demand history from questionary answers
        demand_history = Answer.objects.filter(
            fk_question__question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=questionary_result_id
        ).first()
        
        if not demand_history:
            raise ValueError("No demand history found")
        
        # Parse demand history data
        numbers = self._parse_demand_data(demand_history.answer)
        
        # Calculate basic statistics
        demand_mean = np.mean(numbers)
        mean, std_dev = norm.fit(numbers)
        
        # Smooth data with KDE
        kde = gaussian_kde(numbers)
        smoothed_data = kde(numbers)
        
        # Optimize PDF parameters
        optimized_mean, optimized_std_dev = self._optimize_pdf_parameters(
            numbers, smoothed_data, mean, std_dev
        )
        
        # Find best distribution using Kolmogorov-Smirnov test
        best_distribution, best_ks_statistic, best_ks_p_value = self._find_best_distribution(
            numbers, optimized_mean, optimized_std_dev, user
        )
        
        # Generate PDF for visualization
        pdf = self._generate_pdf(numbers, best_distribution)
        distribution_label = best_distribution.get_distribution_type_display()
        
        # Create visualizations
        scatter_image = self._plot_scatter_and_pdf(numbers, pdf, distribution_label)
        histogram_image = self._plot_histogram_and_pdf(numbers, pdf, distribution_label)
        
        # Process data for template
        data_str = re.sub(r'<br\s*/?>', '\n', demand_history.answer)
        data_str = data_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "")
        data_list = [float(value) for value in data_str.split()]
        
        # Floor the statistical values for display
        best_ks_p_value_floor = math.floor(best_ks_p_value * 100) / 100
        best_ks_statistic_floor = math.floor(best_ks_statistic * 100) / 100
        
        return {
            'scatter_image': scatter_image,
            'histogram_image': histogram_image,
            'best_distribution': best_distribution,
            'demand_mean': demand_mean,
            'data_list': data_list,
            'best_ks_p_value_floor': best_ks_p_value_floor,
            'best_ks_statistic_floor': best_ks_statistic_floor,
        }
    
    def _parse_demand_data(self, demand_answer):
        """Parse demand data from answer string"""
        # Clean the string and convert to numbers
        cadena_numerica = demand_answer.strip('[]')
        subcadenas = cadena_numerica.split()
        numbers = np.array([float(subcadena) for subcadena in subcadenas])
        return numbers
    
    def _optimize_pdf_parameters(self, numbers, smoothed_data, initial_mean, initial_std_dev):
        """Optimize PDF parameters using smooth data fitting"""
        def loss_function(parameters):
            theoretical_pdf = norm.pdf(smoothed_data, loc=parameters[0], scale=parameters[1])
            loss = np.sum((smoothed_data - theoretical_pdf)**2)
            return loss
        
        initial_parameters = [initial_mean, initial_std_dev]
        result = minimize(loss_function, initial_parameters, method='L-BFGS-B')
        
        return result.x[0], result.x[1]  # optimized_mean, optimized_std_dev
    
    def _find_best_distribution(self, numbers, optimized_mean, optimized_std_dev, user):
        """Find the best fitting probability distribution using Kolmogorov-Smirnov test"""
        distributions = ProbabilisticDensityFunction.objects.filter(
            is_active=True, 
            fk_business__fk_user=user
        ).order_by('-id')
        
        demand_mean = statistics.mean(numbers)
        demand_mean_array = np.array([demand_mean])
        
        # Initialize variables for tracking best fit
        best_distribution = None
        best_ks_statistic = float('inf')
        best_ks_p_value = 0.0
        
        # Test each distribution
        for distribution in distributions:
            theoretical_distribution = self._create_theoretical_distribution(
                distribution, optimized_mean, optimized_std_dev
            )
            
            if theoretical_distribution is None:
                continue
            
            # Perform Kolmogorov-Smirnov test
            ks_statistic, ks_p_value = kstest(demand_mean_array, theoretical_distribution.cdf)
            
            # Update best fit if p-value is higher
            if ks_p_value > best_ks_p_value:
                best_ks_statistic = ks_statistic
                best_ks_p_value = ks_p_value
                best_distribution = distribution
        
        return best_distribution, best_ks_statistic, best_ks_p_value
    
    def _create_theoretical_distribution(self, distribution, optimized_mean, optimized_std_dev):
        """Create theoretical distribution object based on distribution type"""
        if distribution.distribution_type == 1:  # Normal distribution
            return norm(loc=optimized_mean, scale=optimized_std_dev)
        elif distribution.distribution_type == 2:  # Exponential distribution
            return expon(scale=1/distribution.lambda_param)
        elif distribution.distribution_type == 3:  # Log-Normal distribution
            return lognorm(s=optimized_std_dev, scale=np.exp(optimized_mean))
        else:
            return None
    
    def _generate_pdf(self, data, best_distribution):
        """Generate PDF values for the best distribution"""
        if not best_distribution:
            return None
        
        distribution_type = best_distribution.get_distribution_type_display()
        
        if distribution_type == "Normal":
            mean = best_distribution.mean_param
            std_dev = best_distribution.std_dev_param
            if std_dev is not None:
                return norm.pdf(data, loc=mean, scale=std_dev)
            else:
                return np.zeros_like(data)
        
        elif distribution_type == "Exponential":
            lambda_param = best_distribution.lambda_param
            return expon.pdf(data, scale=1 / lambda_param)
        
        elif distribution_type == "Log-Norm":
            s = best_distribution.std_dev_param
            scale = np.exp(best_distribution.mean_param)
            return lognorm.pdf(data, s=s, scale=scale)
        
        return None
    
    def _plot_scatter_and_pdf(self, data, pdf, distribution_label, confidence_interval=0.95):
        """Create scatter plot of demand history"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Scatter plot with swapped x and y axes
        ax.scatter(
            np.arange(1, len(data) + 1), 
            data, 
            alpha=0.5, 
            label='Demanda Historica', 
            marker='o', 
            edgecolor='none'
        )
        
        # Configure plot
        ax.legend()
        ax.set_xlabel('Número de datos')
        ax.set_ylabel('Demanda [Litros]')
        ax.set_title('Demanda historica')
        plt.grid(True)
        
        # Save plot to base64
        return self._save_plot_as_base64(fig)
    
    def _plot_histogram_and_pdf(self, data, pdf, distribution_label):
        """Create histogram with PDF overlay"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Histogram
        ax.hist(
            data, 
            bins=20, 
            density=True, 
            alpha=0.5, 
            label='Demanda Historica', 
            edgecolor='none'
        )
        
        # Plot PDF if available
        if pdf is not None:
            ax.plot(
                data, 
                pdf, 
                label=f'Función de densidad de probabilidad ({distribution_label})'
            )
        
        # Configure plot
        ax.legend()
        ax.set_xlabel('Demanda [Litros]')
        ax.set_ylabel('Densidad de probabilidad')
        ax.set_title('Demanda historica VS Funcion de Densidad de Probabilidad (FDP)')
        
        # Save plot to base64
        return self._save_plot_as_base64(fig)
    
    def _save_plot_as_base64(self, fig):
        """Save matplotlib figure as base64 encoded string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        plt.close(fig)
        
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_data
    
    def calculate_correlation_matrix(self, variables_data):
        """Calculate correlation matrix for variables"""
        # Convert variables data to numpy array
        data_matrix = np.array([list(var_data.values()) for var_data in variables_data])
        
        # Calculate correlation matrix
        correlation_matrix = np.corrcoef(data_matrix)
        
        return correlation_matrix
    
    def perform_regression_analysis(self, x_data, y_data, degree=1):
        """Perform polynomial regression analysis"""
        # Fit polynomial
        coefficients = np.polyfit(x_data, y_data, degree)
        polynomial = np.poly1d(coefficients)
        
        # Calculate R-squared
        y_pred = polynomial(x_data)
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return {
            'coefficients': coefficients,
            'polynomial': polynomial,
            'r_squared': r_squared,
            'predictions': y_pred
        }
    
    def calculate_confidence_intervals(self, data, confidence_level=0.95):
        """Calculate confidence intervals for data"""
        n = len(data)
        mean = np.mean(data)
        std_err = stats.sem(data)
        
        # Calculate confidence interval
        h = std_err * stats.t.ppf((1 + confidence_level) / 2., n-1)
        
        return {
            'mean': mean,
            'lower_bound': mean - h,
            'upper_bound': mean + h,
            'margin_of_error': h
        }
    
    def detect_outliers(self, data, method='iqr'):
        """Detect outliers in data using various methods"""
        if method == 'iqr':
            Q1 = np.percentile(data, 25)
            Q3 = np.percentile(data, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data))
            threshold = 3
            outliers = data[z_scores > threshold]
            
        else:
            raise ValueError("Method must be 'iqr' or 'zscore'")
        
        return {
            'outliers': outliers,
            'outlier_indices': np.where((data < lower_bound) | (data > upper_bound))[0] if method == 'iqr' else np.where(z_scores > threshold)[0],
            'clean_data': data[~((data < lower_bound) | (data > upper_bound))] if method == 'iqr' else data[z_scores <= threshold]
        }