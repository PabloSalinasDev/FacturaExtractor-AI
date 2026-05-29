from db.database import get_conn
from datetime import datetime

def normalizar_fecha(fecha_str):
    """
    Toma un string de fecha del LLM en múltiples formatos posibles
    y lo devuelve estrictamente en formato 'DD-MM-YYYY'.
    Si no puede parsearlo, devuelve la fecha actual como fallback seguro o lanza un error.
    """
    if not fecha_str:
        return datetime.now().strftime("%d-%m-%Y")

    fecha_str = fecha_str.strip()
    
    # Intentar limpiar formatos comunes de texto que a veces meten los LLMs
    # Formatos numéricos posibles a probar
    formatos = [
        "%d-%m-%Y",  # 20-05-2026 (El ideal)
        "%d/%m/%Y",  # 20/05/2026
        "%Y-%m-%d",  # 2026-05-20 (Formato ISO)
        "%Y/%m/%d",  # 2026/05/20
    ]
    
    for formato in formatos:
        try:
            # datetime.strptime toma el string y el formato que tiene
            objeto_fecha = datetime.strptime(fecha_str, formato)
            # Si tiene éxito, lo exportamos forzadamente a DD-MM-YYYY usando strftime
            return objeto_fecha.strftime("%d-%m-%Y")
        except ValueError:
            continue
            
    # Si los formatos numéricos estándar fallan, se puede intentar un regex rápido
    # para capturar si envió algo intermedio o con años de 2 dígitos (ej: 20-05-26)
    try:
        # Intento de parsear año de 2 dígitos DD-MM-YY o DD/MM/YY
        for formato_corto in ["%d-%m-%y", "%d/%m/%y"]:
            try:
                objeto_fecha = datetime.strptime(fecha_str, formato_corto)
                return objeto_fecha.strftime("%d-%m-%Y")
            except ValueError:
                continue
    except Exception:
        pass

    # Fallback: Si el LLM alucinó por completo (ej: "No especifica"),
    # devolvemos la fecha de hoy para no romper la base de datos, o una fecha por defecto.
    return datetime.now().strftime("%d-%m-%Y")

def save_factura(proveedor, fecha, monto, moneda, fuente, archivo=None):
    # NORMALIZACIÓN OBLIGATORIA ANTES DE ESCRIBIR EN LA BD
    fecha_limpia = normalizar_fecha(fecha)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO facturas (proveedor, fecha, monto, moneda, fuente, archivo) VALUES (?,?,?,?,?,?)",
            (proveedor, fecha_limpia, monto, moneda, fuente, archivo)
        )
        conn.commit()
        return cur.lastrowid


def get_all_facturas(proveedor=None, fecha=None, estado=None, fuente=None):
    query  = "SELECT * FROM facturas WHERE 1=1"
    params = []
    if proveedor:
        query += " AND proveedor LIKE ?"
        params.append(f"%{proveedor}%")
    if fecha:
        query += " AND fecha LIKE ?"
        params.append(f"%{fecha}%")
    if estado and estado != "todos":
        query += " AND estado = ?"
        params.append(estado)
    if fuente and fuente != "todos":
        query += " AND fuente = ?"
        params.append(fuente)
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def update_estado(factura_id, estado):
    with get_conn() as conn:
        conn.execute("UPDATE facturas SET estado=? WHERE id=?", (estado, factura_id))
        conn.commit()


def delete_factura(factura_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM facturas WHERE id=?", (factura_id,))
        conn.commit()


def get_setting(key, default=""):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


def save_setting(key, value):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
        conn.commit()