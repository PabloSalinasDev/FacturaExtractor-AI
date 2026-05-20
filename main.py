import flet as ft
import time

from db.database          import init_db
from modules.llm_client   import model_exists, download_model
from views.helpers        import PRIMARY, ACCENT, BG, CARD_BG, TEXT_DARK, TEXT_GRAY
from views.extractor_view import build_extractor
from views.history_view   import build_history
from views.settings_view  import build_settings
from views.charts_view    import build_charts

def main(page: ft.Page):
    page.title             = "FacturaExtractor - Gestión de Facturas con IA"
    page.bgcolor           = BG
    page.theme_mode        = ft.ThemeMode.LIGHT
    page.window.maximized  = True
    page.window.width      = 1100
    page.window.height     = 760
    page.window.min_width  = 900
    page.window.min_height = 640

    init_db()

    page.theme = ft.Theme(
    navigation_rail_theme=ft.NavigationRailTheme(
        selected_label_text_style=ft.TextStyle(color=ACCENT),
        unselected_label_text_style=ft.TextStyle(color="#aaaaaa"),
    )
)
    # ── NAVEGACIÓN ───────────────────────────────────────────────────
    content_area = ft.Container(expand=True, padding=20, alignment=ft.alignment.top_left)

    def navigate(view):
        if view == "extractor":
            content_area.content = build_extractor(page)
        elif view == "history":
            content_area.content = build_history(page)
        elif view == "graficos":
            content_area.content = build_charts(page)
        elif view == "settings":
            content_area.content = build_settings(page)
        page.update()

    nav_rail = ft.NavigationRail(
        selected_index=0, expand=True,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=72, min_extended_width=160,
        bgcolor=PRIMARY, indicator_color=ACCENT,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, color="#aaaaaa"),
                selected_icon=ft.Icons.UPLOAD_FILE, label="Extraer"),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.LIST_ALT_OUTLINED, color="#aaaaaa"),
                selected_icon=ft.Icons.LIST_ALT, label="Historial"),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.BAR_CHART_OUTLINED, color="#aaaaaa"),
                selected_icon=ft.Icons.BAR_CHART, label="Gráficos"),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.SETTINGS_OUTLINED, color="#aaaaaa"),
                selected_icon=ft.Icons.SETTINGS, label="Config"),
        ],
        on_change=lambda e: navigate(
            ["extractor", "history", "graficos", "settings"][e.control.selected_index]
        ),
    )

    header = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=22, color="#cccccc"),
            ft.Text("FE", size=13, weight=ft.FontWeight.BOLD, color="#cccccc"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor=PRIMARY, padding=ft.padding.symmetric(8, 12), width=72,
    )

    def launch_main_app():
        page.controls.clear()
        navigate("extractor")
        page.add(ft.Row([
            ft.Column([header, nav_rail], spacing=0, width=72),
            ft.VerticalDivider(width=1, color="#eeeeee"),
            content_area,
        ], expand=True, spacing=0))
        page.update()

    # ── PANTALLA DE DESCARGA ─────────────────────────────────────────
    def show_download_screen():
        progress_bar = ft.ProgressBar(value=0, color=ACCENT, height=6, border_radius=5, bgcolor="#e0e0e0", width=420)
        pct_lbl      = ft.Text("0%", size=13, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
        size_lbl     = ft.Text("0 GB / 0.92 GB", size=12, color=TEXT_GRAY)
        status_lbl   = ft.Text("Preparando descarga...", size=12, color=TEXT_GRAY)

        btn_dl = ft.ElevatedButton(
            "Descargar modelo de IA (~0.92 GB)", icon=ft.Icons.DOWNLOAD,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT},
                color={ft.ControlState.DEFAULT: "white"},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            )
        )
        btn_skip = ft.TextButton("Omitir por ahora",
                                style=ft.ButtonStyle(color=TEXT_GRAY))

        progress_section = ft.Column([
            progress_bar,
            ft.Row([pct_lbl, size_lbl],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=420),
            status_lbl,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6, visible=False)

        def start_dl(e):
            btn_dl.visible           = False
            btn_skip.visible         = False
            progress_section.visible = True
            status_lbl.value         = "Descargando... esto puede tardar varios minutos."
            page.update()

            def on_progress(pct, d_gb, t_gb):
                progress_bar.value = pct
                pct_lbl.value      = f"{pct * 100:.1f}%"
                size_lbl.value     = f"{d_gb:.2f} GB / {t_gb:.2f} GB"
                page.update()

            def on_done():
                status_lbl.value = "Listo. Iniciando FacturaExtractor..."
                page.update()
                time.sleep(1)
                launch_main_app()

            def on_error(msg):
                status_lbl.value         = f"Error: {msg}"
                btn_dl.visible           = True
                btn_skip.visible         = True
                progress_section.visible = False
                page.update()

            download_model(on_progress, on_done, on_error)

        btn_dl.on_click   = start_dl
        btn_skip.on_click = lambda e: launch_main_app()

        page.add(ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=56, color="#cccccc"),
                ft.Text("FacturaExtractor", size=26,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Text("Gestión de Facturas con IA Local",
                        size=14, color=TEXT_GRAY),
                ft.Divider(height=20, color="transparent"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Configuración inicial", size=15,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(
                            "El tiempo de extracción depende del hardware de tu equipo.\n"
                            "Con GPU dedicada: ~8 segundos. Solo CPU: ~40 segundos.",
                            size=11, color=TEXT_GRAY, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Para funcionar offline necesitamos descargar el modelo de IA.\n"
                            "Esto ocurre una sola vez (~0.92 GB). Después no necesitás internet.",
                            size=12, color=TEXT_GRAY, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=10, color="transparent"),
                        progress_section,
                        btn_dl,
                        btn_skip,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    bgcolor=CARD_BG, border_radius=16, padding=30,
                    shadow=ft.BoxShadow(blur_radius=16, color="#00000015",
                                        offset=ft.Offset(0, 4)),
                    width=500,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            alignment=ft.alignment.center,
            expand=True,
        ))
        page.update()

    # ── ARRANQUE ─────────────────────────────────────────────────────
    if model_exists():
        launch_main_app()
    else:
        show_download_screen()

if __name__ == "__main__":
    ft.app(target=main)