#!/usr/bin/env python3
"""Native GTK front end for Japanese VPN Gate relays via SoftEther VPN Client."""

from __future__ import annotations

import concurrent.futures
import os
import socket
import subprocess
import threading
import time
import gi
import requests

from relays import Relay, parse_relays

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402


API_URL = "https://www.vpngate.net/api/iphone/"
ACCOUNT = "Japan-GUI"
NIC = "japan"
HELPER = "/usr/libexec/softether-jp-helper"


def run(*args: str, timeout: int = 30, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=check)


def vpncmd(command: str, *args: str, check: bool = True) -> str:
    proc = run("vpncmd", "localhost", "/CLIENT", "/CMD", command, *args, check=check)
    return proc.stdout + proc.stderr


class SoftEtherJapan(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="net.vpngate.SoftEtherJapan")
        self.relays: list[Relay] = []
        self.rows: dict[Gtk.ListBoxRow, Relay] = {}
        self.connected: Relay | None = None
        self.busy = False

    def do_activate(self) -> None:
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("SoftEther Japan")
        self.window.set_default_size(820, 620)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)
        self.window.set_child(root)

        title_row = Gtk.Box(spacing=12)
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Japanese VPN Gate relays</span>")
        title.set_xalign(0)
        title.set_hexpand(True)
        title_row.append(title)
        self.refresh_button = Gtk.Button(label="Refresh")
        self.refresh_button.connect("clicked", lambda *_: self.refresh())
        title_row.append(self.refresh_button)
        root.append(title_row)

        subtitle = Gtk.Label(label="Native SoftEther VPN Client • live University of Tsukuba directory")
        subtitle.set_xalign(0)
        subtitle.add_css_class("dim-label")
        root.append(subtitle)

        self.status = Gtk.Label(label="Loading Japanese relays…")
        self.status.set_xalign(0)
        self.status.set_wrap(True)
        root.append(self.status)

        headings = Gtk.Box(spacing=12)
        for text, width, expand in (("Relay", 28, True), ("Ping", 9, False), ("Speed", 12, False), ("Users", 8, False)):
            label = Gtk.Label(label=text, xalign=0)
            label.set_width_chars(width)
            label.set_hexpand(expand)
            label.add_css_class("heading")
            headings.append(label)
        root.append(headings)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.connect("row-activated", lambda *_: self.connect_selected())
        scroll.set_child(self.listbox)
        root.append(scroll)

        actions = Gtk.Box(spacing=10)
        self.connect_button = Gtk.Button(label="Connect selected")
        self.connect_button.add_css_class("suggested-action")
        self.connect_button.set_sensitive(False)
        self.connect_button.connect("clicked", lambda *_: self.connect_selected())
        actions.append(self.connect_button)
        self.disconnect_button = Gtk.Button(label="Disconnect")
        self.disconnect_button.add_css_class("destructive-action")
        self.disconnect_button.set_sensitive(False)
        self.disconnect_button.connect("clicked", lambda *_: self.disconnect())
        actions.append(self.disconnect_button)
        self.ip_label = Gtk.Label(label="Not connected", xalign=1)
        self.ip_label.set_hexpand(True)
        actions.append(self.ip_label)
        root.append(actions)

        self.window.present()
        self.refresh()

    def set_status(self, text: str) -> bool:
        self.status.set_text(text)
        return False

    def set_busy(self, busy: bool) -> bool:
        self.busy = busy
        self.refresh_button.set_sensitive(not busy)
        self.connect_button.set_sensitive(not busy and self.listbox.get_selected_row() is not None and self.connected is None)
        self.disconnect_button.set_sensitive(not busy and self.connected is not None)
        return False

    def refresh(self) -> None:
        if self.busy:
            return
        self.set_busy(True)
        self.set_status("Refreshing the live VPN Gate directory…")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            response = requests.get(API_URL, timeout=25, headers={"User-Agent": "SoftEtherJapan/1.0"})
            response.raise_for_status()
            parsed = parse_relays(response.text)
            if not parsed:
                raise RuntimeError("VPN Gate returned no Japanese relays")
            GLib.idle_add(self._show_relays, parsed)
        except Exception as exc:
            GLib.idle_add(self.set_status, f"Refresh failed: {exc}")
        finally:
            GLib.idle_add(self.set_busy, False)

    def _show_relays(self, relays: list[Relay]) -> bool:
        while child := self.listbox.get_first_child():
            self.listbox.remove(child)
        self.rows.clear()
        self.relays = relays
        for relay in relays:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(spacing=12)
            box.set_margin_top(9)
            box.set_margin_bottom(9)
            box.set_margin_start(10)
            box.set_margin_end(10)
            name = Gtk.Label(label=f"{relay.host}\n{relay.ip}", xalign=0)
            name.set_width_chars(28)
            name.set_hexpand(True)
            box.append(name)
            for text, width in ((relay.ping_text, 9), (relay.speed_text, 12), (str(relay.sessions), 8)):
                label = Gtk.Label(label=text, xalign=0)
                label.set_width_chars(width)
                box.append(label)
            row.set_child(box)
            self.listbox.append(row)
            self.rows[row] = relay
        first = self.listbox.get_row_at_index(0)
        self.listbox.select_row(first)
        self.set_status(f"{len(relays)} Japanese relays available. Double-click a relay or press Connect selected.")
        self.connect_button.set_sensitive(self.connected is None)
        return False

    def connect_selected(self) -> None:
        if self.busy or self.connected:
            return
        row = self.listbox.get_selected_row()
        if row is None:
            return
        relay = self.rows[row]
        self.set_busy(True)
        self.set_status(f"Connecting to {relay.ip}… You may be asked for your administrator password.")
        threading.Thread(target=self._connect_worker, args=(relay,), daemon=True).start()

    @staticmethod
    def _open_port(ip: str) -> int:
        def reachable(port: int) -> int | None:
            try:
                with socket.create_connection((ip, port), timeout=3):
                    return port
            except OSError:
                return None
        ports = (443, 992, 5555)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(ports)) as pool:
            results = list(pool.map(reachable, ports))
        for port in ports:
            if port in results:
                return port
        raise RuntimeError("This relay is no longer accepting SoftEther connections")

    def _connect_worker(self, relay: Relay) -> None:
        try:
            port = self._open_port(relay.ip)
            if not os.path.isfile(HELPER) or os.stat(HELPER).st_uid != 0:
                raise RuntimeError("The root-owned networking helper is not installed")
            # Fail closed before starting the tunnel. Only the selected relay and
            # local-network traffic may leave through the physical interface.
            run("pkexec", HELPER, "prepare", relay.ip, timeout=60)
            vpncmd("AccountDisconnect", ACCOUNT, check=False)
            vpncmd("AccountDelete", ACCOUNT, check=False)
            vpncmd("AccountCreate", ACCOUNT, f"/SERVER:{relay.ip}:{port}", "/HUB:VPNGATE", "/USERNAME:vpn", f"/NICNAME:{NIC}")
            vpncmd("AccountPasswordSet", ACCOUNT, "/PASSWORD:vpn", "/TYPE:standard")
            vpncmd("AccountServerCertDisable", ACCOUNT)
            vpncmd("AccountConnect", ACCOUNT)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                status = vpncmd("AccountStatusGet", ACCOUNT, check=False)
                if "Session Established" in status or "Connection Completed" in status:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("SoftEther did not establish a session in time")
            run("pkexec", HELPER, "up", timeout=60)
            ip_info = requests.get("https://ipinfo.io/json", timeout=15).json()
            if ip_info.get("country") != "JP":
                raise RuntimeError(f"Connected, but public location is {ip_info.get('country', 'unknown')} instead of JP")
            self.connected = relay
            public_ip = ip_info.get("ip", relay.ip)
            city = ip_info.get("city", "Japan")
            GLib.idle_add(self._connected_ui, public_ip, city)
        except Exception as exc:
            vpncmd("AccountDisconnect", ACCOUNT, check=False)
            run("pkexec", HELPER, "down", timeout=45, check=False)
            GLib.idle_add(self.set_status, f"Connection failed: {exc}")
        finally:
            GLib.idle_add(self.set_busy, False)

    def _connected_ui(self, public_ip: str, city: str) -> bool:
        self.ip_label.set_text(f"JP • {public_ip} • {city}")
        self.set_status("Connected through the native SoftEther client. You can now launch the game.")
        return False

    def disconnect(self) -> None:
        if self.busy or not self.connected:
            return
        self.set_busy(True)
        self.set_status("Disconnecting…")
        threading.Thread(target=self._disconnect_worker, daemon=True).start()

    def _disconnect_worker(self) -> None:
        errors = []
        try:
            # Drop the tunnel while the kill switch is still active, then
            # deliberately restore the normal physical route.
            vpncmd("AccountDisconnect", ACCOUNT, check=False)
            run("pkexec", HELPER, "down", timeout=45, check=False)
        except Exception as exc:
            errors.append(str(exc))
        self.connected = None
        GLib.idle_add(self._disconnected_ui, errors)
        GLib.idle_add(self.set_busy, False)

    def _disconnected_ui(self, errors: list[str]) -> bool:
        self.ip_label.set_text("Not connected")
        self.set_status("Disconnected." if not errors else f"Disconnected with warning: {'; '.join(errors)}")
        return False


if __name__ == "__main__":
    raise SystemExit(SoftEtherJapan().run())
