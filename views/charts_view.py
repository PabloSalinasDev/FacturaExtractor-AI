import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import io
import base64
from collections import defaultdict
from datetime import datetime

from db.crud import get_all_facturas
from modules.csv_exporter import export_reporte_csv
from views.helpers import (
    card, section_title, 
    show_snack, btn_outline, PENDING, ACCENT, PRIMARY, TEXT_GRAY, 
    BAR_COLOR, BAR_EDGE, GRID_COLOR, LABEL_COLOR, TITLE_COLOR
)


def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110,
                facecolor="white", edgecolor="none")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def _style_ax(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold", color=TITLE_COLOR, pad=12)
    ax.set_xlabel(xlabel, fontsize=10, color=LABEL_COLOR)
    ax.set_ylabel(ylabel, fontsize=10, color=LABEL_COLOR)
    ax.tick_params(colors=LABEL_COLOR, labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x:,.0f}"
    ))
    ax.set_facecolor("white")
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)


# Recibe el parámetro 'moneda' para setear el eje Y correctamente
def _build_chart_image(labels, values, title, xlabel, moneda):
    ancho_dinamico = max(6, len(labels) * 0.5)
    fig, ax = plt.subplots(figsize=(ancho_dinamico, 4))
    bar_width = 0.34 if len(labels) <= 6 else min(0.34, 0.1 + len(labels) * 0.04)
    bars = ax.bar(labels, values, color=BAR_COLOR, edgecolor=BAR_EDGE,
                linewidth=0.6, width=bar_width, zorder=3)
    
    if len(labels) == 1:
        ax.set_xlim(-1, 1)

    # Valor encima de cada barra
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + max(values) * 0.01,
            f"${h:,.0f}", ha="center", va="bottom",
            fontsize=8, color=TITLE_COLOR,
        )

    # Se pasa la moneda dinámica al label del eje Y
    _style_ax(ax, title, xlabel, f"Monto ({moneda})")
    if len(labels) > 6:
        plt.xticks(rotation=30, ha="right")
    else:
        plt.xticks(rotation=0, ha="center")
    fig.tight_layout()
    return _fig_to_base64(fig)


def _parse_fecha(fecha_str):
    """
    Parsea de forma segura la fecha garantizada como DD-MM-YYYY de la BD.
    Devuelve una tupla de 3 enteros: (dia, mes, anio).
    """
    try:
        dt = datetime.strptime(fecha_str.strip(), "%d-%m-%Y")
        return dt.day, dt.month, dt.year
    except (ValueError, AttributeError, TypeError):
        hoy = datetime.now()
        return hoy.day, hoy.month, hoy.year

def _get_data():
    rows = get_all_facturas()
    result = []
    for row in rows:
        fecha_cruda  = row[2]  
        monto_crudo  = row[3]  
        moneda_cruda = row[4]  
        
        parsed = _parse_fecha(fecha_cruda)
        if parsed:
            d, m, y = parsed
            result.append({
                "dia": d, 
                "mes": m, 
                "anio": y, 
                "monto": float(monto_crudo),
                "moneda": str(moneda_cruda).upper() if moneda_cruda else "ARS"
            })
    return result


def _chart_por_dia(data, moneda, anio_filtro=None, mes_filtro=None):
    hoy = datetime.now()
    anio_ref = anio_filtro if anio_filtro else hoy.year
    mes_ref  = mes_filtro  if mes_filtro  else hoy.month

    filtrada = [r for r in data if r["anio"] == anio_ref and r["mes"] == mes_ref]

    totales = defaultdict(float)
    for r in filtrada:
        totales[r["dia"]] += r["monto"]

    if not totales:
        return None

    MESES = ["Ene","Feb","Mar","Abr","May","Jun",
            "Jul","Ago","Sep","Oct","Nov","Dic"]
    keys_sorted = sorted(totales.keys())
    labels = [f"{d:02d}" for d in keys_sorted]
    values = [totales[k] for k in keys_sorted]
    titulo = f"Gastos por Día — {MESES[mes_ref-1]} {anio_ref}"
    return _build_chart_image(labels, values, titulo, "Día", moneda)


def _chart_por_mes(data, moneda, anio_filtro=None):
    hoy = datetime.now()
    anio_ref = anio_filtro if anio_filtro else hoy.year

    filtrada = [r for r in data if r["anio"] == anio_ref]

    MESES = ["Ene","Feb","Mar","Abr","May","Jun",
            "Jul","Ago","Sep","Oct","Nov","Dic"]
    totales = defaultdict(float)
    for r in filtrada:
        totales[r["mes"]] += r["monto"]
    if not totales:
        return None
    keys_sorted = sorted(totales.keys())
    labels = [MESES[m-1] for m in keys_sorted]
    values = [totales[k] for k in keys_sorted]
    titulo = f"Gastos por Mes — {anio_ref}"
    return _build_chart_image(labels, values, titulo, "Mes", moneda)


def _chart_por_anio(data, moneda):
    totales = defaultdict(float)
    for r in data:
        totales[r["anio"]] += r["monto"]
    if not totales:
        return None
    keys   = sorted(totales.keys())
    labels = [str(k) for k in keys]
    values = [totales[k] for k in keys]
    return _build_chart_image(labels, values, "Gastos por Año", "Año", moneda)


def build_charts(page):
    img_control = ft.Image(fit=ft.ImageFit.CONTAIN, expand=True)
    no_data_msg = ft.Text(
        "No hay facturas registradas para mostrar",
        size=20, color=TEXT_GRAY,
    )
    chart_container = ft.Container(
        content=ft.Column(
            [img_control],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        visible=False,
        expand=True,
    )
    no_data_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.BAR_CHART_OUTLINED, size=100, color="#cccccc"),
                no_data_msg,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        visible=False,
        expand=True,
        padding=40,
    )

    # Estado del botón activo
    active = {"btn": None, "fn": None}

    def _set_active(btn, chart_fn):
        for b in [btn_dia, btn_mes, btn_anio]:
            b.style = _btn_style(b == btn)
        active["btn"] = btn
        active["fn"] = chart_fn
        page.update()

    def _btn_style(selected):
        if selected:
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: PRIMARY},
                color={ft.ControlState.DEFAULT: "white"},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=11),
            )
        return ft.ButtonStyle(
            side=ft.BorderSide(1.5, PRIMARY),
            color=PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=11),
        )

    def do_export(e):
        data = _get_data()
        if not data:
            show_snack(page, "No hay datos para exportar.", PENDING)
            return
        path = export_reporte_csv(data)
        show_snack(page, f"Reporte exportado: {Path(path).name}")

    btn_export = btn_outline("Exportar Reporte", do_export,
                            icon=ft.Icons.DOWNLOAD, color=PRIMARY)

    def _dd_style(width):
        return dict(
            width=width,
            color=PRIMARY,
            border_color=PRIMARY,
            label_style=ft.TextStyle(color=PRIMARY, size=12, weight=ft.FontWeight.BOLD),
            border_width=1.5,
        )

    MESES_OPTS = [
        ft.dropdown.Option("1",  "Enero"),   ft.dropdown.Option("2",  "Febrero"),
        ft.dropdown.Option("3",  "Marzo"),   ft.dropdown.Option("4",  "Abril"),
        ft.dropdown.Option("5",  "Mayo"),    ft.dropdown.Option("6",  "Junio"),
        ft.dropdown.Option("7",  "Julio"),   ft.dropdown.Option("8",  "Agosto"),
        ft.dropdown.Option("9",  "Sep"),     ft.dropdown.Option("10", "Oct"),
        ft.dropdown.Option("11", "Nov"),     ft.dropdown.Option("12", "Dic"),
    ]

    dd_moneda = ft.Dropdown(
        label="Moneda",
        options=[
            ft.dropdown.Option("ARS"),
            ft.dropdown.Option("USD"),
            ft.dropdown.Option("EUR"),
            ft.dropdown.Option("BRL"),
        ],
        value="ARS",
        **_dd_style(110),
        on_change=lambda e: _refresh_chart(),
    )

    dd_anio = ft.Dropdown(
        label="Año",
        options=[],   # se pobla en _refresh_anios()
        value=None,
        hint_text="Todos",
        **_dd_style(110),
        on_change=lambda e: _refresh_chart(),
    )

    dd_mes = ft.Dropdown(
        label="Mes",
        options=MESES_OPTS,
        value=None,
        hint_text="Mes actual",
        **_dd_style(130),
        on_change=lambda e: _refresh_chart(),
    )

    def _refresh_anios():
        """Rellena dd_anio con los años que existen en la BD para la moneda elegida."""
        data_total = _get_data()
        moneda = dd_moneda.value
        anios = sorted({r["anio"] for r in data_total if r["moneda"] == moneda}, reverse=True)
        dd_anio.options = [ft.dropdown.Option(str(a)) for a in anios]
        # Si el valor actual ya no existe en la nueva lista, lo limpiamos
        valores_validos = [str(a) for a in anios]
        if dd_anio.value and dd_anio.value not in valores_validos:
            dd_anio.value = None
            dd_mes.value  = None  # si el año desaparece, el mes pierde contexto
            return

        # Validar que el mes seleccionado tenga datos en el año/moneda actual
        if dd_mes.value:
            anio_ref = int(dd_anio.value) if dd_anio.value else datetime.now().year
            mes_ref  = int(dd_mes.value)
            hay_datos = any(
                r["anio"] == anio_ref and r["mes"] == mes_ref and r["moneda"] == moneda
                for r in data_total
            )
            if not hay_datos:
                dd_mes.value = None

    def _refresh_chart():
        if not active["fn"]:
            _refresh_anios()
            page.update()
            return
        _refresh_anios()
        show_chart(active["fn"], active["btn"])

    def show_chart(chart_fn, btn):
        _set_active(btn, chart_fn)
        data_total   = _get_data()
        moneda       = dd_moneda.value
        anio_val     = int(dd_anio.value) if dd_anio.value else None
        mes_val      = int(dd_mes.value)  if dd_mes.value  else None

        data_filtrada = [r for r in data_total if r["moneda"] == moneda]

        # Despachar según el botón activo
        if chart_fn is _chart_por_anio:
            # Siempre todos los años — ignora los dropdowns de año/mes
            b64 = _chart_por_anio(data_filtrada, moneda)

        elif chart_fn is _chart_por_mes:
            # Filtra por año seleccionado; si no hay, usa el año en curso
            b64 = _chart_por_mes(data_filtrada, moneda, anio_filtro=anio_val)

        else:  # _chart_por_dia
            # Filtra por mes seleccionado (y el año de ese mes si también fue elegido)
            b64 = _chart_por_dia(data_filtrada, moneda,
                                    anio_filtro=anio_val, mes_filtro=mes_val)

        if b64:
            img_control.src_base64    = b64
            chart_container.visible   = True
            no_data_container.visible = False
        else:
            chart_container.visible   = False
            no_data_container.visible = True
        page.update()

    btn_dia  = ft.ElevatedButton("Por Día",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_dia,  btn_dia))
    btn_mes  = ft.ElevatedButton("Por Mes",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_mes,  btn_mes))
    btn_anio = ft.ElevatedButton("Por Año",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_anio, btn_anio))

    # Poblar años al construir la vista
    _refresh_anios()

    return ft.Column([
        section_title("Gráficas de Gastos"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Text("Seleccioná el período y divisa", size=14,
                    weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row(
                [dd_moneda, dd_anio, dd_mes, btn_dia, btn_mes, btn_anio, btn_export],
                spacing=12,
                wrap=True,
            ),
        ], spacing=8)),
        chart_container,
        no_data_container,
    ], spacing=8, expand=True)