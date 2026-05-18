from db.database import get_conn


def save_factura(proveedor, fecha, monto, moneda, fuente, archivo=None):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO facturas (proveedor, fecha, monto, moneda, fuente, archivo) VALUES (?,?,?,?,?,?)",
            (proveedor, fecha, monto, moneda, fuente, archivo)
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