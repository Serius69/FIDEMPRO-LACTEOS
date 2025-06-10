import base64
import logging
from io import BytesIO
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

class ChartBase:
    def __init__(self):
        self.cache_timeout = 3600
        self._setup_plot_style()

    def _setup_plot_style(self):
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        plt.rcParams['figure.max_open_warning'] = 0
        plt.rcParams['figure.autolayout'] = True
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10

    def _save_plot_as_base64(self, fig):
        try:
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            buf.close()
            return image_base64
        except Exception as e:
            logger.error(f"Error saving plot as base64: {str(e)}")
            return None