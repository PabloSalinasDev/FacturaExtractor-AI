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
    Genera el reporte respetando el diseño original del proyecto (Repomix)
    pero repitiendo las secciones por cada moneda de forma aislada.
    Garantiza que todo el archivo tenga una estructura fija de 2 columnas,
    haciendo que los visores estrictos y Excel lo abran de forma impecable.
    """
    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    anio_actual = datetime.now().year

    # 1. Detectar qué monedas tienen datos realmente
    monedas_presentes = sorted(list(set(r.get("moneda", "ARS").upper() for r in data))) if data else ["ARS"]

    # 2. Estructurar la data en diccionarios de doble entrada: [moneda][mes/anio]
    por_mes_moneda = defaultdict(lambda: defaultdict(float))
    por_anio_moneda = defaultdict(lambda: defaultdict(float))
    total_general_moneda = defaultdict(float)

    for r in data:
        mnd = r.get("moneda", "ARS").upper()
        monto = r["monto"]
        
        # Subtotales por mes del año actual
        if r["anio"] == anio_actual:
            por_mes_moneda[mnd][r["mes"]] += monto
            
        # Subtotales por año
        por_anio_moneda[mnd][r["anio"]] += monto
        
        # Acumulado absoluto
        total_general_moneda[mnd] += monto

    # Definir ruta de salida en el Escritorio
    if custom_path:
        dest = Path(custom_path)
    else:
        desktop = Path(os.path.expanduser("~")) / "Desktop"
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest    = desktop / f"reporte_gastos_{ts}.csv"

    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Encabezado general del documento (2 columnas estrictas)
        writer.writerow(["Reporte generado:", datetime.now().strftime("%d-%m-%Y %H:%M")])
        writer.writerow(["", ""]) # Línea divisoria simétrica

        for mnd in monedas_presentes:
            
            # --- SECCIÓN 1: GASTOS POR MES ---
            writer.writerow([f"GASTOS POR MES ({anio_actual}) - DIVISA: {mnd}", ""])
            writer.writerow(["Mes", "Monto"])
            for m in range(1, 13):
                monto_mes = por_mes_moneda[mnd].get(m, 0.0)
                # Se guarda como float redondeado para evitar comillas de strings pesados
                writer.writerow([MESES[m - 1], round(monto_mes, 2)])
            writer.writerow(["", ""])

            # --- SECCIÓN 2: GASTOS POR AÑO ---
            writer.writerow([f"GASTOS POR AÑO - DIVISA: {mnd}", ""])
            writer.writerow(["Año", "Monto"])
            # Se obtiene los años ordenados específicos que tengan registros en esta moneda
            anios_mnd = sorted(por_anio_moneda[mnd].keys()) if por_anio_moneda[mnd] else [anio_actual]
            for anio in anios_mnd:
                monto_anio = por_anio_moneda[mnd].get(anio, 0.0)
                writer.writerow([anio, round(monto_anio, 2)])
            writer.writerow(["", ""])

            # --- SECCIÓN 3: TOTAL GENERAL ---
            writer.writerow([f"TOTAL GENERAL ({mnd})", ""])
            total_abs = total_general_moneda.get(mnd, 0.0)
            writer.writerow(["Acumulado:", round(total_abs, 2)])
            
            # Separador estético de tres líneas vacías simétricas antes de pasar a la siguiente moneda
            writer.writerow(["", ""])
            writer.writerow(["---------------------------------------", "---------------------------------------"])
            writer.writerow(["", ""])

    return str(dest)