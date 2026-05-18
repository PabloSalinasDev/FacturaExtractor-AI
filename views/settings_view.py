import flet as ft

from db.crud              import get_setting, save_setting
from modules.file_manager import get_facturas_folder
from views.helpers import (
    card, section_title, btn_outline, show_snack,
    ACCENT, PRIMARY, TEXT_GRAY,
)


def build_settings(page: ft.Page):
    carpeta_saved = get_setting("carpeta_destino")
    carpeta_lbl   = ft.Text(
        carpeta_saved or str(get_facturas_folder()),
        size=12, color=TEXT_GRAY,
        overflow=ft.TextOverflow.ELLIPSIS, expand=True,
    )

    def on_pick_folder(e: ft.FilePickerResultEvent):
        if e.path:
            save_setting("carpeta_destino", e.path)
            carpeta_lbl.value = e.path
            page.update()
            show_snack(page, "Carpeta guardada")

    folder_picker = ft.FilePicker(on_result=on_pick_folder)
    page.overlay.append(folder_picker)

    return ft.Column([
        section_title("Configuración"),
        ft.Divider(height=1, color="#eeeeee"),
        card(ft.Column([
            ft.Text("Carpeta de destino para PDFs",
                    size=14, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Divider(height=1, color="#f0f0f0"),
            ft.Text(
                "Los PDFs de facturas se guardarán automáticamente en esta carpeta "
                "al confirmar los datos extraídos.",
                size=12, color=TEXT_GRAY,
            ),
            ft.Container(height=4),
            ft.Row([
                ft.Icon(ft.Icons.FOLDER_OUTLINED, color=PRIMARY, size=20),
                carpeta_lbl,
                btn_outline("Cambiar", lambda e: folder_picker.get_directory_path(),
                            icon=ft.Icons.FOLDER_OPEN),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        ], spacing=8)),
    ], spacing=8)