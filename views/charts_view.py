import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import io
import base64
from collections import defaultdict

from db.crud import get_all_facturas
from modules.csv_exporter import export_reporte_csv
from views.helpers import (
    card, section_title,
    ACCENT, PRIMARY, TEXT_GRAY, show_snack, PENDING,
    btn_outline,
)

# ── COLORES MATPLOTLIB ──────────────────────────
BAR_COLOR    = "#2ecc71"
BAR_EDGE     = "#27ae60"
GRID_COLOR   = "#eeeeee"
LABEL_COLOR  = "#6c757d"
TITLE_COLOR  = "#1a1a2e"


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


def _build_chart_image(labels, values, title, xlabel):
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(labels, values, color=BAR_COLOR, edgecolor=BAR_EDGE,
                linewidth=0.6, width=0.55, zorder=3)

    # Valor encima de cada barra
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + max(values) * 0.01,
            f"${h:,.0f}", ha="center", va="bottom",
            fontsize=8, color=TITLE_COLOR,
        )

    _style_ax(ax, title, xlabel, "Monto (ARS)")
    plt.xticks(rotation=45 if len(labels) > 6 else 0, ha="right")
    fig.tight_layout()
    return _fig_to_base64(fig)


def _parse_fecha(fecha):
    """Intenta parsear DD-MM-YYYY o DD/MM/YYYY. Retorna (dia, mes, anio) o None."""
    for sep in ("-", "/"):
        parts = fecha.split(sep)
        if len(parts) == 3:
            try:
                return int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                pass
    return None


def _get_data():
    rows = get_all_facturas()
    # rows: id, proveedor, fecha, monto, moneda, estado, fuente, archivo, created_at
    result = []
    for row in rows:
        parsed = _parse_fecha(row[2])
        if parsed:
            d, m, y = parsed
            result.append({"dia": d, "mes": m, "anio": y, "monto": float(row[3])})
    return result


def _chart_por_dia(data):
    totales = defaultdict(float)
    for r in data:
        key = (r["anio"], r["mes"], r["dia"])
        totales[key] += r["monto"]
    if not totales:
        return None
    keys_sorted = sorted(totales.keys())
    labels = [f"{d:02d}-{m:02d}-{y}" for y, m, d in keys_sorted]
    values = [totales[k] for k in keys_sorted]
    return _build_chart_image(labels, values, "Gastos por Día", "Fecha")


def _chart_por_mes(data):
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
    return _build_chart_image(labels, values, "Gastos por Mes", "Mes")


def _chart_por_anio(data):
    totales = defaultdict(float)
    for r in data:
        totales[r["anio"]] += r["monto"]
    if not totales:
        return None
    keys   = sorted(totales.keys())
    labels = [str(k) for k in keys]
    values = [totales[k] for k in keys]
    return _build_chart_image(labels, values, "Gastos por Año", "Año")


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
    active = {"btn": None}

    def _set_active(btn):
        for b in [btn_dia, btn_mes, btn_anio]:
            b.style = _btn_style(b == btn)
        active["btn"] = btn
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
        _set_active(btn)
        data = _get_data()
        b64  = chart_fn(data)
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

    return ft.Column([
        section_title("Gráficas de Gastos"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Text("Seleccioná el período", size=14,
                    weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row([btn_dia, btn_mes, btn_anio, btn_export], spacing=12),
        ], spacing=8)),
        chart_container,
        no_data_container,
    ], spacing=8, expand=True)