import webbrowser

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.utils import platform

WHATSAPP_URL = "https://wa.me/6281939186103"

SCREEN_ORDER = ["beranda", "paket", "pesan"]

if platform not in ("android", "ios"):
    Window.size = (390, 800)

BG_DARK = (0x0B / 255, 0x12 / 255, 0x20 / 255, 1)          # --bg / #0B1220
SURFACE = (0x11 / 255, 0x1A / 255, 0x2C / 255, 1)          # kartu
BORDER = (0x22 / 255, 0x30 / 255, 0x4F / 255, 1)           # --border
GOLD = (0xFD / 255, 0xB8 / 255, 0x13 / 255, 1)             # --accent-gold
ORANGE = (0xFF / 255, 0x6B / 255, 0x4A / 255, 1)           # --accent-orange
TEXT_MAIN = (0xF3 / 255, 0xF5 / 255, 0xF9 / 255, 1)
TEXT_MUTED = (0x9A / 255, 0xA6 / 255, 0xC0 / 255, 1)
DANGER = (0xFF / 255, 0x6B / 255, 0x6B / 255, 1)

GOLD_HEX = "FDB813"
MUTED_HEX = "9AA6C0"

Window.clearcolor = BG_DARK

BIAYA_INSTALASI = 150000

PAKET_DATA = {
    "cahaya": {"nama": "Cahaya", "sub": "Untuk kebutuhan harian", "speed": "10 Mbps",
               "harga": 100000, "fitur": ["Cocok untuk 1–3 perangkat",
                                           "Streaming & browsing lancar",
                                           "Ideal untuk rumah kecil"]},
    "terang": {"nama": "Terang", "sub": "Untuk keluarga aktif", "speed": "20 Mbps",
               "harga": 200000, "fitur": ["Cocok untuk 4–8 perangkat",
                                           "Video call & kerja dari rumah",
                                           "Gaming ringan tanpa lag"],
               "badge": "Paling laris"},
    "terik": {"nama": "Terik", "sub": "Untuk bisnis & power user", "speed": "50 Mbps",
              "harga": 350000, "fitur": ["Cocok untuk 8+ perangkat",
                                          "Upload & download berat",
                                          "Prioritas dukungan teknis"]},
}


def format_rupiah(n: int) -> str:
    return "Rp" + f"{n:,}".replace(",", ".")


class RoundedCard(BoxLayout):
    def __init__(self, bg=SURFACE, border=BORDER, radius=16, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        with self.canvas.before:
            Color(*bg)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                              radius=[self._radius])
            Color(*border)
            self._border_line = Line(rounded_rectangle=(self.x, self.y, self.width,
                                                          self.height, self._radius),
                                      width=1.1)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_line.rounded_rectangle = (self.x, self.y, self.width,
                                                 self.height, self._radius)


class SectionTitle(BoxLayout):
    def __init__(self, eyebrow, title, lead=None, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                          spacing=dp(6), **kwargs)
        self.bind(minimum_height=self.setter("height"))

        eb = Label(text=eyebrow.upper(), color=GOLD, bold=True, font_size=dp(13),
                   size_hint_y=None, height=dp(22))
        self.add_widget(eb)

        ttl = Label(text=title, color=TEXT_MAIN, bold=True, font_size=dp(24),
                    size_hint_y=None, height=dp(34))
        self.add_widget(ttl)

        if lead:
            ld = Label(text=lead, color=TEXT_MUTED, font_size=dp(14),
                       size_hint_y=None, halign="center", valign="top")
            ld.bind(width=lambda *_: setattr(ld, "text_size", (ld.width, None)))
            ld.bind(texture_size=lambda *_: setattr(ld, "height", ld.texture_size[1]))
            self.add_widget(ld)


class SuryaNetApp(App):
    total_text = StringProperty(format_rupiah(PAKET_DATA["cahaya"]["harga"] + BIAYA_INSTALASI))

    def build(self):
        self.title = "Surya Net — Internet Cepat & Stabil"
        self.selected_paket = "cahaya"
        self.tab_buttons = {}

        Window.bind(on_keyboard=self._on_keyboard)

        root = FloatLayout()

        main_col = BoxLayout(orientation="vertical", size_hint=(1, 1))
        main_col.add_widget(self._build_appbar())

        self.sm = ScreenManager(transition=SlideTransition(duration=0.18))
        self.sm.add_widget(self._make_screen(
            "beranda", [self._build_hero(), self._build_footer()]))
        self.sm.add_widget(self._make_screen("paket", [self._build_paket()]))
        self.sm.add_widget(self._make_screen("pesan", [self._build_form()]))

        main_col.add_widget(self.sm)
        main_col.add_widget(self._build_bottom_nav())

        root.add_widget(main_col)
        root.add_widget(self._build_fab())
        return root

    def _make_screen(self, name, widgets):
        screen = Screen(name=name)
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(28),
                             padding=(dp(16), dp(20), dp(16), dp(30)))
        content.bind(minimum_height=content.setter("height"))
        for w in widgets:
            content.add_widget(w)
        scroll.add_widget(content)
        screen.add_widget(scroll)
        return screen

    def _goto(self, name):
        """Pindah tab/halaman dengan animasi slide, setara ganti section di versi web.
        Bottom nav memanggil ini setiap kali salah satu tab dipencet, jadi bisa
        langsung meloncat ke halaman berikutnya (atau sebelumnya) kapan saja."""
        if self.sm.current != name:
            cur_idx = SCREEN_ORDER.index(self.sm.current)
            new_idx = SCREEN_ORDER.index(name)
            self.sm.transition.direction = "left" if new_idx > cur_idx else "right"
            self.sm.current = name
        self._set_active_tab(name)

    def _go_back(self):
        """Mundur satu halaman sesuai urutan tab (Pesan → Paket → Beranda)."""
        idx = SCREEN_ORDER.index(self.sm.current)
        if idx > 0:
            self._goto(SCREEN_ORDER[idx - 1])

    def _on_keyboard(self, window, key, *args):
        """Tangkap tombol back fisik Android / Esc di desktop."""
        if key == 27:
            if self.sm.current != "beranda":
                self._go_back()
                return True
            return False
        return False

    def _build_appbar(self):
        appbar = BoxLayout(size_hint_y=None, height=dp(56), padding=(dp(6), 0),
                           spacing=dp(6))
        with appbar.canvas.before:
            Color(*SURFACE)
            self._appbar_bg = RoundedRectangle(pos=appbar.pos, size=appbar.size, radius=[0])
            Color(*BORDER)
            self._appbar_line = Line(points=[appbar.x, appbar.y, appbar.right, appbar.y],
                                     width=1)
        def upd(*_):
            self._appbar_bg.pos = appbar.pos
            self._appbar_bg.size = appbar.size
            self._appbar_line.points = [appbar.x, appbar.y, appbar.right, appbar.y]
        appbar.bind(pos=upd, size=upd)

        self.back_btn = Button(text="\u2039", font_size=dp(26), bold=True,
                               color=TEXT_MAIN, size_hint=(None, 1), width=dp(40),
                               background_normal="", background_color=(0, 0, 0, 0),
                               opacity=0, disabled=True)
        self.back_btn.bind(on_release=lambda *_: self._go_back())
        appbar.add_widget(self.back_btn)

        brand = Label(text="[b]Surya[color=fdb813]Net[/color][/b]", markup=True,
                      color=TEXT_MAIN, font_size=dp(18), halign="left", valign="middle",
                      padding=(dp(4), 0))
        brand.bind(size=lambda *_: setattr(brand, "text_size", brand.size))
        appbar.add_widget(brand)
        return appbar

    def _build_bottom_nav(self):
        nav = BoxLayout(size_hint_y=None, height=dp(64), padding=(0, dp(6)))
        with nav.canvas.before:
            Color(*SURFACE)
            self._nav_bg = RoundedRectangle(pos=nav.pos, size=nav.size, radius=[0])
            Color(*BORDER)
            self._nav_line = Line(points=[nav.x, nav.top, nav.right, nav.top], width=1)
        def upd(*_):
            self._nav_bg.pos = nav.pos
            self._nav_bg.size = nav.size
            self._nav_line.points = [nav.x, nav.top, nav.right, nav.top]
        nav.bind(pos=upd, size=upd)

        tabs = [("\U0001F3E0", "Beranda", "beranda"),
                ("\u25A6", "Paket", "paket"),
                ("\u2709", "Pesan", "pesan")]

        for icon, label, key in tabs:
            btn = Button(markup=True, halign="center", valign="middle",
                        background_normal="", background_color=(0, 0, 0, 0),
                        background_down="")
            btn.bind(size=lambda b, *_: setattr(b, "text_size", b.size))
            btn.bind(on_release=lambda _b, k=key: self._goto(k))
            self.tab_buttons[key] = (btn, icon, label)
            nav.add_widget(btn)

        self._set_active_tab("beranda")
        return nav

    def _set_active_tab(self, key):
        for k, (btn, icon, label) in self.tab_buttons.items():
            active = (k == key)
            color_hex = GOLD_HEX if active else MUTED_HEX
            b_open, b_close = ("[b]", "[/b]") if active else ("", "")
            btn.text = (f"[color={color_hex}]{icon}[/color]\n"
                       f"[size=11]{b_open}[color={color_hex}]{label}[/color]{b_close}[/size]")

        if hasattr(self, "back_btn"):
            show_back = SCREEN_ORDER.index(key) > 0
            self.back_btn.opacity = 1 if show_back else 0
            self.back_btn.disabled = not show_back

    def _build_fab(self):
        fab = Button(text="\U0001F4AC", font_size=dp(22),
                    size_hint=(None, None), size=(dp(56), dp(56)),
                    pos_hint={"right": 0.94, "y": 0.115},
                    background_normal="", background_color=(0, 0, 0, 0),
                    color=(1, 1, 1, 1))
        with fab.canvas.before:
            Color(0.13, 0.72, 0.35, 1)  # hijau WhatsApp
            self._fab_circle = Ellipse(pos=fab.pos, size=fab.size)
        fab.bind(pos=lambda *_: setattr(self._fab_circle, "pos", fab.pos))
        fab.bind(size=lambda *_: setattr(self._fab_circle, "size", fab.size))
        fab.bind(on_release=lambda *_: self._open_whatsapp())
        return fab

    def _open_whatsapp(self):
        """Setara dengan tombol .fab (link WhatsApp) di versi web."""
        try:
            if platform == "android":
                from jnius import autoclass, cast
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(WHATSAPP_URL))
                currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
                currentActivity.startActivity(intent)
            else:
                webbrowser.open(WHATSAPP_URL)
        except Exception:
            webbrowser.open(WHATSAPP_URL)

    def _build_hero(self):
        hero = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14),
                          padding=(0, dp(20), 0, dp(10)))
        hero.bind(minimum_height=hero.setter("height"))

        eyebrow = Label(text="ISP LOKAL • RUMAH & BISNIS", color=GOLD, bold=True,
                        font_size=dp(12), size_hint_y=None, height=dp(20))
        hero.add_widget(eyebrow)

        h1 = Label(text="Internet yang menyala [color=fdb813]secepat mentari terbit[/color]",
                   markup=True, color=TEXT_MAIN, bold=True, font_size=dp(28),
                   size_hint_y=None, halign="left", valign="top")
        h1.bind(width=lambda *_: setattr(h1, "text_size", (h1.width, None)))
        h1.bind(texture_size=lambda *_: setattr(h1, "height", h1.texture_size[1]))
        hero.add_widget(h1)

        lead = Label(
            text="Surya Net memasang jaringan fiber stabil ke rumah dan usaha Anda "
                 "— tanpa lemot saat jam sibuk, tanpa drama saat hujan.",
            color=TEXT_MUTED, font_size=dp(14), size_hint_y=None, halign="left", valign="top")
        lead.bind(width=lambda *_: setattr(lead, "text_size", (lead.width, None)))
        lead.bind(texture_size=lambda *_: setattr(lead, "height", lead.texture_size[1]))
        hero.add_widget(lead)

        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_primary = self._primary_button("Lihat Paket")
        btn_primary.bind(on_release=lambda *_: self._goto("paket"))
        btn_ghost = self._ghost_button("Pesan Sekarang")
        btn_ghost.bind(on_release=lambda *_: self._goto("pesan"))
        actions.add_widget(btn_primary)
        actions.add_widget(btn_ghost)
        hero.add_widget(actions)

        stats = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        for num, lbl in [("99.9%", "waktu aktif jaringan"), ("< 48 jam", "rata-rata instalasi"),
                         ("24/7", "dukungan teknisi")]:
            stat = BoxLayout(orientation="vertical")
            n = Label(text=num, color=GOLD, bold=True, font_size=dp(16))
            l = Label(text=lbl, color=TEXT_MUTED, font_size=dp(10))
            stat.add_widget(n)
            stat.add_widget(l)
            stats.add_widget(stat)
        hero.add_widget(stats)

        return hero

    def _primary_button(self, text):
        btn = Button(text=text, bold=True, color=(0.05, 0.05, 0.05, 1),
                    background_normal="", background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            Color(*GOLD)
            rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
        btn.bind(pos=lambda *_: setattr(rect, "pos", btn.pos))
        btn.bind(size=lambda *_: setattr(rect, "size", btn.size))
        return btn

    def _ghost_button(self, text):
        btn = Button(text=text, bold=True, color=TEXT_MAIN,
                    background_normal="", background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            Color(*BORDER)
            line = Line(rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, dp(10)), width=1.2)
        def upd(*_):
            line.rounded_rectangle = (btn.x, btn.y, btn.width, btn.height, dp(10))
        btn.bind(pos=upd, size=upd)
        return btn

    def _build_paket(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(18))
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(SectionTitle(
            "Pilih intensitas Anda", "Paket Layanan",
            "Tiga tingkat kecepatan, dinamai dari cahaya mentari — semakin terik, semakin cepat."))

        cards = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14))
        cards.bind(minimum_height=cards.setter("height"))

        self.plan_cards = {}
        for key, data in PAKET_DATA.items():
            featured = data.get("badge") is not None
            border_color = GOLD if featured else BORDER
            card = RoundedCard(bg=SURFACE, border=border_color, orientation="vertical",
                               size_hint_y=None, height=dp(260), padding=dp(16), spacing=dp(6))
            self.plan_cards[key] = card

            if featured:
                card.add_widget(Label(text=data["badge"], color=(0.05, 0.05, 0.05, 1),
                                      bold=True, font_size=dp(11), size_hint_y=None, height=dp(20)))

            card.add_widget(Label(text=data["nama"], color=GOLD, bold=True, font_size=dp(13),
                                  size_hint_y=None, height=dp(20), halign="left"))
            card.add_widget(Label(text=data["sub"], color=TEXT_MUTED, font_size=dp(12),
                                  size_hint_y=None, height=dp(18), halign="left"))
            card.add_widget(Label(text=f"[b]{data['speed'].split()[0]}[/b] Mbps", markup=True,
                                  color=TEXT_MAIN, font_size=dp(22), size_hint_y=None,
                                  height=dp(34), halign="left"))
            card.add_widget(Label(text=f"{format_rupiah(data['harga'])}/bulan",
                                  color=TEXT_MAIN, bold=True, font_size=dp(16),
                                  size_hint_y=None, height=dp(24), halign="left"))

            feat_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
            for f in data["fitur"]:
                feat_box.add_widget(Label(text=f"• {f}", color=TEXT_MUTED, font_size=dp(11),
                                          halign="left", valign="middle"))
            card.add_widget(feat_box)

            pilih_btn = self._primary_button(f"Pilih {data['nama']}") if featured \
                else self._ghost_button(f"Pilih {data['nama']}")
            pilih_btn.size_hint_y = None
            pilih_btn.height = dp(40)
            pilih_btn.bind(on_release=lambda _b, k=key: self._select_plan(k))
            card.add_widget(pilih_btn)

            for child in card.children:
                if isinstance(child, Label):
                    child.bind(size=lambda lbl, *_: setattr(lbl, "text_size", lbl.size))

            cards.add_widget(card)

        box.add_widget(cards)

        info = Label(
            text=f"Biaya instalasi/pemasangan awal sebesar [b]{format_rupiah(BIAYA_INSTALASI)}[/b] "
                 "(dibayar satu kali, di luar iuran bulanan).",
            markup=True, color=TEXT_MUTED, font_size=dp(12.5),
            size_hint_y=None, halign="center", valign="top")
        info.bind(width=lambda *_: setattr(info, "text_size", (info.width, None)))
        info.bind(texture_size=lambda *_: setattr(info, "height", info.texture_size[1]))
        box.add_widget(info)
        return box

    def _select_plan(self, key):
        """Setara dengan listener [data-select-plan] di script.js"""
        self.selected_paket = key
        if hasattr(self, "paket_spinner"):
            self.paket_spinner.text = self._spinner_label(key)
        self._hitung_total()
        self._goto("pesan")
        if hasattr(self, "nama_input"):
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self.nama_input, "focus", True), 0.4)

    def _spinner_label(self, key):
        d = PAKET_DATA[key]
        return f"{d['nama']} — {d['speed']} — {format_rupiah(d['harga'])}/bulan"

    def _build_form(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14))
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(SectionTitle("Form pemesanan", "Siap terhubung?",
                                    "Lengkapi data di bawah, tim kami akan menghubungi Anda "
                                    "untuk jadwal survei."))

        form_card = RoundedCard(orientation="vertical", size_hint_y=None,
                                padding=dp(16), spacing=dp(10))
        form_card.bind(minimum_height=form_card.setter("height"))

        
        form_card.add_widget(self._field_label("Nama Lengkap"))
        self.nama_input = TextInput(hint_text="Contoh: Siti Rahayu", multiline=False,
                                    size_hint_y=None, height=dp(42),
                                    background_color=(1, 1, 1, 0.06), foreground_color=TEXT_MAIN,
                                    cursor_color=GOLD, padding=(dp(10), dp(10)))
        form_card.add_widget(self.nama_input)
        self.nama_error = Label(text="Mohon isi nama lengkap Anda.", color=DANGER,
                                font_size=dp(11), size_hint_y=None, height=0, opacity=0,
                                halign="left")
        self.nama_error.bind(width=lambda *_: setattr(self.nama_error, "text_size",
                                                       (self.nama_error.width, None)))
        form_card.add_widget(self.nama_error)

        
        form_card.add_widget(self._field_label("Alamat Pemasangan"))
        self.alamat_input = TextInput(hint_text="Jalan, nomor rumah, RT/RW, kelurahan",
                                      multiline=True, size_hint_y=None, height=dp(80),
                                      background_color=(1, 1, 1, 0.06), foreground_color=TEXT_MAIN,
                                      cursor_color=GOLD, padding=(dp(10), dp(10)))
        form_card.add_widget(self.alamat_input)
        self.alamat_error = Label(text="Mohon isi alamat pemasangan.", color=DANGER,
                                  font_size=dp(11), size_hint_y=None, height=0, opacity=0,
                                  halign="left")
        self.alamat_error.bind(width=lambda *_: setattr(self.alamat_error, "text_size",
                                                         (self.alamat_error.width, None)))
        form_card.add_widget(self.alamat_error)

        
        form_card.add_widget(self._field_label("Pilih Paket"))
        spinner_values = [self._spinner_label(k) for k in PAKET_DATA]
        self.paket_spinner = Spinner(text=self._spinner_label("cahaya"), values=spinner_values,
                                     size_hint_y=None, height=dp(42),
                                     background_color=SURFACE, color=TEXT_MAIN)
        self.paket_spinner.bind(text=self._on_spinner_change)
        form_card.add_widget(self.paket_spinner)

        
        total_box = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(12), spacing=dp(10))
        with total_box.canvas.before:
            Color(*BG_DARK)
            trect = RoundedRectangle(pos=total_box.pos, size=total_box.size, radius=[dp(10)])
        total_box.bind(pos=lambda *_: setattr(trect, "pos", total_box.pos))
        total_box.bind(size=lambda *_: setattr(trect, "size", total_box.size))

        total_left = BoxLayout(orientation="vertical")
        total_left.add_widget(Label(text="Perkiraan biaya awal", color=TEXT_MAIN, bold=True,
                                    font_size=dp(12), halign="left"))
        total_left.add_widget(Label(text="Iuran bulan pertama + instalasi", color=TEXT_MUTED,
                                    font_size=dp(10), halign="left"))
        total_box.add_widget(total_left)

        self.total_label = Label(text=self.total_text, color=GOLD, bold=True, font_size=dp(18),
                                 size_hint_x=None, width=dp(120), halign="right")
        total_box.add_widget(self.total_label)
        form_card.add_widget(total_box)

        submit_btn = self._primary_button("Kirim Pesanan")
        submit_btn.size_hint_y = None
        submit_btn.height = dp(46)
        submit_btn.bind(on_release=lambda *_: self._submit_form())
        form_card.add_widget(submit_btn)

        box.add_widget(form_card)
        self._hitung_total()
        return box

    def _field_label(self, text):
        return Label(text=text, color=TEXT_MAIN, bold=True, font_size=dp(12.5),
                    size_hint_y=None, height=dp(20), halign="left",
                    text_size=(Window.width - dp(64), None))

    def _on_spinner_change(self, spinner, text):
        for key, d in PAKET_DATA.items():
            if self._spinner_label(key) == text:
                self.selected_paket = key
                break
        self._hitung_total()

    def _hitung_total(self):
        """Setara dengan hitungTotal() di script.js"""
        harga = PAKET_DATA[self.selected_paket]["harga"]
        total = harga + BIAYA_INSTALASI
        self.total_text = format_rupiah(total)
        if hasattr(self, "total_label"):
            self.total_label.text = self.total_text

    def _show_field_error(self, error_label, show):
        if show:
            error_label.opacity = 1
            error_label.height = dp(18)
        else:
            error_label.opacity = 0
            error_label.height = 0

    def _submit_form(self):
        """Setara dengan submit handler formPesan di script.js"""
        nama = self.nama_input.text.strip()
        alamat = self.alamat_input.text.strip()

        valid = True
        self._show_field_error(self.nama_error, nama == "")
        if nama == "":
            valid = False
        self._show_field_error(self.alamat_error, alamat == "")
        if alamat == "":
            valid = False

        if not valid:
            return

        paket_nama = PAKET_DATA[self.selected_paket]["nama"]
        pesan = (f"Terima kasih, {nama}. Pesanan layanan {paket_nama} Anda sedang kami "
                f"proses. Tim Surya Net akan menghubungi Anda untuk jadwal survei.")
        self._show_alert(pesan)

        self.nama_input.text = ""
        self.alamat_input.text = ""
        self.selected_paket = "cahaya"
        self.paket_spinner.text = self._spinner_label("cahaya")
        self._hitung_total()

    def _show_alert(self, message):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        lbl = Label(text=message, color=TEXT_MAIN, font_size=dp(13), halign="left", valign="top")
        lbl.bind(width=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
        content.add_widget(lbl)
        close_btn = self._primary_button("Tutup")
        close_btn.size_hint_y = None
        close_btn.height = dp(42)
        content.add_widget(close_btn)

        popup = Popup(title="Pesanan Diterima", content=content, size_hint=(0.85, 0.4),
                      separator_color=GOLD, title_color=TEXT_MAIN,
                      background_color=SURFACE)
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _build_footer(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(120),
                        spacing=dp(4), padding=(0, dp(20), 0, 0))
        box.add_widget(Label(text="[b]Surya[color=fdb813]Net[/color][/b]", markup=True,
                             color=TEXT_MAIN, font_size=dp(16)))
        box.add_widget(Label(text="Internet cepat & stabil untuk rumah dan bisnis Anda.",
                             color=TEXT_MUTED, font_size=dp(11)))
        box.add_widget(Label(text="Kontak: 081939186103", color=GOLD, font_size=dp(11)))
        box.add_widget(Label(text="© 2026 Surya Net. Seluruh hak cipta dilindungi.",
                             color=TEXT_MUTED, font_size=dp(10)))
        return box


if __name__ == "__main__":
    SuryaNetApp().run()