#!/usr/bin/env python3

import json
import os
import re
import sys
from Xlib import X, display

class TaskManager:
    def __init__(self):
        self.display = display.Display()
        self.root = self.display.screen().root
        
        self.atoms = {
            'client_list': self.display.get_atom('_NET_CLIENT_LIST'),
            'active_win': self.display.get_atom('_NET_ACTIVE_WINDOW'),
            'desktop': self.display.get_atom('_NET_CURRENT_DESKTOP'),
            'wm_desktop': self.display.get_atom('_NET_WM_DESKTOP'),
            'wm_state': self.display.get_atom('_NET_WM_STATE'),
            'hidden': self.display.get_atom('_NET_WM_STATE_HIDDEN'),
            'wm_pid': self.display.get_atom('_NET_WM_PID')
        }
        
        self.root.change_attributes(event_mask=X.PropertyChangeMask)
        
        # 1. Load Config & Precompute
        self.icon_theme = self.load_icon_config()
        self.desktop_entries = self.load_all_desktop_entries()
        
        self.icon_path_cache = {}
        self.last_json = ""
        
        # Path prioritas Diaz
        self.icon_search_dirs = [
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}-light/scalable/apps"),
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}/scalable/apps"),
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}-light/48x48/apps"),
            "/usr/share/icons/hicolor/scalable/apps",
            "/usr/share/pixmaps"
        ]

    def load_icon_config(self):
        conf_path = os.path.expanduser("~/.config/eww/scripts/icon-theme.conf")
        if os.path.exists(conf_path):
            try:
                with open(conf_path, 'r') as f:
                    content = f.read()
                    match = re.search(r'ICON_THEME=["\']?([^"\s\']+)["\']?', content)
                    if match: return match.group(1)
            except: pass
        return "Tela"

    def load_all_desktop_entries(self):
        entries = []
        dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        for d in dirs:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if f.endswith(".desktop"):
                    try:
                        with open(os.path.join(d, f), 'r', errors='ignore') as file:
                            content = file.read()
                            icon = re.search(r'^Icon=(.*)$', content, re.M)
                            swm = re.search(r'^StartupWMClass=(.*)$', content, re.M)
                            # Ambil Exec tanpa argumen %u dsb
                            exe = re.search(r'^Exec=([^ %\n]*)', content, re.M)
                            
                            if icon:
                                entries.append({
                                    'filename': f.lower().replace(".desktop", ""),
                                    'icon': icon.group(1).strip(),
                                    'swm': swm.group(1).strip().lower() if swm else None,
                                    'exec': os.path.basename(exe.group(1)).lower() if exe else None
                                })
                    except: continue
        return entries

    def get_window_pid_cmd(self, win):
        pid_prop = win.get_full_property(self.atoms['wm_pid'], X.AnyPropertyType)
        if pid_prop:
            pid = pid_prop.value[0]
            try:
                # Cek cmdline untuk mendapatkan nama binary asli
                with open(f"/proc/{pid}/comm", "r") as f:
                    return f.read().strip().lower()
            except: pass
        return None

    def find_icon(self, wm_class, win):
        cls_lower = wm_class.lower()
        if cls_lower in self.icon_path_cache: return self.icon_path_cache[cls_lower]

        icon_name = None
        cmd_name = self.get_window_pid_cmd(win)

        # Cari kecocokan paling akurat
        for entry in self.desktop_entries:
            # 1. Cek StartupWMClass
            if entry['swm'] == cls_lower:
                icon_name = entry['icon']
                break
            # 2. Cek Nama File .desktop (misal kdeconnect-app.desktop)
            if entry['filename'] in cls_lower or (cmd_name and entry['filename'] in cmd_name):
                icon_name = entry['icon']
                break
            # 3. Cek Exec binary
            if cmd_name and entry['exec'] == cmd_name:
                icon_name = entry['icon']
                break
        
        if not icon_name: icon_name = cls_lower

        # Cari path fisik
        final_path = "/usr/share/icons/hicolor/48x48/apps/application-x-executable.png"
        for base in self.icon_search_dirs:
            if final_path != "/usr/share/icons/hicolor/48x48/apps/application-x-executable.png": break
            for ext in [".svg", ".png"]:
                p = os.path.join(base, f"{icon_name}{ext}")
                if os.path.exists(p):
                    final_path = p
                    break
        
        self.icon_path_cache[cls_lower] = final_path
        return final_path

    def get_tasks(self):
        curr_dsktp = self.get_prop(self.root, 'desktop')
        current_desktop = curr_dsktp[0] if curr_dsktp else 0
        active_win = self.get_prop(self.root, 'active_win')
        active_id = active_win[0] if active_win else None
        win_ids = self.get_prop(self.root, 'client_list')
        
        if not win_ids: return "[]"

        tasks = []
        for win_id in win_ids:
            try:
                win = self.display.create_resource_object('window', win_id)
                win_dsktp = self.get_prop(win, 'wm_desktop')
                if win_dsktp and win_dsktp[0] != current_desktop and win_dsktp[0] != 0xFFFFFFFF:
                    continue

                wm_class = win.get_wm_class()
                if not wm_class: continue
                
                # Gunakan class name (index 1) untuk title, tapi index 0 sering lebih akurat buat icon
                instance_name, class_name = wm_class
                if class_name.lower() in ['eww', 'polybar', 'tint2', 'desktop', '_']: continue

                state = self.get_prop(win, 'wm_state')
                minimized = bool(state and self.atoms['hidden'] in state)

                tasks.append({
                    "id": f"0x{win_id:08x}",
                    "title": class_name.capitalize(),
                    "focused": win_id == active_id,
                    "minimized": minimized,
                    "icon": self.find_icon(class_name, win)
                })
            except: continue
        
        return json.dumps(tasks)

    def get_prop(self, win, atom_name):
        try:
            prop = win.get_full_property(self.atoms[atom_name], X.AnyPropertyType)
            return prop.value if prop else None
        except: return None

    def run(self):
        while True:
            current_json = self.get_tasks()
            if current_json != self.last_json:
                sys.stdout.write(current_json + '\n')
                sys.stdout.flush()
                self.last_json = current_json
            
            # Blocking wait for next event
            self.display.next_event()

if __name__ == "__main__":
    TaskManager().run()
