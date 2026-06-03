import flet as ft

# ── COLORES ──────────────────────────────────────────────────────────
PRIMARY      = "#1e3a5f"
ACCENT       = "#2ecc71"
BG           = "#f4f6f9"
CARD_BG      = "#ffffff"
TEXT_DARK    = "#1a1a2e"
TEXT_GRAY    = "#6c757d"
PENDING      = "#f39c12"
PAID         = "#27ae60"
ERROR        = "#dc3545"
BAR_COLOR    = "#2ecc71"
BAR_EDGE     = "#27ae60"
GRID_COLOR   = "#eeeeee"
LABEL_COLOR  = "#6c757d"
TITLE_COLOR  = "#1a1a2e"


STATUS_COLORS = {"pendiente": PENDING, "pagado": PAID}
STATUS_LABELS = {"pendiente": "Pendiente", "pagado": "Pagado"}
MONEDAS       = ["ARS", "USD", "EUR", "BRL"]


# ── COMPONENTES ──────────────────────────────────────────────────────
_icon = ft.Icon(ft.Icons.CIRCLE, size=18, color="#aaaaaa")
_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
_text = ft.Text("IA: Offline", size=11, weight=ft.FontWeight.BOLD, color="#aaaaaa")


_status_ui = ft.Container(
    content=ft.Column([
        ft.Row([_icon, _ring], alignment=ft.MainAxisAlignment.CENTER),
        _text,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
)

def get_llm_status_ui():
    """Esta función siempre devuelve el mismo objeto único."""
    return _status_ui

def set_llm_state(state: str):

    if state == "Loading":
        _icon.visible = False
        _ring.visible = True
        _text.value = "Cargando..."
        _text.color = "#aaaaaa"
    elif state == "Online":
        _icon.visible = True
        _ring.visible = False
        _icon.color = ACCENT
        _text.value = "IA: Online"
        _text.color = "#aaaaaa"
    else: # offline
        _icon.visible = True 
        _ring.visible = False
        _icon.color = LABEL_COLOR
        _text.value = "IA: Offline"
        _text.color = "#aaaaaa"

    _status_ui.update()

def show_snack(page: ft.Page, msg, color = ACCENT):
    snack = ft.SnackBar(
        content=ft.Container(
            content=ft.Text(msg, color="white", weight="bold", size=11),
            alignment=ft.alignment.Alignment(0, 0),
        ),
        bgcolor=color, elevation=0,
        behavior=ft.SnackBarBehavior.FLOATING,
        padding=0, duration=2500,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def card(content, padding=18):
    return ft.Container(
        content=content, bgcolor=CARD_BG, border_radius=12,
        padding=padding,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000012", offset=ft.Offset(0, 2)),
        margin=ft.margin.only(bottom=10),
    )


def section_title(text):
    return ft.Text(text, size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK)


def lbl(text):
    return ft.Text(text, size=12, color=TEXT_GRAY, weight=ft.FontWeight.W_500)


def tf(hint, value="", multiline=False, width=None, expand=False):
    return ft.TextField(
        hint_text=hint, value=value, multiline=multiline,
        min_lines=4 if multiline else 1,
        max_lines=10 if multiline else 1,
        border_color="#dddddd", focused_border_color=ACCENT,
        border_radius=8, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        width=width, expand=expand,
    )


def btn_primary(text, on_click, icon=None, disabled=False):
    return ft.ElevatedButton(
        text=text, icon=icon, on_click=on_click, disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ACCENT, ft.ControlState.DISABLED: "#cccccc"},
            color={ft.ControlState.DEFAULT: "white",  ft.ControlState.DISABLED: "#999999"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=18, vertical=11),
        )
    )


def btn_outline(text, on_click, icon=None, color=PRIMARY):
    return ft.OutlinedButton(
        text=text, icon=icon, on_click=on_click,
        style=ft.ButtonStyle(
            side=ft.BorderSide(1.5, color),
            color=color,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
        )
    )


def status_badge(estado):
    color = STATUS_COLORS.get(estado, TEXT_GRAY)
    label = STATUS_LABELS.get(estado, estado)
    return ft.Container(
        content=ft.Text(label, size=11, color="white", weight=ft.FontWeight.BOLD),
        bgcolor=color, border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )