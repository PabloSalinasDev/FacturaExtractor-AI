import csv
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def export_to_csv(facturas, custom_path=None):
    """
    Exporta la lista de facturas a un CSV.
    Retorna el path del archivo generado.
    """
    if custom_path:
        dest = Path(custom_path)
    else:
        desktop = Path(os.path.expanduser("~")) / "Desktop"
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest    = desktop / f"facturas_export_{ts}.csv"

    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Proveedor", "Fecha", "Monto", "Moneda",
                        "Estado", "Fuente", "Archivo", "Registrado"])
        for row in facturas:
            writer.writerow(row)

    return str(dest)


def export_reporte_csv(data, custom_path=None):
    """
    Genera un reporte CSV con gastos por mes (año actual),
    gastos por año y total general.
    data: lista de dicts con claves dia, mes, anio, monto.
    Retorna el path del archivo generado.
    """
    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    anio_actual = datetime.now().year

    # Subtotales por mes del año actual
    por_mes = defaultdict(float)
    for r in data:
        if r["anio"] == anio_actual:
            por_mes[r["mes"]] += r["monto"]

    # Subtotales por año
    por_anio = defaultdict(float)
    for r in data:
        por_anio[r["anio"]] += r["monto"]

    total_general = sum(r["monto"] for r in data)

    if custom_path:
        dest = Path(custom_path)
    else:
        desktop = Path(os.path.expanduser("~")) / "Desktop"
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest    = desktop / f"reporte_gastos_{ts}.csv"

    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # Fecha de generación
        writer.writerow(["Reporte generado:", datetime.now().strftime("%d-%m-%Y %H:%M")])
        writer.writerow([])

        # Gastos por mes del año actual
        writer.writerow([f"GASTOS POR MES ({anio_actual})"])
        writer.writerow(["Mes", "Monto"])
        for m in range(1, 13):
            monto = por_mes.get(m, 0.0)
            writer.writerow([MESES[m - 1], f"{monto:,.2f}"])
        writer.writerow([])

        # Gastos por año
        writer.writerow(["GASTOS POR AÑO"])
        writer.writerow(["Año", "Monto"])
        for anio in sorted(por_anio.keys()):
            writer.writerow([anio, f"{por_anio[anio]:,.2f}"])
        writer.writerow([])

        # Total general
        writer.writerow(["TOTAL GENERAL"])
        writer.writerow([f"{total_general:,.2f}"])

    return str(dest)