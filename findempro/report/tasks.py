# report/tasks.py
import io
import logging
import math
import statistics
from typing import Dict, Any

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

_PDF_CACHE_TTL = 3600  # 1 hora


def _build_pdf_bytes(report) -> bytes:
    """Generate PDF bytes for a Report instance. Pure function — no Django request needed."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{report.title}</b>", styles['Title']))
    story.append(Spacer(1, 12))

    info_data = [
        ['Fecha de Creación:', report.date_created.strftime('%d/%m/%Y %H:%M')],
        ['Última Actualización:', report.last_updated.strftime('%d/%m/%Y %H:%M')],
    ]
    if report.fk_product:
        info_data.append(['Producto:', report.fk_product.name])

    info_table = Table(info_data, colWidths=[2 * 72, 4 * 72])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 18))

    if isinstance(report.content, dict):
        story.extend(_build_content_sections(report.content, styles))
    else:
        story.append(Paragraph(str(report.content), styles['Normal']))

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"<i>Generado el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}</i>",
        styles['Normal']
    ))

    doc.build(story)
    return buffer.getvalue()


def _build_content_sections(content: Dict[str, Any], styles) -> list:
    """Build ReportLab story elements from report content dict."""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    story = []

    if content.get('parametros'):
        story.append(Paragraph("<b>Parámetros de Simulación</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        param_data = [['Parámetro', 'Valor']]
        for key, value in content['parametros'].items():
            param_data.append([key.replace('_', ' ').title(), str(value)])
        t = Table(param_data, colWidths=[3 * 72, 2 * 72])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    if content.get('resultados_simulacion'):
        story.append(Paragraph("<b>Resultados de Simulación</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        results = content['resultados_simulacion']
        result_units = {
            'utilidad_neta': 'Bs',
            'flujo_caja': 'Bs/mes',
            'roi': '% horizonte',
            'punto_equilibrio': 'unidades',
            'payback_period': 'meses',
            'van': 'Bs',
            'tir': '% anual efectiva',
            'margen_unitario': 'Bs/unidad',
            'ingresos_totales': 'Bs',
        }
        for key, value in results.items():
            label = key.replace('_', ' ').title()
            rendered = 'N/A' if value is None else value
            unit = result_units.get(key, '')
            story.append(Paragraph(f"<b>{label}:</b> {rendered} {unit}".rstrip(), styles['Normal']))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 12))

    if content.get('recomendaciones'):
        story.append(Paragraph("<b>Recomendaciones</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        recs = content['recomendaciones']
        if isinstance(recs, list):
            for rec in recs:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph(str(recs), styles['Normal']))
        story.append(Spacer(1, 12))

    return story


@shared_task(bind=True, max_retries=2)
def generate_report_pdf_async(self, report_id: int, user_id: int) -> Dict[str, Any]:
    """Generate PDF for a Report asynchronously and store bytes in cache."""
    from report.models import Report

    try:
        logger.info("Generating PDF for report %s (user %s)", report_id, user_id)
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Cargando reporte...'},
        )

        report = Report.objects.select_related('fk_product').get(id=report_id)

        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': 'Generando PDF...'},
        )

        pdf_bytes = _build_pdf_bytes(report)

        cache_key = f"pdf_bytes:{report_id}:{user_id}"
        cache.set(cache_key, pdf_bytes, _PDF_CACHE_TTL)

        filename = f"{report.title.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
        cache.set(f"pdf_filename:{report_id}:{user_id}", filename, _PDF_CACHE_TTL)

        logger.info("PDF ready for report %s (%d bytes)", report_id, len(pdf_bytes))
        return {'status': 'success', 'report_id': report_id, 'size': len(pdf_bytes)}

    except Report.DoesNotExist:
        logger.error("Report %s not found", report_id)
        raise
    except Exception as exc:
        logger.error("Error generating PDF for report %s: %s", report_id, exc)
        retry_in = 30 * (2 ** self.request.retries)
        self.retry(exc=exc, countdown=retry_in)


@shared_task(bind=True, max_retries=2)
def generate_simulation_pdf_async(self, simulation_id: int, user_id: int) -> Dict[str, Any]:
    """
    Genera PDF de simulación desde resúmenes persistidos por período.

    El PDF incluye:
      · Serie temporal de utilidad media con banda P5/P95 persistida
      · Resumen descriptivo entre períodos
      · Estado no disponible para métricas que requieren muestras originales

    El PDF se guarda en cache (TTL 1h) bajo 'sim_pdf_bytes:{simulation_id}:{user_id}'.
    """
    from simulate.models import Simulation, ResultSimulation

    try:
        logger.info("Generando PDF para simulación %s (usuario %s)", simulation_id, user_id)
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Cargando simulación...'},
        )

        simulation = Simulation.objects.select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business',
            'fk_fdp',
        ).get(id=simulation_id)

        results = list(ResultSimulation.objects.filter(
            fk_simulation=simulation,
            is_active=True,
        ).order_by('date'))

        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': 'Generando resumen...'},
        )

        pdf_bytes = _build_simulation_pdf(simulation, results)

        cache_key = f'sim_pdf_bytes:{simulation_id}:{user_id}'
        cache.set(cache_key, pdf_bytes, _PDF_CACHE_TTL)

        product = simulation.fk_questionary_result.fk_questionary.fk_product
        filename = (
            f'Simulacion_{product.name.replace(" ", "_")}_{simulation_id}.pdf'
        )
        cache.set(f'sim_pdf_filename:{simulation_id}:{user_id}', filename, _PDF_CACHE_TTL)

        logger.info(
            "PDF listo para simulación %s (%d bytes, archivo=%s)",
            simulation_id, len(pdf_bytes), filename,
        )
        return {
            'status': 'success',
            'simulation_id': simulation_id,
            'size': len(pdf_bytes),
            'filename': filename,
        }

    except Simulation.DoesNotExist:
        logger.error("Simulación %s no encontrada", simulation_id)
        raise
    except Exception as exc:
        logger.error("Error generando PDF para simulación %s: %s", simulation_id, exc)
        retry_in = 30 * (2 ** self.request.retries)
        self.retry(exc=exc, countdown=retry_in)


def _extract_persisted_profit_summary(results: list) -> Dict[str, Any]:
    """Extract finite persisted summaries without reconstructing observations."""
    periods = []
    excluded = 0
    for period_number, result in enumerate(results, start=1):
        variables = getattr(result, 'variables', None)
        if not isinstance(variables, dict):
            excluded += 1
            continue
        try:
            mean_value = float(variables['profit_mean'])
            p5_value = float(variables['profit_p5'])
            p95_value = float(variables['profit_p95'])
        except (KeyError, TypeError, ValueError):
            excluded += 1
            continue
        if not all(math.isfinite(value) for value in (mean_value, p5_value, p95_value)):
            excluded += 1
            continue
        if not p5_value <= mean_value <= p95_value:
            excluded += 1
            continue
        periods.append({
            'period': period_number,
            'mean': mean_value,
            'p5': p5_value,
            'p95': p95_value,
        })

    means = [period['mean'] for period in periods]
    return {
        'periods': periods,
        'excluded_periods': excluded,
        'mean_of_period_means': statistics.fmean(means) if means else None,
        'std_of_period_means': statistics.pstdev(means) if len(means) > 1 else None,
        'negative_mean_periods': sum(value < 0 for value in means),
        'risk_metrics_available': False,
        'risk_unavailable_reason': 'ORIGINAL_MONTE_CARLO_SAMPLES_NOT_PERSISTED',
        'method_version': 'simulation_report_summary_v2',
    }


def _build_simulation_pdf(simulation, results: list) -> bytes:
    """
    Construye el PDF de simulación con Matplotlib + ReportLab.

    Requiere: reportlab, matplotlib (opcionales; falla con ImportError si no están).
    """
    import matplotlib
    matplotlib.use('Agg')   # sin GUI — debe ir antes de plt
    import matplotlib.pyplot as plt
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage,
    )

    # ── Extraer series por período ────────────────────────────────────────────
    summary = _extract_persisted_profit_summary(results)
    periods_data = summary['periods']
    if len(periods_data) < 2:
        return _build_minimal_pdf(simulation, results)

    profit_means = [period['mean'] for period in periods_data]
    profit_p5 = [period['p5'] for period in periods_data]
    profit_p95 = [period['p95'] for period in periods_data]

    # ── Reconstruir distribución de utilidades desde estadísticas ────────────
    # σ estimada del rango inter-percentil  (P5/P95 ≈ ±1.645σ → rango = 3.29σ)

    # ── Métricas de riesgo ────────────────────────────────────────────────────
    cl = simulation.confidence_level

    # ── Generar figuras Matplotlib ────────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor('white')

    ax1.axis('off')
    ax1.set_title('Diagnóstico de Riesgo', fontsize=10, fontweight='bold')
    ax1.text(
        0.5, 0.55,
        'NO DISPONIBLE\n\nLas muestras originales de Monte Carlo\nno están persistidas. No se reconstruyen\nvalores para estimar VaR, CVaR o P(pérdida).',
        ha='center', va='center', fontsize=9,
        bbox={'boxstyle': 'round', 'facecolor': '#f8fafc', 'edgecolor': '#94a3b8'},
    )

    # Serie temporal
    periods = [period['period'] for period in periods_data]
    ax2.plot(periods, profit_means, color='#2563eb', linewidth=1.8,
             marker='o', markersize=2.5)
    ax2.fill_between(periods, profit_p5, profit_p95,
                     alpha=0.2, color='#2563eb', label='IC 90%')
    ax2.axhline(0, color='#dc2626', linestyle='--', linewidth=1, alpha=0.6)
    ax2.set_xlabel('Período', fontsize=9)
    ax2.set_ylabel('Utilidad media (BOB)', fontsize=9)
    ax2.set_title('Evolución por Período', fontsize=10, fontweight='bold')
    ax2.legend(fontsize=7)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='PNG', dpi=150, bbox_inches='tight')
    plt.close(fig)
    img_buf.seek(0)

    # ── Construir PDF con ReportLab ───────────────────────────────────────────
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    story  = []

    product = simulation.fk_questionary_result.fk_questionary.fk_product

    story.append(Paragraph('<b>Reporte de Simulación Monte Carlo</b>', styles['Title']))
    story.append(Paragraph(
        f'Producto: <b>{product.name}</b> | Empresa: <b>{product.fk_business.name}</b>',
        styles['Normal'],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f'Períodos: {simulation.duration_in_days} días | '
        f'Distribución: {simulation.fk_fdp.get_distribution_type_display()} | '
        f'Confianza: {int(cl * 100)}%',
        styles['Normal'],
    ))
    story.append(Spacer(1, 14))

    # Gráficos
    story.append(RLImage(img_buf, width=6.5 * inch, height=2.6 * inch))
    story.append(Spacer(1, 14))

    # Tabla de métricas de riesgo
    story.append(Paragraph('<b>Métricas de Riesgo (BOB)</b>', styles['Heading2']))
    story.append(Spacer(1, 6))

    risk_rows = [
        ['Métrica', 'Valor (BOB)', 'Interpretación'],
        ['Media entre períodos', f'{summary["mean_of_period_means"]:,.2f}',
         'Media descriptiva de las utilidades medias persistidas'],
        ['Desv. entre períodos', f'{summary["std_of_period_means"]:,.2f}',
         'Variabilidad descriptiva entre medias de período'],
        [f'VaR ({int(cl*100)}%)', 'N/A',
         'No disponible sin las muestras originales de Monte Carlo'],
        [f'CVaR / ES ({int(cl*100)}%)', 'N/A',
         'No disponible sin las muestras originales de Monte Carlo'],
        ['Ratio de Sharpe',            'N/A',
         'No aplicable: se requieren retornos periodizados, no utilidad monetaria'],
        ['Ratio de Sortino',           'N/A',
         'No aplicable: se requieren retornos periodizados, no utilidad monetaria'],
        ['Períodos con media negativa',
         f'{summary["negative_mean_periods"]}/{len(periods_data)}',
         'Conteo observado; no es una probabilidad de pérdida'],
    ]

    t = Table(risk_rows, colWidths=[1.8 * inch, 1.5 * inch, 3.2 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  colors.HexColor('#2563eb')),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  colors.whitesmoke),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 9),
        ('ALIGN',        (1, 1), (1, -1),  'RIGHT'),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1),
         [colors.white, colors.HexColor('#eff6ff')]),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTNAME',     (0, 1), (0, -1),  'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        '<b>Metodología:</b> simulation_report_summary_v2. El reporte usa exclusivamente '
        'profit_mean, profit_p5 y profit_p95 persistidos por período. No genera ni '
        'reconstruye muestras. Las métricas dependientes de muestras se muestran como N/A.',
        styles['Normal'],
    ))
    if summary['excluded_periods']:
        story.append(Paragraph(
            f'<b>Calidad de datos:</b> se excluyeron {summary["excluded_periods"]} '
            'período(s) sin resumen finito y coherente.',
            styles['Normal'],
        ))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f'<i>Generado por FindemproAI el '
        f'{timezone.now().strftime("%d/%m/%Y a las %H:%M")} — Moneda: Boliviano (BOB)</i>',
        styles['Normal'],
    ))

    doc.build(story)
    return pdf_buf.getvalue()


def _build_minimal_pdf(simulation, results: list) -> bytes:
    """Fallback PDF when persisted summaries are insufficient."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    product = simulation.fk_questionary_result.fk_questionary.fk_product

    doc.build([
        Paragraph('<b>Reporte de Simulación</b>', styles['Title']),
        Spacer(1, 12),
        Paragraph(f'Producto: {product.name}', styles['Normal']),
        Spacer(1, 6),
        Paragraph(
            f'La simulación #{simulation.id} tiene {len(results)} período(s) registrado(s). '
            'No hay al menos 2 períodos con profit_mean, profit_p5 y profit_p95 '
            'finitos y coherentes. Las métricas de riesgo no se calculan ni se inventan.',
            styles['Normal'],
        ),
    ])
    return buf.getvalue()
