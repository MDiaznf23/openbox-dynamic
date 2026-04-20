#!/usr/bin/env python3
"""
fullscreen-monitor.py — Monitor fullscreen via X11 events (Openbox-compatible)
Event-driven: subscribe ke PropertyNotify pada setiap window baru
"""

import subprocess
import sys

from Xlib import X, display as xdisplay
from Xlib.ext import randr


def get_atoms(d):
    return {
        "fullscreen": d.intern_atom("_NET_WM_STATE_FULLSCREEN"),
        "wm_state":   d.intern_atom("_NET_WM_STATE"),
        "client_list": d.intern_atom("_NET_CLIENT_LIST"),
    }


def is_fullscreen(window, atom_wm_state, atom_fullscreen) -> bool:
    try:
        prop = window.get_full_property(atom_wm_state, X.AnyPropertyType)
        if prop and prop.value:
            return atom_fullscreen in prop.value
    except Exception:
        pass
    return False


def any_fullscreen(d, atoms) -> bool:
    root = d.screen().root
    try:
        client_list = root.get_full_property(atoms["client_list"], X.AnyPropertyType)
        if not client_list:
            return False
        for wid in client_list.value:
            try:
                win = d.create_resource_object("window", wid)
                if is_fullscreen(win, atoms["wm_state"], atoms["fullscreen"]):
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def subscribe_property_notify(d):
    """Subscribe PropertyNotify ke semua existing windows."""
    root = d.screen().root
    try:
        client_list = root.get_full_property(
            d.intern_atom("_NET_CLIENT_LIST"), X.AnyPropertyType
        )
        if client_list:
            for wid in client_list.value:
                try:
                    win = d.create_resource_object("window", wid)
                    win.change_attributes(event_mask=X.PropertyChangeMask)
                except Exception:
                    pass
    except Exception:
        pass


def run():
    d = xdisplay.Display()
    root = d.screen().root
    atoms = get_atoms(d)

    # Subscribe ke root: PropertyNotify (untuk _NET_CLIENT_LIST) + SubstructureNotify
    root.change_attributes(
        event_mask=X.PropertyChangeMask | X.SubstructureNotifyMask
    )

    # Subscribe ke semua window yang sudah ada
    subscribe_property_notify(d)

    prev_state = None

    print("[fullscreen-monitor] Aktif, menunggu X11 events...", file=sys.stderr, flush=True)

    # Cek state awal
    current = any_fullscreen(d, atoms)
    prev_state = current
    if current:
        subprocess.run(["eww", "close", "bar"], capture_output=True)
    else:
        subprocess.run(["eww", "open", "bar"], capture_output=True)

    while True:
        event = d.next_event()

        # Window baru muncul → subscribe PropertyNotify-nya
        if event.type == X.CreateNotify:
            try:
                event.window.change_attributes(event_mask=X.PropertyChangeMask)
            except Exception:
                pass
            continue

        # Hanya proses PropertyNotify
        if event.type != X.PropertyNotify:
            continue

        # Filter: hanya _NET_WM_STATE atau _NET_CLIENT_LIST yang relevan
        if event.atom not in (atoms["wm_state"], atoms["client_list"]):
            continue

        current = any_fullscreen(d, atoms)

        if current == prev_state:
            continue

        prev_state = current

        if current:
            print("[fullscreen-monitor] Fullscreen terdeteksi → tutup bar", file=sys.stderr, flush=True)
            subprocess.run(["eww", "close", "bar"], capture_output=True)
        else:
            print("[fullscreen-monitor] Kembali normal → buka bar", file=sys.stderr, flush=True)
            subprocess.run(["eww", "open", "bar"], capture_output=True)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[fullscreen-monitor] Dihentikan.", file=sys.stderr)
