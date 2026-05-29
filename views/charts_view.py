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
    bars = ax.bar(labels, values, color=BAR_COLOR, edgecolor=BAR_EDGE,
                linewidth=0.6, width=0.55, zorder=3)
    
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

    # Pasamos la moneda dinámica al label del eje Y
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


def _chart_por_dia(data, moneda):
    totales = defaultdict(float)
    for r in data:
        key = (r["anio"], r["mes"], r["dia"])
        totales[key] += r["monto"]

    if not totales:
        return None

    keys_sorted = sorted(totales.keys())
    
    if len(keys_sorted) > 30:
        keys_sorted = keys_sorted[-30:]

    labels = [f"{d:02d}-{m:02d}-{y}" for y, m, d in keys_sorted]
    values = [totales[k] for k in keys_sorted]
    
    return _build_chart_image(labels, values, "Gastos por Día (Últimos 30 días con actividad)", "Fecha", moneda)


def _chart_por_mes(data, moneda):
    MESES = ["Ene","Feb","Mar","Abr","May","Jun",
            "Jul","Ago","Sep","Oct","Nov","Dic"]
    totales = defaultdict(float)
    for r in data:
        key = (r["anio"], r["mes"])
        totales[key] += r["monto"]
    if not totales:
        return None
    keys_sorted = sorted(totales.keys())
    labels = [f"{MESES[m-1]} {y}" for y, m in keys_sorted]
    values = [totales[k] for k in keys_sorted]
    return _build_chart_image(labels, values, "Gastos por Mes", "Mes", moneda)


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
        "No hay facturas registradas para mostrar.",
        size=13, color=TEXT_GRAY,
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
                ft.Icon(ft.Icons.BAR_CHART_OUTLINED, size=40, color="#cccccc"),
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

    def show_chart(chart_fn, btn):
        _set_active(btn, chart_fn)
        data_total = _get_data()
        
        # Se filtra la data en memoria por la moneda seleccionada en el Dropdown
        moneda_seleccionada = dd_moneda.value
        data_filtrada = [r for r in data_total if r["moneda"] == moneda_seleccionada]
        
        if data_filtrada:
            b64 = chart_fn(data_filtrada, moneda_seleccionada)
        else:
            b64 = None

        if b64:
            img_control.src_base64    = b64
            chart_container.visible   = True
            no_data_container.visible = False
        else:
            chart_container.visible   = False
            no_data_container.visible = True
        page.update()

    dd_moneda = ft.Dropdown(
        label="Moneda",
        width=110,
        color=PRIMARY,
        border_color=PRIMARY,
        label_style=ft.TextStyle(color=PRIMARY, size=12, weight=ft.FontWeight.BOLD),
        border_width=1.5,
        options=[
            ft.dropdown.Option("ARS"),
            ft.dropdown.Option("USD"),
            ft.dropdown.Option("EUR"),
            ft.dropdown.Option("BRL"),
        ],
        value="ARS",
        # Al cambiar la moneda, si hay un gráfico seleccionado previamente, lo vuelve a dibujar con el nuevo filtro
        on_change=lambda e: show_chart(active["fn"], active["btn"]) if active["fn"] else page.update()
    )

    btn_dia  = ft.ElevatedButton("Por Día",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_dia,  btn_dia))
    btn_mes  = ft.ElevatedButton("Por Mes",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_mes,  btn_mes))
    btn_anio = ft.ElevatedButton("Por Año",  style=_btn_style(False),
                                on_click=lambda e: show_chart(_chart_por_anio, btn_anio))

    return ft.Column([
        section_title("Gráficas de Gastos"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Text("Seleccioná el período y divisa", size=14,
                    weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row([dd_moneda, btn_dia, btn_mes, btn_anio, btn_export], spacing=12),
        ], spacing=8)),
        chart_container,
        no_data_container,
    ], spacing=8, expand=True)