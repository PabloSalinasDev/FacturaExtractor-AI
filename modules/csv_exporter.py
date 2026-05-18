import csv
import os
from pathlib import Path
from datetime import datetime


def export_to_csv(facturas, custom_path = None):
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