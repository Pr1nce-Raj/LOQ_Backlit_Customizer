import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray

def create_tray_image(width=64, height=64, active=True):
    """Generate a crisp, modern Lenovo LOQ keyboard backlight tray icon."""
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Background rounded badge
    bg_color = (18, 18, 24, 255)
    border_color = (0, 180, 216, 255) if active else (80, 80, 90, 255)
    draw.rounded_rectangle([4, 4, width - 4, height - 4], radius=12, fill=bg_color, outline=border_color, width=3)

    # Keyboard body representation
    kb_top = 16
    kb_bottom = 48
    kb_left = 12
    kb_right = width - 12
    draw.rounded_rectangle([kb_left, kb_top, kb_right, kb_bottom], radius=4, fill=(30, 32, 40, 255))

    # Keyboard key grid (3 rows)
    glow = (0, 220, 255, 255) if active else (100, 100, 110, 255)
    key_size = 5
    for row_idx, y in enumerate([21, 29, 37]):
        cols = 5 if row_idx < 2 else 4
        spacing = (kb_right - kb_left - (cols * key_size)) // (cols + 1)
        for col_idx in range(cols):
            x = kb_left + spacing + col_idx * (key_size + spacing)
            if row_idx == 2 and col_idx == 1:
                # Spacebar
                draw.rectangle([x, y, x + (key_size * 2) + spacing, y + key_size], fill=glow)
                break
            else:
                draw.rectangle([x, y, x + key_size, y + key_size], fill=glow)

    return image

class SystemTrayManager:
    """Manages system tray icon, notifications, and context menu."""

    def __init__(
        self,
        on_show_ui: Callable[[], None],
        on_set_mode: Callable[[str], None],
        on_toggle_power_saving: Callable[[], None],
        on_exit: Callable[[], None],
        get_current_mode: Callable[[], str],
        is_power_saving_enabled: Callable[[], bool],
    ):
        self.on_show_ui = on_show_ui
        self.on_set_mode = on_set_mode
        self.on_toggle_power_saving = on_toggle_power_saving
        self.on_exit = on_exit
        self.get_current_mode = get_current_mode
        self.is_power_saving_enabled = is_power_saving_enabled

        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._icon = pystray.Icon(
            name="LenovoLOQBacklight",
            icon=create_tray_image(active=True),
            title="Lenovo LOQ Backlight Customizer",
            menu=self._build_menu()
        )
        self._thread = threading.Thread(target=self._icon.run, name="SystemTrayThread", daemon=True)
        self._thread.start()

    def update_status(self, mode: str, is_sleeping: bool):
        if not self._icon:
            return
        status = "Sleeping (Power Saving)" if is_sleeping else f"Active ({mode})"
        self._icon.title = f"Lenovo LOQ Backlight - {status}"
        # Update icon active state
        self._icon.icon = create_tray_image(active=not is_sleeping and mode != "Off")
        self._icon.menu = self._build_menu()

    def _build_menu(self):
        curr_mode = self.get_current_mode()
        ps_enabled = self.is_power_saving_enabled()

        def make_mode_item(m):
            def action(icon, item):
                self.on_set_mode(m)
            def is_checked(item):
                return m == self.get_current_mode()
            return pystray.MenuItem(m, action, checked=is_checked, radio=True)

        quick_modes = [
            make_mode_item("Breathing"),
            make_mode_item("Pulse"),
            make_mode_item("Wave"),
            make_mode_item("Solid High"),
            make_mode_item("Solid Low"),
            make_mode_item("Off"),
        ]

        def open_dash(icon, item):
            self.on_show_ui()

        def toggle_ps(icon, item):
            self.on_toggle_power_saving()

        def exit_action(icon, item):
            self.on_exit()

        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", open_dash, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Lighting Mode", pystray.Menu(*quick_modes)),
            pystray.MenuItem(
                "Power Saving (30s Idle)",
                toggle_ps,
                checked=lambda item: self.is_power_saving_enabled()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Application", exit_action)
        )
        return menu

    def stop(self):
        if self._icon:
            try:
                self._icon.visible = False
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
