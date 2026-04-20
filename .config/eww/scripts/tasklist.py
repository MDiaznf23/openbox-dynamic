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
        
        self.icon_theme = self.load_icon_config()
        self.desktop_entries = self.load_all_desktop_entries()
        
        self.icon_path_cache = {}
        self.last_json = ""
        
        self.icon_search_dirs = [
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}-light/scalable/apps"),
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}/scalable/apps"),
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}-light/48x48/apps"),
            os.path.expanduser(f"~/.local/share/icons/{self.icon_theme}/48x48/apps"),
            "/usr/share/icons/hicolor/scalable/apps",
            "/usr/share/icons/hicolor/48x48/apps",
            "/usr/share/pixmaps"
        ]

    def load_icon_config(self):
        conf_path = os.path.expanduser("~/.config/openbox/config-dotfiles")
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
                with open(f"/proc/{pid}/comm", "r") as f:
                    return f.read().strip().lower()
            except: pass
        return None

    def find_icon(self, wm_class, win):
        cls_lower = wm_class.lower()
        if cls_lower in self.icon_path_cache:
            return self.icon_path_cache[cls_lower]

        cmd_name = self.get_window_pid_cmd(win)
        fallback = os.path.realpath("/usr/share/icons/hicolor/48x48/apps/application-x-executable.png")

        desktop_icon = None

        # Pass 1: exact filename == wm_class (paling akurat, hindari false match)
        for entry in self.desktop_entries:
            if entry['filename'] == cls_lower:
                desktop_icon = entry['icon']; break

        # Pass 2: StartupWMClass
        if not desktop_icon:
            for entry in self.desktop_entries:
                if entry['swm'] == cls_lower:
                    desktop_icon = entry['icon']; break

        # Pass 3: exact filename == cmd_name
        if not desktop_icon and cmd_name:
            for entry in self.desktop_entries:
                if entry['filename'] == cmd_name:
                    desktop_icon = entry['icon']; break

        # Pass 4: exec == cmd_name (last resort)
        if not desktop_icon and cmd_name:
            for entry in self.desktop_entries:
                if entry['exec'] == cmd_name:
                    desktop_icon = entry['icon']; break

        candidates = [cls_lower]
        if cmd_name and cmd_name != cls_lower:
            candidates.append(cmd_name)
        if desktop_icon and desktop_icon.lower() not in candidates:
            candidates.append(desktop_icon)

        result = fallback
        for name in candidates:
            found = False
            for base in self.icon_search_dirs:
                for ext in [".svg", ".png"]:
                    p = os.path.join(base, f"{name}{ext}")
                    if os.path.exists(p):
                        result = os.path.realpath(p)
                        found = True
                        break
                if found: break
            if found: break

        self.icon_path_cache[cls_lower] = result
        return result

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
            
            self.display.next_event()

if __name__ == "__main__":
    TaskManager().run()
