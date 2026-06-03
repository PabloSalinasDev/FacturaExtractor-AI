import flet as ft
import threading
from pathlib import Path
import time
import logging

from db.crud              import save_factura, get_setting
from modules.reader       import extract_text
from modules.file_manager import save_pdf
from modules.llm_client   import extract_invoice_data
from views.state_manager        import AppState
from views.helpers        import (
    card, section_title, lbl, tf, btn_primary, btn_outline,
    show_snack, ACCENT, PRIMARY, TEXT_DARK, TEXT_GRAY, MONEDAS, ERROR
)

def build_extractor(page: ft.Page):
    state = {
        "pdf_path":   None,
        "fuente":     "PDF",
        "extracting": False,
    }

    result_area  = ft.Column(visible=False, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    tf_proveedor = tf("Nombre del proveedor")
    tf_fecha     = tf("DD-MM-YYYY")
    tf_monto     = tf("0.00")

    dd_moneda = ft.Dropdown(
        value="ARS",
        options=[ft.dropdown.Option(m) for m in MONEDAS],
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        width=120,
    )

    fuente_pdf_btn = ft.ElevatedButton(
        "Archivo PDF",
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: PRIMARY, ft.ControlState.DISABLED: "#cccccc"},
            color={ft.ControlState.DEFAULT: "white", ft.ControlState.DISABLED: "#999999"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        ), disabled=not AppState.is_ready()
    )
    fuente_mensaje_btn = ft.OutlinedButton(
        "Texto Mensaje",
        style=ft.ButtonStyle(
            side={ft.ControlState.DEFAULT: ft.BorderSide(1.5, PRIMARY), ft.ControlState.DISABLED: ft.BorderSide(1.5, "#999999")},
            color={ft.ControlState.DEFAULT: PRIMARY, ft.ControlState.DISABLED: "#999999"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        ), disabled=not AppState.is_ready()
    )

    def on_ready():
        fuente_pdf_btn.disabled = False
        fuente_mensaje_btn.disabled = False
        page.update()

    AppState.subscribe(on_ready)

    mensaje_area = ft.Column([
        lbl("Pegá el texto con los datos de la factura:"),
        tf("Pegá aquí el contenido del texto...", multiline=True, expand=True),
    ], visible=False, spacing=6, expand=True)

    pdf_info_row = ft.Row([
        ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#e74c3c", size=18),
        ft.Text("", size=12, color=TEXT_GRAY, expand=True,
                overflow=ft.TextOverflow.ELLIPSIS),
    ], visible=False, spacing=6)

    btn_analizar = btn_primary("Analizar con IA", None,
                                icon=ft.Icons.AUTO_AWESOME, disabled=True)

    def set_fuente_pdf(e):
        state["fuente"] = "PDF"
        result_area.visible  = False
        mensaje_area.visible   = False
        page.update()
        file_picker.pick_files(allowed_extensions=["pdf"], allow_multiple=False)

    def set_fuente_mensaje(e):
        state["fuente"]        = "Mensaje"
        state["pdf_path"]      = None
        pdf_info_row.visible   = False
        mensaje_area.visible     = True
        result_area.visible    = False
        btn_analizar.disabled  = False
        page.update()

    fuente_pdf_btn.on_click   = set_fuente_pdf
    fuente_mensaje_btn.on_click = set_fuente_mensaje

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            state["pdf_path"]              = path
            pdf_info_row.controls[1].value = Path(path).name
            pdf_info_row.visible           = True
            btn_analizar.disabled          = False
            result_area.visible            = False
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def do_analyze(e):
        if state["extracting"]:
            return

        state["extracting"]   = True
        btn_analizar.disabled = True
        result_area.visible   = False
        page.update()

        progress_state = {"stop": False, "current": 0.0}

        # ── DIALOG MODAL ─────────────────────────────────────────────
        pb_dlg  = ft.ProgressBar(width=380, height=6, color=ACCENT, border_radius=5, bgcolor="#eeeeee")
        lbl_dlg = ft.Text("Iniciando motor de IA...", size=13, color=TEXT_GRAY)

        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Column([
                ft.Row([
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color=ACCENT),
                    lbl_dlg,
                ], spacing=10),
                pb_dlg,
            ], spacing=12, tight=True),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

        def simulate_progress():
            step     = 0.005
            interval = 0.3
            while not progress_state["stop"]:
                if progress_state["current"] < 0.90:
                    progress_state["current"] += step
                    pb_dlg.value = min(progress_state["current"], 0.90)
                    try:
                        page.update()
                    except:
                        break
                time.sleep(interval)

        def run():
            try:
                lbl_dlg.value = "Analizando factura..."
                page.update()

                t = threading.Thread(target=simulate_progress, daemon=True)
                t.start()

                if state["fuente"] == "PDF":
                    text, _ = extract_text(state["pdf_path"])
                else:
                    text = mensaje_area.controls[1].value.strip()
                    if not text:
                        raise ValueError("El campo de texto está vacío.")

                data = extract_invoice_data(text)

                progress_state["stop"] = True
                pb_dlg.value           = 1.0
                lbl_dlg.value          = "Extracción completada"
                page.update()
                time.sleep(0.8)

                tf_proveedor.value = data.get("proveedor") or ""
                tf_fecha.value     = data.get("fecha")     or ""
                tf_monto.value     = str(data.get("monto") or "")
                moneda_det         = data.get("moneda")    or "ARS"
                dd_moneda.value    = moneda_det if moneda_det in MONEDAS else "ARS"

                dlg.open              = False
                result_area.visible   = True
                btn_analizar.disabled = False
                state["extracting"]   = False
                page.update()

            except Exception as ex:
                progress_state["stop"] = True
                dlg.open               = False
                btn_analizar.disabled  = False
                state["extracting"]    = False
                page.update()
                show_snack(page, f"Error: {ex}", ERROR)
                logging.error("Error: %s", ex)


        threading.Thread(target=run, daemon=True).start()

    btn_analizar.on_click = do_analyze

    def do_save(e):
        proveedor = tf_proveedor.value.strip()
        fecha     = tf_fecha.value.strip()
        moneda    = dd_moneda.value

        try:
            monto = float(tf_monto.value.strip().replace(",", "."))
        except ValueError:
            show_snack(page, "El monto debe ser un número válido.", ERROR)
            return

        if not proveedor or not fecha:
            show_snack(page, "Proveedor y fecha son obligatorios.", ERROR)
            return

        archivo_guardado = None
        if state["fuente"] == "PDF" and state["pdf_path"]:
            try:
                carpeta = get_setting("carpeta_destino") or None
                archivo_guardado = save_pdf(
                    state["pdf_path"], proveedor, fecha, monto, moneda, carpeta
                )
            except Exception as ex:
                show_snack(page, f"No se pudo copiar el PDF: {ex} | path: {state['pdf_path']}", ERROR)
                logging.warning("No se pudo copiar el PDF: %s | path:%s", ex, state["pdf_path"])
        save_factura(proveedor, fecha, monto, moneda, state["fuente"], archivo_guardado)
        show_snack(page, "Factura guardada correctamente")

        tf_proveedor.value             = ""
        tf_fecha.value                 = ""
        tf_monto.value                 = ""
        dd_moneda.value                = "ARS"
        result_area.visible            = False
        pdf_info_row.visible           = False
        mensaje_area.controls[1].value   = ""
        state["pdf_path"]              = None
        btn_analizar.disabled          = True
        page.update()

    result_area.controls = [
        card(ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ACCENT, size=18),
                ft.Text("Datos extraídos — revisá y corregí si es necesario",
                        size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ], spacing=8),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row([
                ft.Column([lbl("Proveedor"), tf_proveedor], expand=True),
                ft.Container(width=12),
                ft.Column([lbl("Fecha (DD-MM-YYYY)"), tf_fecha], expand=True),
            ]),
            ft.Row([
                ft.Column([lbl("Monto"), tf_monto], expand=True),
                ft.Container(width=12),
                ft.Column([lbl("Moneda"), dd_moneda]),
            ]),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row([
                btn_primary("Confirmar y guardar", do_save),
                ft.Container(width=8),
                btn_outline("Cancelar",
                            lambda e: setattr(result_area, "visible", False) or page.update()),
            ]),
        ], spacing=8)),
    ]

    return ft.Column([
        section_title("Extraer Factura"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Text("Seleccioná el origen de la factura",
                    size=14, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Row([fuente_pdf_btn, fuente_mensaje_btn], spacing=12),
            ft.Container(height=4),
            pdf_info_row,
            mensaje_area,
            ft.Container(height=4),
            btn_analizar,
            ft.Text("* Si la factura no tiene un formato estándar o es escaneada la IA podría tener algún error de reconocimiento de los datos.",
                    size=10, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
        ], spacing=8)),
        result_area,
    ], spacing=8)