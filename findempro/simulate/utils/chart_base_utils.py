# utils/chart_base.py
import base64
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional
from functools import lru_cache

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from django.core.cache import cache

from dashboards.models import Chart
from variable.models import Variable

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

# Configure matplotlib for better performance
plt.rcParams['figure.max_open_warning'] = 0
plt.rcParams['figure.autolayout'] = True
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

logger = logging.getLogger(__name__)
# Silenciar específicamente los mensajes de findfont
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# Opcional: configurar una fuente por defecto para evitar búsquedas
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']

class ChartBase:
    """Base class for chart generation with common functionality"""
    
    def __init__(self):
        self.iniciales_a_buscar = [
            'CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 
            'NR', 'GO', 'GG', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 
            'CUP', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PE', 
            'HO', 'CHO', 'CA'
        ]
        self.cache_timeout = 3600  # 1 hour
        self._setup_plot_style()
    
    def _setup_plot_style(self):
        """Set up consistent plot styling"""
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    @lru_cache(maxsize=128)
    def _get_variable_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get cached variable mapping"""
        variables_db = Variable.objects.filter(
            initials__in=self.iniciales_a_buscar
        ).values('initials', 'name', 'unit')
        
        return {
            variable['initials']: {
                'name': variable['name'], 
                'unit': variable['unit']
            } 
            for variable in variables_db
        }
    
    def _validate_chart_data(self, chart_data: Dict) -> bool:
        """Validate chart data before plotting"""
        if not chart_data or 'labels' not in chart_data or 'datasets' not in chart_data:
            return False
        
        if not chart_data['labels'] or not chart_data['datasets']:
            return False
        
        # Check all datasets have same length as labels
        labels_len = len(chart_data['labels'])
        for dataset in chart_data['datasets']:
            if len(dataset.get('values', [])) != labels_len:
                return False
        
        return True
    
    def _configure_plot(self, ax, chart_data: Dict, title: str, description: str):
        """Configure plot appearance and labels"""
        # Set labels
        ax.set_xlabel(chart_data.get('x_label', 'X'), fontsize=12)
        ax.set_ylabel(chart_data.get('y_label', 'Y'), fontsize=12)
        
        # Set title
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Rotate x labels if many
        if len(chart_data['labels']) > 20:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add description as subtitle
        ax.text(0.5, -0.15, description, transform=ax.transAxes, 
               ha='center', fontsize=10, style='italic', wrap=True)
        
        # Improve layout
        plt.tight_layout()
    
    def _save_plot_as_base64(self, fig: Figure) -> str:
        """Save matplotlib figure as base64 encoded string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return image_data
    
    def _plot_line_chart(self, ax, chart_data: Dict):
        """Plot enhanced line chart with statistics"""
        labels = chart_data['labels']
        
        for i, dataset in enumerate(chart_data['datasets']):
            values = dataset['values']
            ax.plot(labels, values, label=dataset['label'], 
                   linewidth=2, marker='o', markersize=4)
            
            # Add trend line for each dataset
            if len(labels) > 2:
                z = np.polyfit(labels, values, 1)
                p = np.poly1d(z)
                ax.plot(labels, p(labels), '--', alpha=0.5)
        
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_bar_chart(self, ax, chart_data: Dict):
        """Plot enhanced bar chart"""
        labels = chart_data['labels']
        x = np.arange(len(labels))
        width = 0.8 / len(chart_data['datasets'])
        
        for i, dataset in enumerate(chart_data['datasets']):
            offset = (i - len(chart_data['datasets'])/2) * width + width/2
            bars = ax.bar(x + offset, dataset['values'], width, 
                          label=dataset['label'], alpha=0.8)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def _plot_scatter_chart(self, ax, chart_data: Dict):
        """Plot scatter chart with regression lines"""
        labels = chart_data['labels']
        
        for i, dataset in enumerate(chart_data['datasets']):
            ax.scatter(labels, dataset['values'], label=dataset['label'], 
                      s=50, alpha=0.7)
            
            # Add regression line
            if len(labels) > 1:
                z = np.polyfit(labels, dataset['values'], 1)
                p = np.poly1d(z)
                ax.plot(labels, p(labels), '--', alpha=0.8)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_histogram_chart(self, ax, chart_data: Dict):
        """Plot histogram with statistics"""
        for dataset in chart_data['datasets']:
            values = dataset['values']
            
            # Plot histogram with KDE
            n, bins, patches = ax.hist(values, bins=20, alpha=0.7, 
                                      density=True, label=dataset['label'])
            
            # Add KDE curve
            from scipy import stats
            kde = stats.gaussian_kde(values)
            x_range = np.linspace(min(values), max(values), 100)
            ax.plot(x_range, kde(x_range), linewidth=2)
            
            # Add statistics
            mean_val = np.mean(values)
            std_val = np.std(values)
            ax.axvline(mean_val, color='red', linestyle='--', 
                      label=f'Media: {mean_val:.2f}')
            
            # Add text box with stats
            textstr = f'μ={mean_val:.2f}\nσ={std_val:.2f}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, 
                   verticalalignment='top', bbox=props)
        
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def _plot_stacked_bar_chart(self, ax, chart_data: Dict):
        """Plot stacked bar chart"""
        labels = chart_data['labels']
        x = np.arange(len(labels))
        bottom = np.zeros(len(labels))
        
        colors = plt.cm.get_cmap('tab10')(range(len(chart_data['datasets'])))
        
        for i, dataset in enumerate(chart_data['datasets']):
            values = np.array(dataset['values'])
            bars = ax.bar(x, values, label=dataset['label'], 
                          bottom=bottom, alpha=0.8, color=colors[i])
            
            # Add percentage labels
            for j, (bar, val) in enumerate(zip(bars, values)):
                if val > 0:
                    total = sum(d['values'][j] for d in chart_data['datasets'])
                    percentage = (val / total * 100) if total > 0 else 0
                    if percentage > 5:  # Only show if > 5%
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., 
                               bottom[j] + height/2,
                               f'{percentage:.1f}%', ha='center', 
                               va='center', fontsize=8)
            
            bottom += values
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def get_chart_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about chart generation performance"""
        stats = cache.get('chart_generation_stats', {})
        return {
            'total_generated': stats.get('total', 0),
            'average_time': stats.get('avg_time', 0),
            'cache_hits': stats.get('cache_hits', 0),
            'errors': stats.get('errors', 0),
        }
        
    