import flet as ft
from pathlib import Path

from db.crud import get_all_facturas, update_estado, delete_factura
from modules.csv_exporter import export_to_csv
from views.helpers import (
    card, section_title, btn_outline, show_snack, status_badge,
    ACCENT, PRIMARY, TEXT_DARK, TEXT_GRAY, PENDING, CARD_BG,
)


def build_history(page: ft.Page):
    list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    tf_search = ft.TextField(
        hint_text="Buscar por proveedor...",
        prefix_icon=ft.Icons.SEARCH,
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        expand=True,
    )
    tf_fecha_f = ft.TextField(
        hint_text="Fecha (MM-YYYY)",
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        width=160,
    )
    dd_estado_f = ft.Dropdown(
        value="todos",
        options=[
            ft.dropdown.Option("todos",     "Todos"),
            ft.dropdown.Option("pendiente", "Pendiente"),
            ft.dropdown.Option("pagado",    "Pagado"),
        ],
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        width=140,
    )
    dd_fuente_f = ft.Dropdown(
        value="todos",
        options=[
            ft.dropdown.Option("todos", "Todos"),
            ft.dropdown.Option("PDF",   "PDF"),
            ft.dropdown.Option("Mensaje", "Mensaje"),
        ],
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        width=130,
    )

    def build_rows(proveedor="", fecha="", estado="todos", fuente="todos"):
        list_col.controls.clear()
        rows = get_all_facturas(
            proveedor or None, fecha or None, estado, fuente
        )

        if not rows:
            list_col.controls.append(ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=100, color="#cccccc"),
                    ft.Text("Sin facturas registradas", size=20, color=TEXT_GRAY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center, padding=40,
            ))
            page.update()
            return

        for row in rows:
            rid, prv, fch, mnt, mon, est, fnt, arch, created = row

            def make_delete(fid, nombre):
                def do_delete(e):
                    def confirm(e):
                        dlg.open = False
                        page.update()
                        delete_factura(fid)
                        build_rows(tf_search.value, tf_fecha_f.value,
                                    dd_estado_f.value, dd_fuente_f.value)

                    def cancel(e):
                        dlg.open = False
                        page.update()

                    dlg = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Confirmar eliminación",
                                        weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        content=ft.Text(
                            f"¿Estás seguro que querés eliminar la factura de {nombre}?\n"
                            "Esta acción no se puede deshacer.",
                            size=13, color=TEXT_GRAY,
                        ),
                        actions=[
                            ft.TextButton("Cancelar", on_click=cancel,
                                            style=ft.ButtonStyle(color=TEXT_GRAY)),
                            ft.ElevatedButton(
                                "Eliminar", on_click=confirm,
                                style=ft.ButtonStyle(
                                    bgcolor={ft.ControlState.DEFAULT: "#dc3545"},
                                    color={ft.ControlState.DEFAULT: "white"},
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.overlay.append(dlg)
                    dlg.open = True
                    page.update()

                return do_delete

            def make_status_change(fid, current):
                def do_change(e):
                    new = "pagado" if current == "pendiente" else "pendiente"
                    update_estado(fid, new)
                    build_rows(tf_search.value, tf_fecha_f.value,
                                dd_estado_f.value, dd_fuente_f.value)
                return do_change

            fuente_icon  = ft.Icons.PICTURE_AS_PDF if fnt == "PDF" else ft.Icons.EMAIL_OUTLINED
            fuente_color = "#e74c3c" if fnt == "PDF" else PRIMARY

            list_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(fuente_icon, color=fuente_color, size=20),
                        ft.Column([
                            ft.Text(prv, size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(f"{fch}  ·  {mon} {mnt:,.2f}  ·  {fnt}",
                                    size=11, color=TEXT_GRAY),
                        ], expand=True, spacing=2),
                        status_badge(est),
                        ft.Container(width=4),
                        ft.IconButton(ft.Icons.SWAP_HORIZ,
                                        tooltip="Cambiar estado",
                                        icon_size=18,
                                        on_click=make_status_change(rid, est),
                                        icon_color=TEXT_GRAY),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE,
                                        tooltip="Eliminar",
                                        icon_size=18,
                                        on_click=make_delete(rid, prv),
                                        icon_color="#dc3545"),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    bgcolor=CARD_BG, border_radius=10,
                    padding=ft.padding.symmetric(12, 14),
                    shadow=ft.BoxShadow(blur_radius=4, color="#00000010",
                                        offset=ft.Offset(0, 1)),
                )
            )
        page.update()

    def on_filter(e):
        build_rows(tf_search.value, tf_fecha_f.value,
                    dd_estado_f.value, dd_fuente_f.value)

    tf_search.on_change   = on_filter
    tf_fecha_f.on_change  = on_filter
    dd_estado_f.on_change = on_filter
    dd_fuente_f.on_change = on_filter

    def do_export(e):
        rows = get_all_facturas(
            tf_search.value or None, tf_fecha_f.value or None,
            dd_estado_f.value, dd_fuente_f.value,
        )
        if not rows:
            show_snack(page, "No hay datos para exportar.", PENDING)
            return
        path = export_to_csv(rows)
        show_snack(page, f"Exportado: {Path(path).name}")

    build_rows()

    return ft.Column([
        section_title("Historial de Facturas"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Row([
                tf_search,
                ft.Container(width=8),
                tf_fecha_f,
                ft.Container(width=8),
                dd_estado_f,
                ft.Container(width=8),
                dd_fuente_f,
                ft.Container(width=8),
                btn_outline("Exportar CSV", do_export,
                            icon=ft.Icons.DOWNLOAD, color=PRIMARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=0), padding=12),
        ft.Container(height=14),
        list_col,
    ], spacing=6)