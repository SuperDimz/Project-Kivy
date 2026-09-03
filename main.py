import json
import os
from sys import platform
import uuid
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
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
from kivy.lang import Builder

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


class TaskItem(BoxLayout):
    def __init__(self, task, on_toggle, on_delete, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(64),
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

        self._build_header()
        self._build_stats()
        self._build_filters()
        self._build_list()
        self._build_composer()

        self.load_tasks()


    def _build_header(self):
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56))
        title = Label(text="To Do List", font_size="24sp", bold=True,
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
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
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

        self.input.bind(on_text_validate=lambda *_: self.add_task())
        add_btn = Button(
            text="+",
            size_hint=(None, 1),
            width=dp(52),
            background_normal="",
            background_color=(0, 0, 0, 0),
            font_size="22sp",
            bold=True
        )

        with add_btn.canvas.before:
            Color(*ACCENT_COLOR)
            add_btn.bg = RoundedRectangle(
            pos=add_btn.pos,
            size=add_btn.size,
            radius=[20, 20, 20, 20]
        )

        def update_add_btn(instance, value):
            add_btn.bg.pos = add_btn.pos
            add_btn.bg.size = add_btn.size

        add_btn.bind(pos=update_add_btn, size=update_add_btn) 

        add_btn.bind(on_release=lambda *_: self.add_task())
        row.add_widget(self.input)
        row.add_widget(add_btn)
        self.add_widget(row)


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
            return
        self.tasks.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "created_at": datetime.now().strftime("%d %b %Y"),
        })
        self.input.text = ""
        self.save_tasks()
        self.render_list()

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


        sorted_tasks = sorted(filtered, key=lambda t: (t["done"],), reverse=False)
        for task in sorted_tasks:
            item = TaskItem(task, self.toggle_task, self.delete_task)
            self.list_layout.add_widget(item)


class TodoApp(App):
    def build(self):
        self.title = "To-Do List"
        return TodoRoot()


if __name__ == "__main__":
    TodoApp().run()
