import os
import shutil
from pathlib import Path


def get_facturas_folder(custom_path = None):
    """Retorna la carpeta de destino para las facturas."""
    if custom_path and Path(custom_path).exists():
        return Path(custom_path)
    desktop = Path(os.path.expanduser("~")) / "Desktop"
    folder  = desktop / "facturas-gastos"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def build_filename(proveedor, fecha, monto, moneda):
    """Genera el nombre del archivo: Proveedor_DD-MM-YYYY_$Monto."""
    proveedor_clean = proveedor.strip().replace(" ", "_").replace("/", "-")
    fecha_clean = fecha.strip().replace("/", "-")
    monto_str = f"{monto:,.0f}".replace(",", ".")
    return f"{proveedor_clean}_{fecha_clean}_{moneda}{monto_str}.pdf"


def save_pdf(src_path, proveedor, fecha,
            monto, moneda, custom_folder = None):
    """
    Copia y renombra el PDF en la carpeta de facturas.
    Si ya existe un archivo con ese nombre agrega _2, _3, etc.
    Retorna el path final del archivo guardado.
    """
    folder   = get_facturas_folder(custom_folder)
    filename = build_filename(proveedor, fecha, monto, moneda)
    dest     = folder / filename

    # Evitar sobreescribir
    counter = 2
    while dest.exists():
        stem = Path(filename).stem
        dest = folder / f"{stem}_{counter}.pdf"
        counter += 1

    shutil.copy2(src_path, dest)
    return str(dest)