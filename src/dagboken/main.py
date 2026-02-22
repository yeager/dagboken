import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio
import gettext, locale, os, json, time

__version__ = "0.1.0"
APP_ID = "se.danielnylander.dagboken"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'share', 'locale')
if not os.path.isdir(LOCALE_DIR): LOCALE_DIR = "/usr/share/locale"
try:
    locale.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.textdomain(APP_ID)
except Exception: pass
_ = gettext.gettext
def N_(s): return s


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_('Dagboken'))
        self.set_default_size(500, 550)
        self._entries = []
        self._config_dir = os.path.join(GLib.get_user_config_dir(), 'dagboken')
        os.makedirs(self._config_dir, exist_ok=True)
        self._load()
        
        header = Adw.HeaderBar()
        add_btn = Gtk.Button(icon_name='list-add-symbolic')
        add_btn.connect('clicked', self._on_add)
        header.pack_start(add_btn)
        menu_btn = Gtk.MenuButton(icon_name='open-menu-symbolic')
        menu = Gio.Menu()
        menu.append(_('About'), 'app.about')
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)
        
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main.append(header)
        
        title = Gtk.Label(label=_('My Diary'))
        title.add_css_class('title-2')
        title.set_margin_top(16)
        main.append(title)
        
        today = Gtk.Label(label=time.strftime('%A %d %B %Y'))
        today.add_css_class('dim-label')
        main.append(today)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self._list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._list.set_margin_top(16)
        self._list.set_margin_start(16)
        self._list.set_margin_end(16)
        self._list.set_margin_bottom(16)
        
        self._refresh_list()
        scroll.set_child(self._list)
        main.append(scroll)
        
        if not self._entries:
            empty = Gtk.Label(label=_('No entries yet. Tap + to add your first entry!'))
            empty.add_css_class('dim-label')
            empty.set_wrap(True)
            self._list.append(empty)
        
        self.set_content(main)
    
    def _on_add(self, btn):
        dialog = Adw.Dialog()
        dialog.set_title(_('New Entry'))
        dialog.set_content_width(400)
        dialog.set_content_height(300)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        hdr = Adw.HeaderBar()
        save_btn = Gtk.Button(label=_('Save'))
        save_btn.add_css_class('suggested-action')
        hdr.pack_end(save_btn)
        box.append(hdr)
        
        moods = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        moods.set_halign(Gtk.Align.CENTER)
        moods.set_margin_top(8)
        selected_mood = ["😊"]
        for emoji in ["😊", "😐", "😢", "😡", "😴", "🤩"]:
            btn_m = Gtk.Button(label=emoji)
            btn_m.add_css_class('circular')
            btn_m.connect('clicked', lambda b, e=emoji: selected_mood.__setitem__(0, e))
            moods.append(btn_m)
        box.append(moods)
        
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_margin_start(16)
        text_view.set_margin_end(16)
        text_view.set_vexpand(True)
        text_view.get_buffer().set_text(_('What happened today?'))
        box.append(text_view)
        
        def on_save(b):
            buf = text_view.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
            entry = {'mood': selected_mood[0], 'text': text, 'time': time.strftime('%Y-%m-%d %H:%M')}
            self._entries.append(entry)
            self._save()
            self._refresh_list()
            dialog.close()
        
        save_btn.connect('clicked', on_save)
        dialog.set_child(box)
        dialog.present(self)
    
    def _refresh_list(self):
        while child := self._list.get_first_child():
            self._list.remove(child)
        for entry in reversed(self._entries[-20:]):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            mood = Gtk.Label(label=entry.get('mood', ''))
            mood.add_css_class('title-2')
            row.append(mood)
            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            info.set_hexpand(True)
            dt = Gtk.Label(label=entry.get('time', ''), xalign=0)
            dt.add_css_class('dim-label')
            dt.add_css_class('caption')
            info.append(dt)
            txt = Gtk.Label(label=entry.get('text', '')[:80], xalign=0)
            txt.set_wrap(True)
            info.append(txt)
            row.append(info)
            self._list.append(row)
    
    def _load(self):
        try:
            with open(os.path.join(self._config_dir, 'diary.json')) as f:
                self._entries = json.load(f)
        except Exception:
            self._entries = []
    
    def _save(self):
        with open(os.path.join(self._config_dir, 'diary.json'), 'w') as f:
            json.dump(self._entries, f, ensure_ascii=False)

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id='se.danielnylander.dagboken')
        self.connect('activate', self._on_activate)
        about = Gio.SimpleAction.new('about', None)
        about.connect('activate', self._on_about)
        self.add_action(about)
    def _on_activate(self, app): MainWindow(application=app).present()
    def _on_about(self, a, p):
        Adw.AboutDialog(application_name=_('Dagboken'), application_icon=APP_ID,
            version=__version__, developer_name='Daniel Nylander',
            website='https://github.com/yeager/dagboken', license_type=Gtk.License.GPL_3_0,
            comments=_('Picture diary for children'),
            developers=['Daniel Nylander <daniel@danielnylander.se>']).present(self.get_active_window())


def main():
    app = App()
    app.run()

if __name__ == "__main__":
    main()
