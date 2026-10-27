"""Gráficas de los notebooks. Una sola plantilla para que todas se vean igual."""
import plotly.graph_objects as go
import plotly.io as pio

PALETA = ["#2a6f97", "#d1495b", "#edae49", "#66a182", "#8d6a9f"]

pio.templates["hfdemo"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, Segoe UI, sans-serif", size=13),
        colorway=PALETA,
        margin=dict(l=60, r=20, t=60, b=50),
    )
)
pio.templates.default = "plotly_white+hfdemo"


def barras_agrupadas(categorias, series: dict, titulo, eje_x, eje_y):
    """Barras agrupadas: `series` es {nombre: valores alineados con `categorias`}."""
    fig = go.Figure([go.Bar(name=n, x=categorias, y=v) for n, v in series.items()])
    fig.update_layout(title=titulo, xaxis_title=eje_x, yaxis_title=eje_y, barmode="group")
    return fig
