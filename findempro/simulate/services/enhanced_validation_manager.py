# services/enhanced_validation_manager.py
"""
Gestor mejorado de validación para simulaciones.
Centraliza todos los tipos de validación y análisis de confiabilidad.
"""
import logging
from typing import Dict, List, Any, Optional
import numpy as np
try:
    from scipy import stats
    import scipy.stats
except ImportError:
    raise ImportError("scipy es requerido para el análisis estadístico. Instalar con: pip install scipy")

from ..models import Simulation, ResultSimulation
from .validation_service import SimulationValidationService

logger = logging.getLogger(__name__)


class EnhancedValidationManager:
    """Gestor avanzado de validación con múltiples tipos de análisis"""
    
    def __init__(self):
        self.validation_service = SimulationValidationService()
    
    def perform_comprehensive_validation(self, simulation_id: int, simulation_instance: Simulation,
                                       results_simulation: List[ResultSimulation],
                                       historical_demand: List[float],
                                       all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Realiza validación comprehensiva de la simulación
        """
        try:
            logger.info(f"Starting comprehensive validation for simulation {simulation_id}")
            
            validation_results = {
                'basic_validation': {},
                'model_validation': {},
                'prediction_validation': {},
                'statistical_validation': {},
                'distribution_validation': {},
                'ks_validation': {},
                'temporal_validation': {},
                'reliability_assessment': {},
                'validation_summary': {},
                'alerts_grouped': {},
                'confidence_metrics': {}
            }
            
            # 1. Validación básica del modelo
            validation_results['basic_validation'] = self._perform_basic_validation(simulation_id)
            
            # 2. Validación de variables del modelo
            if all_variables_extracted:
                validation_results['model_validation'] = self._perform_model_validation(
                    simulation_instance, results_simulation, all_variables_extracted
                )
            
            # 3. Validación de predicciones
            if historical_demand:
                validation_results['prediction_validation'] = self._perform_prediction_validation(
                    simulation_instance, results_simulation, historical_demand
                )
            
            # 4. Validación estadística avanzada
            validation_results['statistical_validation'] = self._perform_statistical_validation(
                historical_demand, results_simulation, all_variables_extracted
            )
            
            # 5. Validación de distribuciones (Kolmogorov-Smirnov)
            validation_results['ks_validation'] = self._perform_ks_validation(
                simulation_instance, results_simulation, all_variables_extracted
            )
            
            # 6. Validación temporal y consistencia
            validation_results['temporal_validation'] = self._perform_temporal_validation(
                results_simulation, historical_demand
            )
            
            # 7. Evaluación de confiabilidad
            validation_results['reliability_assessment'] = self._assess_reliability(
                validation_results, historical_demand, results_simulation
            )
            
            # 8. Generar resumen consolidado
            validation_results['validation_summary'] = self._generate_validation_summary(
                validation_results
            )
            
            # 9. Agrupar alertas por tipo y severidad
            validation_results['alerts_grouped'] = self._group_validation_alerts(
                validation_results
            )
            
            # 10. Métricas de confianza
            validation_results['confidence_metrics'] = self._calculate_confidence_metrics(
                validation_results, historical_demand, results_simulation
            )
            
            logger.info("Comprehensive validation completed successfully")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {str(e)}")
            return self._get_error_validation_results(simulation_id, str(e))
    
    def _perform_basic_validation(self, simulation_id: int) -> Dict[str, Any]:
        """Realiza validación básica usando el servicio existente"""
        try:
            return self.validation_service.validate_simulation(simulation_id)
        except Exception as e:
            logger.error(f"Error in basic validation: {e}")
            return {'alerts': [], 'is_valid': False, 'summary': {}}
    
    def _perform_model_validation(self, simulation_instance: Simulation,
                                results_simulation: List[ResultSimulation],
                                all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Realiza validación de variables del modelo"""
        try:
            return self.validation_service._validate_model_variables(
                simulation_instance, results_simulation, all_variables_extracted
            )
        except Exception as e:
            logger.error(f"Error in model validation: {e}")
            return {
                'summary': {'success_rate': 0.0, 'is_valid': False},
                'by_variable': {},
                'daily_details': []
            }
    
    def _perform_prediction_validation(self, simulation_instance: Simulation,
                                     results_simulation: List[ResultSimulation],
                                     historical_demand: List[float]) -> Dict[str, Any]:
        """Realiza validación de predicciones del modelo"""
        try:
            return self.validation_service._validate_model_predictions(
                simulation_instance, results_simulation, historical_demand
            )
        except Exception as e:
            logger.error(f"Error in prediction validation: {e}")
            return {
                'summary': {'success_rate': 0.0, 'avg_mape': 100.0},
                'details': {},
                'metrics': {},
                'alerts': []
            }
    
    def _perform_statistical_validation(self, historical_demand: List[float],
                                      results_simulation: List[ResultSimulation],
                                      all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Realiza validación estadística avanzada"""
        try:
            statistical_validation = {
                'normality_tests': {},
                'distribution_tests': {},
                'correlation_tests': {},
                'trend_tests': {},
                'autocorrelation_tests': {},
                'heteroscedasticity_tests': {},
                'summary': {}
            }
            
            # Extraer demandas simuladas
            simulated_demands = [float(r.demand_mean) for r in results_simulation if hasattr(r, 'demand_mean')]
            
            if simulated_demands:
                # Pruebas de normalidad
                statistical_validation['normality_tests'] = self._test_normality(simulated_demands)
                
                # Pruebas de autocorrelación
                if len(simulated_demands) > 10:
                    statistical_validation['autocorrelation_tests'] = self._test_autocorrelation(simulated_demands)
                
                # Comparación con datos históricos
                if historical_demand:
                    statistical_validation['distribution_tests'] = self._test_distributions_comparison(
                        historical_demand, simulated_demands
                    )
                    
                    statistical_validation['correlation_tests'] = self._test_correlation(
                        historical_demand, simulated_demands
                    )
                
                # Análisis de tendencias
                statistical_validation['trend_tests'] = self._test_trends(simulated_demands)
                
                # Pruebas de heterocedasticidad
                if len(simulated_demands) > 20:
                    statistical_validation['heteroscedasticity_tests'] = self._test_heteroscedasticity(simulated_demands)
            
            # Generar resumen
            statistical_validation['summary'] = self._summarize_statistical_tests(statistical_validation)
            
            return statistical_validation
            
        except Exception as e:
            logger.error(f"Error in statistical validation: {e}")
            return {'summary': {'overall_validity': False, 'issues_found': []}}
    
    def _perform_ks_validation(self, simulation_instance: Simulation,
                             results_simulation: List[ResultSimulation],
                             all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Realiza validación Kolmogorov-Smirnov específica"""
        try:
            return self.validation_service.validate_distribution_consistency(
                simulation_instance, results_simulation, distribution_params=None
            )
        except Exception as e:
            logger.error(f"Error in KS validation: {e}")
            return {
                'summary': {'total_tests': 0, 'passed_tests': 0, 'overall_validity': False},
                'ks_tests': {},
                'confidence_intervals': {},
                'reliability_report': {},
                'distribution_analysis': {}
            }
    
    def _perform_temporal_validation(self, results_simulation: List[ResultSimulation],
                                   historical_demand: List[float]) -> Dict[str, Any]:
        """Realiza validación de consistencia temporal"""
        try:
            temporal_validation = {
                'trend_consistency': {},
                'seasonal_patterns': {},
                'volatility_analysis': {},
                'regime_changes': {},
                'summary': {}
            }
            
            simulated_demands = [float(r.demand_mean) for r in results_simulation if hasattr(r, 'demand_mean')]
            
            if simulated_demands:
                # Análisis de tendencias temporales
                temporal_validation['trend_consistency'] = self._analyze_trend_consistency(
                    simulated_demands, historical_demand
                )
                
                # Detección de patrones estacionales
                if len(simulated_demands) >= 30:
                    temporal_validation['seasonal_patterns'] = self._detect_seasonal_patterns(simulated_demands)
                
                # Análisis de volatilidad
                temporal_validation['volatility_analysis'] = self._analyze_volatility(
                    simulated_demands, historical_demand
                )
                
                # Detección de cambios de régimen
                if len(simulated_demands) >= 50:
                    temporal_validation['regime_changes'] = self._detect_regime_changes(simulated_demands)
                
                # Resumen temporal
                temporal_validation['summary'] = self._summarize_temporal_analysis(temporal_validation)
            
            return temporal_validation
            
        except Exception as e:
            logger.error(f"Error in temporal validation: {e}")
            return {'summary': {'temporal_consistency': False, 'issues': []}}
    
    def _assess_reliability(self, validation_results: Dict[str, Any],
                          historical_demand: List[float],
                          results_simulation: List[ResultSimulation]) -> Dict[str, Any]:
        """Evalúa la confiabilidad general del modelo"""
        try:
            reliability_assessment = {
                'reliability_score': 0.0,
                'certification_status': 'NOT_CERTIFIED',
                'reliability_level': 'Bajo',
                'component_analysis': {},
                'risk_assessment': {},
                'recommendations': [],
                'confidence_level': 0.0
            }
            
            # Calcular score de confiabilidad basado en múltiples validaciones
            reliability_score = self._calculate_reliability_score(validation_results)
            reliability_assessment['reliability_score'] = reliability_score
            
            # Determinar estado de certificación
            if reliability_score >= 90:
                reliability_assessment['certification_status'] = 'CERTIFIED'
                reliability_assessment['reliability_level'] = 'Muy Alto'
            elif reliability_score >= 75:
                reliability_assessment['certification_status'] = 'CONDITIONAL'
                reliability_assessment['reliability_level'] = 'Alto'
            elif reliability_score >= 60:
                reliability_assessment['reliability_level'] = 'Medio'
            else:
                reliability_assessment['reliability_level'] = 'Bajo'
            
            # Análisis por componentes
            reliability_assessment['component_analysis'] = self._analyze_reliability_components(
                validation_results
            )
            
            # Evaluación de riesgos
            reliability_assessment['risk_assessment'] = self._assess_model_risks(
                validation_results, historical_demand, results_simulation
            )
            
            # Generar recomendaciones
            reliability_assessment['recommendations'] = self._generate_reliability_recommendations(
                reliability_assessment, validation_results
            )
            
            # Nivel de confianza estadística
            reliability_assessment['confidence_level'] = self._calculate_statistical_confidence(
                validation_results
            )
            
            return reliability_assessment
            
        except Exception as e:
            logger.error(f"Error assessing reliability: {e}")
            return {
                'reliability_score': 0.0,
                'certification_status': 'NOT_CERTIFIED',
                'reliability_level': 'Desconocido',
                'recommendations': ['Error en evaluación de confiabilidad']
            }
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera resumen consolidado de todas las validaciones"""
        try:
            summary = {
                'overall_validity': False,
                'total_tests_performed': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'critical_issues': [],
                'warnings': [],
                'strengths': [],
                'areas_for_improvement': [],
                'overall_score': 0.0,
                'validation_categories': {}
            }
            
            # Contar tests por categoría
            categories = ['basic_validation', 'model_validation', 'prediction_validation', 
                         'statistical_validation', 'ks_validation', 'temporal_validation']
            
            for category in categories:
                category_data = validation_results.get(category, {})
                category_summary = self._summarize_category(category, category_data)
                summary['validation_categories'][category] = category_summary
                
                summary['total_tests_performed'] += category_summary.get('tests_performed', 0)
                summary['tests_passed'] += category_summary.get('tests_passed', 0)
                summary['tests_failed'] += category_summary.get('tests_failed', 0)
            
            # Calcular score general
            if summary['total_tests_performed'] > 0:
                summary['overall_score'] = (summary['tests_passed'] / summary['total_tests_performed']) * 100
                summary['overall_validity'] = summary['overall_score'] >= 70
            
            # Identificar fortalezas y áreas de mejora
            summary['strengths'], summary['areas_for_improvement'] = self._identify_strengths_and_improvements(
                validation_results
            )
            
            # Recopilar issues críticos y warnings
            summary['critical_issues'], summary['warnings'] = self._collect_critical_issues_and_warnings(
                validation_results
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating validation summary: {e}")
            return {
                'overall_validity': False,
                'overall_score': 0.0,
                'critical_issues': [f'Error en resumen: {str(e)}']
            }
    
    def _group_validation_alerts(self, validation_results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa alertas de validación por tipo y severidad"""
        try:
            alerts_grouped = {
                'CRITICAL': [],
                'ERROR': [],
                'WARNING': [],
                'INFO': [],
                'SUCCESS': []
            }
            
            # Recopilar alertas de todas las validaciones
            for validation_type, validation_data in validation_results.items():
                if isinstance(validation_data, dict) and 'alerts' in validation_data:
                    for alert in validation_data['alerts']:
                        severity = alert.get('severity', 'INFO').upper()
                        alert_type = alert.get('type', 'INFO').upper()
                        
                        # Determinar categoría final
                        final_category = self._determine_alert_category(severity, alert_type)
                        
                        alert_info = {
                            'message': alert.get('message', 'Alert message'),
                            'details': alert.get('details', ''),
                            'source': validation_type,
                            'severity': severity,
                            'type': alert_type,
                            'recommendation': alert.get('recommendation', ''),
                            'category': alert.get('category', 'General')
                        }
                        
                        alerts_grouped[final_category].append(alert_info)
            
            # Ordenar alertas por severidad dentro de cada categoría
            for category in alerts_grouped:
                alerts_grouped[category].sort(
                    key=lambda x: self._get_alert_priority(x.get('severity', 'INFO'))
                )
            
            return alerts_grouped
            
        except Exception as e:
            logger.error(f"Error grouping validation alerts: {e}")
            return {'ERROR': [{'message': f'Error agrupando alertas: {str(e)}', 'severity': 'ERROR'}]}
    
    def _calculate_confidence_metrics(self, validation_results: Dict[str, Any],
                                    historical_demand: List[float],
                                    results_simulation: List[ResultSimulation]) -> Dict[str, Any]:
        """Calcula métricas de confianza del modelo"""
        try:
            confidence_metrics = {
                'prediction_confidence': 0.0,
                'model_stability': 0.0,
                'data_quality_score': 0.0,
                'statistical_significance': 0.0,
                'overall_confidence': 0.0,
                'confidence_intervals': {},
                'uncertainty_bounds': {},
                'risk_metrics': {}
            }
            
            # Confianza en predicciones
            if historical_demand and results_simulation:
                confidence_metrics['prediction_confidence'] = self._calculate_prediction_confidence(
                    historical_demand, results_simulation
                )
            
            # Estabilidad del modelo
            confidence_metrics['model_stability'] = self._calculate_model_stability(validation_results)
            
            # Calidad de datos
            confidence_metrics['data_quality_score'] = self._calculate_data_quality_score(
                historical_demand, results_simulation
            )
            
            # Significancia estadística
            statistical_validation = validation_results.get('statistical_validation', {})
            confidence_metrics['statistical_significance'] = self._calculate_statistical_significance(
                statistical_validation
            )
            
            # Intervalos de confianza
            if historical_demand:
                confidence_metrics['confidence_intervals'] = self._calculate_prediction_intervals(
                    historical_demand, results_simulation
                )
            
            # Métricas de riesgo
            confidence_metrics['risk_metrics'] = self._calculate_risk_metrics(
                validation_results, results_simulation
            )
            
            # Confianza general
            confidence_metrics['overall_confidence'] = np.mean([
                confidence_metrics['prediction_confidence'],
                confidence_metrics['model_stability'],
                confidence_metrics['data_quality_score'],
                confidence_metrics['statistical_significance']
            ])
            
            return confidence_metrics
            
        except Exception as e:
            logger.error(f"Error calculating confidence metrics: {e}")
            return {
                'overall_confidence': 0.0,
                'prediction_confidence': 0.0,
                'model_stability': 0.0,
                'data_quality_score': 0.0
            }
    
    # Métodos helper para validaciones específicas
    
    def _test_normality(self, data: List[float]) -> Dict[str, Any]:
        """Pruebas de normalidad"""
        try:
            normality_tests = {}
            
            if len(data) <= 5000:
                # Shapiro-Wilk test
                stat, p_value = scipy.stats.shapiro(data)
                normality_tests['shapiro_wilk'] = {
                    'statistic': float(stat),
                    'p_value': float(p_value),
                    'is_normal': p_value > 0.05,
                    'interpretation': 'Normal' if p_value > 0.05 else 'No normal'
                }
            
            # Kolmogorov-Smirnov test contra distribución normal
            mean, std = np.mean(data), np.std(data)
            ks_stat, ks_p = scipy.stats.kstest(data, lambda x: scipy.stats.norm.cdf(x, mean, std))
            normality_tests['kolmogorov_smirnov'] = {
                'statistic': float(ks_stat),
                'p_value': float(ks_p),
                'is_normal': ks_p > 0.05,
                'interpretation': 'Normal' if ks_p > 0.05 else 'No normal'
            }
            
            # D'Agostino's normality test
            try:
                dag_stat, dag_p = scipy.stats.normaltest(data)
                normality_tests['dagostino'] = {
                    'statistic': float(dag_stat),
                    'p_value': float(dag_p),
                    'is_normal': dag_p > 0.05,
                    'interpretation': 'Normal' if dag_p > 0.05 else 'No normal'
                }
            except:
                pass
            
            return normality_tests
            
        except Exception as e:
            logger.error(f"Error testing normality: {e}")
            return {}
    
    def _test_autocorrelation(self, data: List[float]) -> Dict[str, Any]:
        """Pruebas de autocorrelación"""
        try:
            autocorr_tests = {
                'ljung_box': {},
                'durbin_watson': {},
                'autocorrelation_function': []
            }
            
            # Ljung-Box test
            try:
                from statsmodels.stats.diagnostic import acorr_ljungbox
                lb_result = acorr_ljungbox(data, lags=min(10, len(data)//4), return_df=True)
                autocorr_tests['ljung_box'] = {
                    'statistics': lb_result['lb_stat'].tolist(),
                    'p_values': lb_result['lb_pvalue'].tolist(),
                    'has_autocorr': any(lb_result['lb_pvalue'] < 0.05)
                }
            except ImportError:
                # Fallback simple
                autocorr_tests['ljung_box'] = {'has_autocorr': False}
            
            # Función de autocorrelación simple
            max_lag = min(20, len(data)//4)
            for lag in range(1, max_lag + 1):
                if len(data) > lag:
                    corr = np.corrcoef(data[:-lag], data[lag:])[0, 1]
                    autocorr_tests['autocorrelation_function'].append({
                        'lag': lag,
                        'correlation': float(corr) if not np.isnan(corr) else 0.0
                    })
            
            return autocorr_tests
            
        except Exception as e:
            logger.error(f"Error testing autocorrelation: {e}")
            return {}
    
    def _test_distributions_comparison(self, hist_data: List[float], 
                                     sim_data: List[float]) -> Dict[str, Any]:
        """Comparación de distribuciones"""
        try:
            comparison_tests = {}
            
            min_len = min(len(hist_data), len(sim_data))
            hist_sample = hist_data[:min_len]
            sim_sample = sim_data[:min_len]
            
            # Kolmogorov-Smirnov de dos muestras
            ks_stat, ks_p = scipy.stats.ks_2samp(hist_sample, sim_sample)
            comparison_tests['kolmogorov_smirnov_2samp'] = {
                'statistic': float(ks_stat),
                'p_value': float(ks_p),
                'distributions_similar': ks_p > 0.05,
                'interpretation': 'Similares' if ks_p > 0.05 else 'Diferentes'
            }
            
            # Mann-Whitney U test
            try:
                mw_stat, mw_p = scipy.stats.mannwhitneyu(hist_sample, sim_sample, alternative='two-sided')
                comparison_tests['mann_whitney'] = {
                    'statistic': float(mw_stat),
                    'p_value': float(mw_p),
                    'medians_similar': mw_p > 0.05,
                    'interpretation': 'Medianas similares' if mw_p > 0.05 else 'Medianas diferentes'
                }
            except Exception:
                pass
            
            # Anderson-Darling test
            try:
                combined_data = np.concatenate([hist_sample, sim_sample])
                labels = [0] * len(hist_sample) + [1] * len(sim_sample)
                # Implementación simplificada
                comparison_tests['anderson_darling'] = {
                    'note': 'Test no implementado completamente'
                }
            except Exception:
                pass
            
            return comparison_tests
            
        except Exception as e:
            logger.error(f"Error comparing distributions: {e}")
            return {}
    
    def _test_correlation(self, hist_data: List[float], sim_data: List[float]) -> Dict[str, Any]:
        """Pruebas de correlación"""
        try:
            correlation_tests = {}
            
            min_len = min(len(hist_data), len(sim_data))
            hist_sample = hist_data[:min_len]
            sim_sample = sim_data[:min_len]
            
            # Correlación de Pearson
            pearson_r, pearson_p = scipy.stats.pearsonr(hist_sample, sim_sample)
            correlation_tests['pearson'] = {
                'correlation': float(pearson_r),
                'p_value': float(pearson_p),
                'is_significant': pearson_p < 0.05,
                'strength': self._interpret_correlation_strength(pearson_r)
            }
            
            # Correlación de Spearman
            spearman_r, spearman_p = scipy.stats.spearmanr(hist_sample, sim_sample)
            correlation_tests['spearman'] = {
                'correlation': float(spearman_r),
                'p_value': float(spearman_p),
                'is_significant': spearman_p < 0.05,
                'strength': self._interpret_correlation_strength(spearman_r)
            }
            
            return correlation_tests
            
        except Exception as e:
            logger.error(f"Error testing correlation: {e}")
            return {}
    
    def _test_trends(self, data: List[float]) -> Dict[str, Any]:
        """Pruebas de tendencias"""
        try:
            trend_tests = {}
            
            if len(data) >= 3:
                # Regresión lineal para tendencia
                x = np.arange(len(data))
                slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, data)
                
                trend_tests['linear_trend'] = {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'has_trend': p_value < 0.05,
                    'trend_direction': 'Creciente' if slope > 0 else 'Decreciente' if slope < 0 else 'Estable'
                }
                
                # Mann-Kendall test para tendencia
                try:
                    tau, tau_p = scipy.stats.kendalltau(x, data)
                    trend_tests['mann_kendall'] = {
                        'tau': float(tau),
                        'p_value': float(tau_p),
                        'has_trend': tau_p < 0.05,
                        'trend_direction': 'Creciente' if tau > 0 else 'Decreciente' if tau < 0 else 'Estable'
                    }
                except Exception:
                    pass
            
            return trend_tests
            
        except Exception as e:
            logger.error(f"Error testing trends: {e}")
            return {}
    
    def _test_heteroscedasticity(self, data: List[float]) -> Dict[str, Any]:
        """Pruebas de heterocedasticidad"""
        try:
            # Implementación simplificada
            # Dividir datos en grupos y comparar varianzas
            n = len(data)
            group_size = n // 3
            
            if group_size >= 5:
                group1 = data[:group_size]
                group2 = data[group_size:2*group_size]
                group3 = data[2*group_size:]
                
                var1, var2, var3 = np.var(group1), np.var(group2), np.var(group3)
                
                # Test F simple entre grupos
                f_stat = max(var1, var2, var3) / min(var1, var2, var3)
                
                return {
                    'variance_groups': [float(var1), float(var2), float(var3)],
                    'f_statistic': float(f_stat),
                    'has_heteroscedasticity': f_stat > 2.0,  # Threshold simple
                    'interpretation': 'Varianza heterogénea' if f_stat > 2.0 else 'Varianza homogénea'
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error testing heteroscedasticity: {e}")
            return {}
    
    # Métodos helper adicionales
    
    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpreta la fuerza de correlación"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.9:
            return 'Muy fuerte'
        elif abs_corr >= 0.7:
            return 'Fuerte'
        elif abs_corr >= 0.5:
            return 'Moderada'
        elif abs_corr >= 0.3:
            return 'Débil'
        else:
            return 'Muy débil'
    
    def _summarize_statistical_tests(self, statistical_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Resume las pruebas estadísticas"""
        try:
            summary = {
                'overall_validity': True,
                'issues_found': [],
                'passed_tests': 0,
                'total_tests': 0
            }
            
            # Revisar cada categoría de tests
            for test_category, tests in statistical_validation.items():
                if test_category == 'summary':
                    continue
                
                if isinstance(tests, dict):
                    for test_name, test_result in tests.items():
                        summary['total_tests'] += 1
                        
                        # Evaluar si el test pasó (lógica específica por tipo)
                        if self._evaluate_test_result(test_category, test_name, test_result):
                            summary['passed_tests'] += 1
                        else:
                            summary['issues_found'].append(f"{test_category}.{test_name}")
            
            # Determinar validez general
            if summary['total_tests'] > 0:
                pass_rate = summary['passed_tests'] / summary['total_tests']
                summary['overall_validity'] = pass_rate >= 0.7
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing statistical tests: {e}")
            return {'overall_validity': False, 'issues_found': []}
    
    def _evaluate_test_result(self, test_category: str, test_name: str, test_result: Dict[str, Any]) -> bool:
        """Evalúa si un test específico pasó"""
        try:
            # Lógica específica por tipo de test
            if 'p_value' in test_result:
                if test_category == 'normality_tests':
                    return test_result.get('is_normal', False)
                elif test_category == 'distribution_tests':
                    return test_result.get('distributions_similar', False)
                elif test_category == 'correlation_tests':
                    return test_result.get('is_significant', False)
                else:
                    return test_result.get('p_value', 1.0) > 0.05
            
            # Para tests sin p-value
            if 'has_autocorr' in test_result:
                return not test_result['has_autocorr']  # No queremos autocorrelación
            
            if 'has_heteroscedasticity' in test_result:
                return not test_result['has_heteroscedasticity']  # No queremos heterocedasticidad
            
            return True  # Por defecto asumir que pasó
            
        except Exception as e:
            logger.error(f"Error evaluating test result: {e}")
            return False
    
    def _get_error_validation_results(self, simulation_id: int, error_msg: str) -> Dict[str, Any]:
        """Retorna resultados de error para validación"""
        return {
            'basic_validation': {'alerts': [{'type': 'ERROR', 'message': error_msg}], 'is_valid': False},
            'model_validation': {'summary': {'is_valid': False}},
            'prediction_validation': {'summary': {'success_rate': 0.0}},
            'statistical_validation': {'summary': {'overall_validity': False}},
            'ks_validation': {'summary': {'overall_validity': False}},
            'temporal_validation': {'summary': {'temporal_consistency': False}},
            'reliability_assessment': {'reliability_score': 0.0, 'certification_status': 'NOT_CERTIFIED'},
            'validation_summary': {'overall_validity': False, 'overall_score': 0.0},
            'alerts_grouped': {'ERROR': [{'message': error_msg, 'severity': 'ERROR'}]},
            'confidence_metrics': {'overall_confidence': 0.0}
        }
    
    # Métodos adicionales para análisis temporal y confiabilidad
    
    def _analyze_trend_consistency(self, simulated_data: List[float], 
                                 historical_data: Optional[List[float]]) -> Dict[str, Any]:
        """Analiza consistencia de tendencias"""
        try:
            trend_analysis = {
                'simulated_trend': {},
                'historical_trend': {},
                'consistency_score': 0.0,
                'trend_match': False
            }
            
            # Analizar tendencia simulada
            if len(simulated_data) >= 3:
                x = np.arange(len(simulated_data))
                slope, _, r_val, p_val, _ = scipy.stats.linregress(x, simulated_data)
                trend_analysis['simulated_trend'] = {
                    'slope': float(slope),
                    'r_squared': float(r_val ** 2),
                    'p_value': float(p_val),
                    'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
                }
            
            # Analizar tendencia histórica si está disponible
            if historical_data and len(historical_data) >= 3:
                x_hist = np.arange(len(historical_data))
                slope_hist, _, r_val_hist, p_val_hist, _ = scipy.stats.linregress(x_hist, historical_data)
                trend_analysis['historical_trend'] = {
                    'slope': float(slope_hist),
                    'r_squared': float(r_val_hist ** 2),
                    'p_value': float(p_val_hist),
                    'direction': 'increasing' if slope_hist > 0 else 'decreasing' if slope_hist < 0 else 'stable'
                }
                
                # Calcular consistencia
                if 'simulated_trend' in trend_analysis and trend_analysis['simulated_trend']:
                    sim_dir = trend_analysis['simulated_trend']['direction']
                    hist_dir = trend_analysis['historical_trend']['direction']
                    trend_analysis['trend_match'] = sim_dir == hist_dir
                    trend_analysis['consistency_score'] = 100.0 if sim_dir == hist_dir else 0.0
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trend consistency: {e}")
            return {'consistency_score': 0.0, 'trend_match': False}
    
    def _detect_seasonal_patterns(self, data: List[float]) -> Dict[str, Any]:
        """Detecta patrones estacionales simples"""
        try:
            seasonal_analysis = {
                'has_seasonality': False,
                'dominant_period': 0,
                'seasonal_strength': 0.0,
                'patterns_detected': []
            }
            
            # Buscar periodicidades comunes
            common_periods = [7, 30, 90, 365]  # Semanal, mensual, trimestral, anual
            
            best_autocorr = 0.0
            best_period = 0
            
            for period in common_periods:
                if len(data) > 2 * period:
                    # Calcular autocorrelación para este período
                    autocorr_values = []
                    for i in range(0, len(data) - period, period):
                        segment1 = data[i:i + period]
                        segment2 = data[i + period:i + 2 * period]
                        if len(segment1) == len(segment2) == period:
                            corr = np.corrcoef(segment1, segment2)[0, 1]
                            if not np.isnan(corr):
                                autocorr_values.append(abs(corr))
                    
                    if autocorr_values:
                        avg_autocorr = np.mean(autocorr_values)
                        if avg_autocorr > best_autocorr:
                            best_autocorr = avg_autocorr
                            best_period = period
                        
                        if avg_autocorr > 0.3:  # Threshold para detectar estacionalidad
                            seasonal_analysis['patterns_detected'].append({
                                'period': period,
                                'strength': float(avg_autocorr),
                                'description': self._describe_period(period)
                            })
            
            seasonal_analysis['has_seasonality'] = best_autocorr > 0.3
            seasonal_analysis['dominant_period'] = best_period
            seasonal_analysis['seasonal_strength'] = float(best_autocorr)
            
            return seasonal_analysis
            
        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")
            return {'has_seasonality': False, 'seasonal_strength': 0.0}
    
    def _describe_period(self, period: int) -> str:
        """Describe un período estacional"""
        descriptions = {
            7: 'Semanal',
            30: 'Mensual',
            90: 'Trimestral',
            365: 'Anual'
        }
        return descriptions.get(period, f'{period} días')
    
    def _analyze_volatility(self, simulated_data: List[float], 
                          historical_data: Optional[List[float]]) -> Dict[str, Any]:
        """Analiza volatilidad de los datos"""
        try:
            volatility_analysis = {
                'simulated_volatility': 0.0,
                'historical_volatility': 0.0,
                'volatility_ratio': 1.0,
                'volatility_match': False,
                'volatility_clusters': []
            }
            
            # Calcular volatilidad simulada
            if len(simulated_data) > 1:
                sim_std = np.std(simulated_data)
                sim_mean = np.mean(simulated_data)
                volatility_analysis['simulated_volatility'] = float(sim_std / sim_mean if sim_mean != 0 else 0)
            
            # Calcular volatilidad histórica
            if historical_data and len(historical_data) > 1:
                hist_std = np.std(historical_data)
                hist_mean = np.mean(historical_data)
                volatility_analysis['historical_volatility'] = float(hist_std / hist_mean if hist_mean != 0 else 0)
                
                # Ratio de volatilidades
                if volatility_analysis['historical_volatility'] != 0:
                    volatility_analysis['volatility_ratio'] = (
                        volatility_analysis['simulated_volatility'] / volatility_analysis['historical_volatility']
                    )
                    
                    # Considerar match si ratio está entre 0.8 y 1.2
                    volatility_analysis['volatility_match'] = 0.8 <= volatility_analysis['volatility_ratio'] <= 1.2
            
            # Detectar clusters de volatilidad
            volatility_analysis['volatility_clusters'] = self._detect_volatility_clusters(simulated_data)
            
            return volatility_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volatility: {e}")
            return {'simulated_volatility': 0.0, 'volatility_match': False}
    
    def _detect_volatility_clusters(self, data: List[float]) -> List[Dict[str, Any]]:
        """Detecta clusters de alta/baja volatilidad"""
        try:
            if len(data) < 20:
                return []
            
            # Calcular volatilidad rolling
            window_size = min(10, len(data) // 4)
            rolling_volatilities = []
            
            for i in range(len(data) - window_size + 1):
                window = data[i:i + window_size]
                vol = np.std(window)
                rolling_volatilities.append(vol)
            
            if not rolling_volatilities:
                return []
            
            # Identificar períodos de alta volatilidad
            vol_threshold = np.mean(rolling_volatilities) + np.std(rolling_volatilities)
            clusters = []
            
            high_vol_periods = [i for i, vol in enumerate(rolling_volatilities) if vol > vol_threshold]
            
            if high_vol_periods:
                # Agrupar períodos consecutivos
                current_cluster = [high_vol_periods[0]]
                
                for period in high_vol_periods[1:]:
                    if period - current_cluster[-1] <= 2:  # Períodos cercanos
                        current_cluster.append(period)
                    else:
                        if len(current_cluster) >= 3:  # Cluster significativo
                            clusters.append({
                                'start_period': current_cluster[0],
                                'end_period': current_cluster[-1],
                                'duration': len(current_cluster),
                                'avg_volatility': float(np.mean([rolling_volatilities[i] for i in current_cluster]))
                            })
                        current_cluster = [period]
                
                # Agregar último cluster si es significativo
                if len(current_cluster) >= 3:
                    clusters.append({
                        'start_period': current_cluster[0],
                        'end_period': current_cluster[-1],
                        'duration': len(current_cluster),
                        'avg_volatility': float(np.mean([rolling_volatilities[i] for i in current_cluster]))
                    })
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error detecting volatility clusters: {e}")
            return []
    
    def _detect_regime_changes(self, data: List[float]) -> Dict[str, Any]:
        """Detecta cambios de régimen en los datos"""
        try:
            regime_analysis = {
                'regime_changes_detected': [],
                'number_of_regimes': 1,
                'regime_stability': 1.0
            }
            
            if len(data) < 50:
                return regime_analysis
            
            # Implementación simplificada usando ventanas deslizantes
            window_size = len(data) // 10
            regime_changes = []
            
            for i in range(window_size, len(data) - window_size, window_size // 2):
                before_window = data[i - window_size:i]
                after_window = data[i:i + window_size]
                
                # Test t para comparar medias
                if len(before_window) > 5 and len(after_window) > 5:
                    t_stat, p_value = scipy.stats.ttest_ind(before_window, after_window)
                    
                    if p_value < 0.05:  # Cambio significativo
                        mean_before = np.mean(before_window)
                        mean_after = np.mean(after_window)
                        change_magnitude = abs(mean_after - mean_before) / mean_before if mean_before != 0 else 0
                        
                        if change_magnitude > 0.2:  # Cambio sustancial (>20%)
                            regime_changes.append({
                                'change_point': i,
                                'p_value': float(p_value),
                                'mean_before': float(mean_before),
                                'mean_after': float(mean_after),
                                'change_magnitude': float(change_magnitude),
                                'change_type': 'increase' if mean_after > mean_before else 'decrease'
                            })
            
            regime_analysis['regime_changes_detected'] = regime_changes
            regime_analysis['number_of_regimes'] = len(regime_changes) + 1
            regime_analysis['regime_stability'] = 1.0 / (1.0 + len(regime_changes) * 0.2)
            
            return regime_analysis
            
        except Exception as e:
            logger.error(f"Error detecting regime changes: {e}")
            return {'number_of_regimes': 1, 'regime_stability': 1.0}
    
    def _summarize_temporal_analysis(self, temporal_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Resume el análisis temporal"""
        try:
            summary = {
                'temporal_consistency': True,
                'issues': [],
                'strengths': [],
                'overall_score': 0.0
            }
            
            scores = []
            
            # Evaluar consistencia de tendencias
            trend_data = temporal_validation.get('trend_consistency', {})
            if trend_data.get('consistency_score', 0) >= 80:
                summary['strengths'].append('Tendencias consistentes con datos históricos')
                scores.append(trend_data['consistency_score'])
            elif trend_data.get('consistency_score', 0) < 50:
                summary['issues'].append('Tendencias inconsistentes con datos históricos')
                scores.append(trend_data.get('consistency_score', 0))
            
            # Evaluar estacionalidad
            seasonal_data = temporal_validation.get('seasonal_patterns', {})
            if seasonal_data.get('has_seasonality', False):
                if seasonal_data.get('seasonal_strength', 0) > 0.5:
                    summary['strengths'].append('Patrones estacionales bien definidos')
                    scores.append(80)
                else:
                    scores.append(60)
            else:
                scores.append(70)  # Neutral si no hay estacionalidad
            
            # Evaluar volatilidad
            volatility_data = temporal_validation.get('volatility_analysis', {})
            if volatility_data.get('volatility_match', False):
                summary['strengths'].append('Volatilidad consistente con datos históricos')
                scores.append(85)
            elif volatility_data.get('volatility_ratio', 1.0) > 2.0:
                summary['issues'].append('Volatilidad excesivamente alta')
                scores.append(30)
            else:
                scores.append(60)
            
            # Evaluar estabilidad de régimen
            regime_data = temporal_validation.get('regime_changes', {})
            regime_stability = regime_data.get('regime_stability', 1.0)
            if regime_stability > 0.8:
                summary['strengths'].append('Modelo temporalmente estable')
                scores.append(90)
            elif regime_stability < 0.5:
                summary['issues'].append('Múltiples cambios de régimen detectados')
                scores.append(40)
            else:
                scores.append(70)
            
            # Calcular score general
            if scores:
                summary['overall_score'] = float(np.mean(scores))
                summary['temporal_consistency'] = summary['overall_score'] >= 70
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing temporal analysis: {e}")
            return {'temporal_consistency': False, 'overall_score': 0.0}
    
    def _calculate_reliability_score(self, validation_results: Dict[str, Any]) -> float:
        """Calcula score de confiabilidad basado en todas las validaciones"""
        try:
            scores = []
            weights = []
            
            # Validación básica (peso 0.2)
            basic_val = validation_results.get('basic_validation', {})
            if basic_val.get('is_valid', False):
                scores.append(85)
            else:
                scores.append(30)
            weights.append(0.2)
            
            # Validación del modelo (peso 0.25)
            model_val = validation_results.get('model_validation', {})
            model_summary = model_val.get('summary', {})
            model_score = model_summary.get('success_rate', 0) * 100
            scores.append(model_score)
            weights.append(0.25)
            
            # Validación de predicciones (peso 0.25)
            pred_val = validation_results.get('prediction_validation', {})
            pred_summary = pred_val.get('summary', {})
            pred_accuracy = 100 - pred_summary.get('avg_mape', 100)
            scores.append(max(0, pred_accuracy))
            weights.append(0.25)
            
            # Validación estadística (peso 0.15)
            stat_val = validation_results.get('statistical_validation', {})
            stat_summary = stat_val.get('summary', {})
            if stat_summary.get('overall_validity', False):
                scores.append(80)
            else:
                scores.append(40)
            weights.append(0.15)
            
            # Validación temporal (peso 0.15)
            temp_val = validation_results.get('temporal_validation', {})
            temp_summary = temp_val.get('summary', {})
            temp_score = temp_summary.get('overall_score', 50)
            scores.append(temp_score)
            weights.append(0.15)
            
            # Calcular promedio ponderado
            if len(scores) == len(weights):
                reliability_score = sum(score * weight for score, weight in zip(scores, weights))
                return float(max(0, min(100, reliability_score)))
            
            return 50.0  # Score por defecto
            
        except Exception as e:
            logger.error(f"Error calculating reliability score: {e}")
            return 0.0
    
    def _analyze_reliability_components(self, validation_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analiza confiabilidad por componentes"""
        try:
            components = {
                'data_quality': self._assess_data_quality_component(validation_results),
                'model_accuracy': self._assess_model_accuracy_component(validation_results),
                'statistical_validity': self._assess_statistical_validity_component(validation_results),
                'temporal_consistency': self._assess_temporal_consistency_component(validation_results),
                'prediction_reliability': self._assess_prediction_reliability_component(validation_results)
            }
            
            return components
            
        except Exception as e:
            logger.error(f"Error analyzing reliability components: {e}")
            return {}
    
    def _assess_data_quality_component(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa componente de calidad de datos"""
        # Implementación simplificada
        return {
            'reliability': 'medium',
            'score': 70.0,
            'issues': [],
            'strengths': ['Datos disponibles para análisis']
        }
    
    def _assess_model_accuracy_component(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa componente de precisión del modelo"""
        model_val = validation_results.get('model_validation', {})
        model_summary = model_val.get('summary', {})
        success_rate = model_summary.get('success_rate', 0) * 100
        
        if success_rate >= 80:
            reliability = 'high'
        elif success_rate >= 60:
            reliability = 'medium'
        else:
            reliability = 'low'
        
        return {
            'reliability': reliability,
            'score': success_rate,
            'issues': [] if success_rate >= 70 else ['Precisión del modelo por debajo del umbral'],
            'strengths': ['Modelo validado'] if success_rate >= 70 else []
        }
    
    def _assess_statistical_validity_component(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa componente de validez estadística"""
        stat_val = validation_results.get('statistical_validation', {})
        stat_summary = stat_val.get('summary', {})
        
        if stat_summary.get('overall_validity', False):
            return {
                'reliability': 'high',
                'score': 85.0,
                'issues': [],
                'strengths': ['Tests estadísticos satisfactorios']
            }
        else:
            return {
                'reliability': 'low',
                'score': 40.0,
                'issues': ['Fallas en tests estadísticos'],
                'strengths': []
            }
    
    def _assess_temporal_consistency_component(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa componente de consistencia temporal"""
        temp_val = validation_results.get('temporal_validation', {})
        temp_summary = temp_val.get('summary', {})
        temp_score = temp_summary.get('overall_score', 50)
        
        if temp_score >= 80:
            reliability = 'high'
        elif temp_score >= 60:
            reliability = 'medium'
        else:
            reliability = 'low'
        
        return {
            'reliability': reliability,
            'score': temp_score,
            'issues': temp_summary.get('issues', []),
            'strengths': temp_summary.get('strengths', [])
        }
    
    def _assess_prediction_reliability_component(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa componente de confiabilidad de predicciones"""
        pred_val = validation_results.get('prediction_validation', {})
        pred_summary = pred_val.get('summary', {})
        avg_mape = pred_summary.get('avg_mape', 100)
        
        if avg_mape <= 15:
            reliability = 'high'
            score = 90.0
        elif avg_mape <= 30:
            reliability = 'medium'
            score = 70.0
        else:
            reliability = 'low'
            score = 40.0
        
        return {
            'reliability': reliability,
            'score': score,
            'issues': [] if avg_mape <= 25 else ['Error de predicción elevado'],
            'strengths': ['Predicciones precisas'] if avg_mape <= 20 else []
        }
    
    # Continúa con los métodos restantes...
    
    def _determine_alert_category(self, severity: str, alert_type: str) -> str:
        """Determina la categoría final de una alerta"""
        severity_map = {
            'CRITICAL': 'CRITICAL',
            'ERROR': 'ERROR',
            'WARNING': 'WARNING',
            'INFO': 'INFO',
            'SUCCESS': 'SUCCESS'
        }
        return severity_map.get(severity.upper(), 'INFO')
    
    def _get_alert_priority(self, severity: str) -> int:
        """Obtiene prioridad numérica de una alerta"""
        priority_map = {
            'CRITICAL': 0,
            'ERROR': 1,
            'WARNING': 2,
            'INFO': 3,
            'SUCCESS': 4
        }
        return priority_map.get(severity.upper(), 5)