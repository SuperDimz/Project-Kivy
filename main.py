import calendar as calendar_module
import json
import os
import uuid
from datetime import datetime, date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform

try:
    from plyer import notification as plyer_notification
except ImportError:
    plyer_notification = None

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

if platform not in ("android", "ios"):
    Window.size = (390, 800)

BG_COLOR = (0.06, 0.07, 0.09, 1)
CARD_COLOR = (0.10, 0.11, 0.14, 1)
ACCENT_COLOR = (0.42, 0.55, 1, 1)
DONE_COLOR = (0.30, 0.70, 0.49, 1)
TEXT_COLOR = (0.95, 0.95, 0.97, 1)
MUTED_COLOR = (0.55, 0.56, 0.61, 1)
DANGER_COLOR = (1, 0.42, 0.42, 1)

Window.clearcolor = BG_COLOR

DEADLINE_FORMAT = "%d-%m-%Y"
MONTH_NAMES_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
WEEKDAY_NAMES_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


def parse_deadline(deadline_str):
    """Ubah string 'dd-mm-yyyy' menjadi objek date. Kembalikan None kalau kosong/invalid."""
    if not deadline_str:
        return None
    try:
        return datetime.strptime(deadline_str, DEADLINE_FORMAT).date()
    except ValueError:
        return None


def format_deadline_label(deadline_str, done):
    """Kembalikan (teks, warna) untuk label deadline pada kartu tugas."""
    d = parse_deadline(deadline_str)
    if d is None:
        return "", MUTED_COLOR
    text = "Tenggat: " + d.strftime("%d %b %Y")
    if done:
        return text, MUTED_COLOR
    today = date.today()
    if d < today:
        return text + " (Terlambat)", DANGER_COLOR
    if d == today:
        return text + " (Hari ini)", ACCENT_COLOR
    if d == today + timedelta(days=1):
        return text + " (Besok)", ACCENT_COLOR
    return text, MUTED_COLOR



class CalendarPopup(Popup):
    def __init__(self, on_select, initial_date=None, **kwargs):
        self.on_select = on_select
        today = date.today()
        start = initial_date or today
        self.view_year = start.year
        self.view_month = start.month
        self.selected_date = initial_date

        super().__init__(
            title="Pilih Deadline",
            size_hint=(0.92, 0.68),
            separator_color=ACCENT_COLOR,
            title_color=TEXT_COLOR,
            **kwargs
        )

        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        with root.canvas.before:
            Color(*BG_COLOR)
            self._bg_rect = RoundedRectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self._bg_rect, "pos", root.pos))
        root.bind(size=lambda *_: setattr(self._bg_rect, "size", root.size))
        self.content = root


        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        prev_btn = Button(text="<", size_hint=(None, 1), width=dp(44),
                           background_normal="", background_color=CARD_COLOR,
                           color=TEXT_COLOR, bold=True)
        prev_btn.bind(on_release=lambda *_: self._change_month(-1))
        self.month_label = Label(text="", color=TEXT_COLOR, font_size="16sp", bold=True)
        next_btn = Button(text=">", size_hint=(None, 1), width=dp(44),
                           background_normal="", background_color=CARD_COLOR,
                           color=TEXT_COLOR, bold=True)
        next_btn.bind(on_release=lambda *_: self._change_month(1))
        nav.add_widget(prev_btn)
        nav.add_widget(self.month_label)
        nav.add_widget(next_btn)
        root.add_widget(nav)


        weekday_row = GridLayout(cols=7, size_hint_y=None, height=dp(24))
        for wd in WEEKDAY_NAMES_ID:
            weekday_row.add_widget(
                Label(text=wd, color=MUTED_COLOR, font_size="11sp", bold=True)
            )
        root.add_widget(weekday_row)

  
        self.day_grid = GridLayout(cols=7, spacing=dp(4))
        root.add_widget(self.day_grid)


        cancel_btn = Button(
            text="Batal", size_hint_y=None, height=dp(40),
            background_normal="", background_color=CARD_COLOR,
            color=MUTED_COLOR, bold=True,
        )
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        root.add_widget(cancel_btn)

        self._render_calendar()

    def _change_month(self, delta):
        m = self.view_month + delta
        y = self.view_year
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        self.view_month = m
        self.view_year = y
        self._render_calendar()

    def _render_calendar(self):
        self.month_label.text = "{} {}".format(MONTH_NAMES_ID[self.view_month], self.view_year)
        self.day_grid.clear_widgets()
        cal = calendar_module.Calendar(firstweekday=0)
        today = date.today()
        for week in cal.monthdayscalendar(self.view_year, self.view_month):
            for day in week:
                if day == 0:
                    self.day_grid.add_widget(Label(text=""))
                    continue
                d = date(self.view_year, self.view_month, day)
                is_past = d < today
                is_selected = self.selected_date == d
                is_today = d == today and not is_selected

                if is_selected:
                    bg = ACCENT_COLOR
                    fg = (1, 1, 1, 1)
                elif is_past:
                    bg = BG_COLOR
                    fg = MUTED_COLOR
                elif is_today:
                    bg = CARD_COLOR
                    fg = ACCENT_COLOR
                else:
                    bg = CARD_COLOR
                    fg = TEXT_COLOR

                btn = Button(
                    text=str(day),
                    background_normal="",
                    background_color=bg,
                    color=fg,
                    disabled=is_past,
                    font_size="13sp",
                    bold=is_today or is_selected,
                )
                if not is_past:
                    btn.bind(on_release=lambda b, dd=d: self._select_date(dd))
                self.day_grid.add_widget(btn)

    def _select_date(self, d):
        self.selected_date = d
        self.on_select(d)
        self.dismiss()


class TaskItem(BoxLayout):
    def __init__(self, task, on_toggle, on_delete, **kwargs):
        deadline_text, deadline_color = format_deadline_label(
            task.get("deadline"), task["done"]
        )
        card_height = dp(78) if deadline_text else dp(64)
        super().__init__(orientation="horizontal", size_hint_y=None, height=card_height,
                          padding=(dp(12), dp(8)), spacing=dp(10), **kwargs)
        self.task = task

        with self.canvas.before:
            Color(*CARD_COLOR)
            self.bg_rect = RoundedRectangle(radius=[dp(14)], pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

    
        self.checkbox = CheckBox(active=task["done"], size_hint=(None, None),
                                  size=(dp(28), dp(28)))
        self.checkbox.bind(active=lambda cb, val: on_toggle(task["id"], val))
        self.add_widget(self.checkbox)

     
        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_color = MUTED_COLOR if task["done"] else TEXT_COLOR
        self.title_label = Label(
            text=("[s]" + task["text"] + "[/s]") if task["done"] else task["text"],
            markup=True,
            color=title_color,
            font_size="15sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
        )
        self.title_label.bind(size=lambda *_: setattr(self.title_label, "text_size",
                                                        (self.title_label.width, None)))
        date_label = Label(
            text=task["created_at"],
            color=MUTED_COLOR,
            font_size="11sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(16),
        )
        date_label.bind(size=lambda *_: setattr(date_label, "text_size",
                                                  (date_label.width, None)))
        text_box.add_widget(self.title_label)
        text_box.add_widget(date_label)

        if deadline_text:
            deadline_label = Label(
                text=deadline_text,
                color=deadline_color,
                font_size="11sp",
                bold=(deadline_color == DANGER_COLOR),
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(16),
            )
            deadline_label.bind(size=lambda *_: setattr(deadline_label, "text_size",
                                                          (deadline_label.width, None)))
            text_box.add_widget(deadline_label)

        self.add_widget(text_box)

    
        delete_btn = Button(
            text="X",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=MUTED_COLOR,
            bold=True,
        )
        delete_btn.bind(on_release=lambda *_: on_delete(task["id"]))
        self.add_widget(delete_btn)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size



class TodoRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16), spacing=dp(12), **kwargs)
        self.tasks = []
        self.current_filter = "all"
        self.selected_deadline = None

        self._build_header()
        self._build_stats()
        self._build_filters()
        self._build_list()
        self._build_composer()

        self.load_tasks()

 
        Clock.schedule_once(lambda dt: self.check_deadline_notifications(), 2)
        Clock.schedule_interval(self.check_deadline_notifications, 3600)


    def _build_header(self):
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56))
        title = Label(text="Tugas Saya", font_size="24sp", bold=True,
                       color=TEXT_COLOR, halign="left", valign="top",
                       size_hint_y=None, height=dp(32))
        title.bind(size=lambda *_: setattr(title, "text_size", (title.width, None)))
        subtitle = Label(text="Catat, centang, selesai.", font_size="13sp",
                          color=MUTED_COLOR, halign="left", valign="top",
                          size_hint_y=None, height=dp(20))
        subtitle.bind(size=lambda *_: setattr(subtitle, "text_size", (subtitle.width, None)))
        header.add_widget(title)
        header.add_widget(subtitle)
        self.add_widget(header)


    def _build_stats(self):
        stats_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(64), spacing=dp(10))
        self.stat_total = self._make_stat_card("0", "Total")
        self.stat_active = self._make_stat_card("0", "Belum selesai")
        self.stat_done = self._make_stat_card("0", "Selesai")
        stats_row.add_widget(self.stat_total["widget"])
        stats_row.add_widget(self.stat_active["widget"])
        stats_row.add_widget(self.stat_done["widget"])
        self.add_widget(stats_row)

    def _make_stat_card(self, number, label):
        box = BoxLayout(orientation="vertical", padding=(dp(10), dp(8)))
        with box.canvas.before:
            Color(*CARD_COLOR)
            rect = RoundedRectangle(radius=[dp(12)], pos=box.pos, size=box.size)
        box.bind(pos=lambda *_: setattr(rect, "pos", box.pos))
        box.bind(size=lambda *_: setattr(rect, "size", box.size))

        num_label = Label(text=number, font_size="20sp", bold=True, color=TEXT_COLOR,
                           halign="left", valign="top")
        text_label = Label(text=label, font_size="11sp", color=MUTED_COLOR,
                            halign="left", valign="bottom")
        box.add_widget(num_label)
        box.add_widget(text_label)
        return {"widget": box, "num": num_label}

   
    def _build_filters(self):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40),
                         spacing=dp(8))
        self.filter_buttons = {}
        for key, label in [("all", "Semua"), ("active", "Aktif"), ("done", "Selesai")]:
            btn = ToggleButton(
                text=label, group="filter", state="down" if key == "all" else "normal",
                background_normal="", background_down="",
                background_color=ACCENT_COLOR if key == "all" else CARD_COLOR,
                color=(1, 1, 1, 1) if key == "all" else MUTED_COLOR,
            )
            btn.bind(on_release=lambda b, k=key: self.set_filter(k))
            self.filter_buttons[key] = btn
            row.add_widget(btn)
        self.add_widget(row)

    def set_filter(self, key):
        self.current_filter = key
        for k, btn in self.filter_buttons.items():
            btn.background_color = ACCENT_COLOR if k == key else CARD_COLOR
            btn.color = (1, 1, 1, 1) if k == key else MUTED_COLOR
        self.render_list()


    def _build_list(self):
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None,
                                       padding=(0, dp(4)))
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        scroll.add_widget(self.list_layout)
        self.add_widget(scroll)


    def _build_composer(self):
        composer = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(96),
                              spacing=dp(6))


        row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                          spacing=dp(8))
        self.input = TextInput(
            hint_text="Tulis tugas baru...",
            multiline=False,
            background_color=CARD_COLOR,
            foreground_color=TEXT_COLOR,
            hint_text_color=MUTED_COLOR,
            padding=(dp(14), dp(14)),
            cursor_color=ACCENT_COLOR,
        )
        add_btn = Button(
            text="+", size_hint=(None, 1), width=dp(52),
            background_normal="", background_color=ACCENT_COLOR,
            font_size="22sp", bold=True,
        )
        add_btn.bind(on_release=lambda *_: self.add_task())
        row1.add_widget(self.input)
        row1.add_widget(add_btn)

        row2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40),
                          spacing=dp(8))
        self.deadline_btn = Button(
            text="Pilih deadline (wajib)",
            background_normal="",
            background_color=CARD_COLOR,
            color=MUTED_COLOR,
            font_size="13sp",
            halign="left",
        )
        self.deadline_btn.bind(size=lambda *_: setattr(
            self.deadline_btn, "text_size", (self.deadline_btn.width - dp(20), None)
        ))
        self.deadline_btn.bind(on_release=lambda *_: self.open_calendar())
        row2.add_widget(self.deadline_btn)
        composer.add_widget(row1)
        composer.add_widget(row2)
        self.add_widget(composer)

    def open_calendar(self):
        popup = CalendarPopup(on_select=self.set_deadline, initial_date=self.selected_deadline)
        popup.open()

    def set_deadline(self, d):
        self.selected_deadline = d
        self.deadline_btn.text = "\U0001F4C5 " + d.strftime("%d %b %Y")
        self.deadline_btn.color = TEXT_COLOR

    def reset_deadline_button(self):
        self.selected_deadline = None
        self.deadline_btn.text = "Pilih deadline (wajib)"
        self.deadline_btn.color = MUTED_COLOR


    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.tasks = []
        else:
            self.tasks = []
        self.render_list()

    def save_tasks(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def add_task(self):
        text = self.input.text.strip()
        if not text:
            self._show_error("Nama tugas tidak boleh kosong.")
            return

        if self.selected_deadline is None:
            self._show_error("Deadline wajib dipilih. Ketuk tombol kalender di bawah.")
            return

        self.tasks.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "created_at": datetime.now().strftime("%d %b %Y"),
            "deadline": self.selected_deadline.strftime(DEADLINE_FORMAT),
            "notified": False,
        })
        self.input.text = ""
        self.reset_deadline_button()
        self.save_tasks()
        self.render_list()

    def _show_error(self, message):
        popup = Popup(
            title="Oops",
            content=Label(text=message, color=TEXT_COLOR),
            size_hint=(0.8, None),
            height=dp(160),
            separator_color=ACCENT_COLOR,
        )
        popup.open()

    def toggle_task(self, task_id, value):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = bool(value)
                break
        self.save_tasks()
        self.render_list()

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()
        self.render_list()

    def render_list(self):
        self.list_layout.clear_widgets()

        if self.current_filter == "active":
            filtered = [t for t in self.tasks if not t["done"]]
        elif self.current_filter == "done":
            filtered = [t for t in self.tasks if t["done"]]
        else:
            filtered = self.tasks


        total = len(self.tasks)
        done = len([t for t in self.tasks if t["done"]])
        active = total - done
        self.stat_total["num"].text = str(total)
        self.stat_active["num"].text = str(active)
        self.stat_done["num"].text = str(done)

        if not filtered:
            msg = {
                "all": "Belum ada tugas. Tambahkan satu di bawah!",
                "active": "Semua tugas sudah selesai",
                "done": "Belum ada tugas selesai",
            }[self.current_filter]
            empty_label = Label(text=msg, color=MUTED_COLOR, size_hint_y=None,
                                 height=dp(80))
            self.list_layout.add_widget(empty_label)
            return


        def sort_key(t):
            d = parse_deadline(t.get("deadline"))
            has_no_deadline = d is None
            return (t["done"], has_no_deadline, d or date.max)

        sorted_tasks = sorted(filtered, key=sort_key)
        for task in sorted_tasks:
            item = TaskItem(task, self.toggle_task, self.delete_task)
            self.list_layout.add_widget(item)


    def check_deadline_notifications(self, *args):
        if plyer_notification is None:
            return
        tomorrow = date.today() + timedelta(days=1)
        changed = False
        for t in self.tasks:
            if t["done"] or t.get("notified"):
                continue
            d = parse_deadline(t.get("deadline"))
            if d == tomorrow:
                try:
                    plyer_notification.notify(
                        title="Deadline besok!",
                        message='Tugas "{}" harus selesai besok ({}).'.format(
                            t["text"], d.strftime("%d %b %Y")
                        ),
                        timeout=10,
                    )
                except Exception:
                    pass
                t["notified"] = True
                changed = True
        if changed:
            self.save_tasks()


class TodoApp(App):
    def build(self):
        self.title = "To-Do List"
        return TodoRoot()


if __name__ == "__main__":
    TodoApp().run()
