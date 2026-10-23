# SoftEther Japan

A native GTK 4 front end for connecting Arch Linux to Japanese
[VPN Gate](https://www.vpngate.net/) relays through the Linux SoftEther VPN
Client.

## Features

- Live, Japanese-only relay list from VPN Gate's official CSV API
- Ping, advertised throughput, and session counts
- One-click connect and disconnect
- Native SoftEther protocol rather than a Windows client under Wine
- Fail-closed `nftables` kill switch on the physical interface
- Physical-interface DNS blocking while the VPN is expected to be active
- Public-IP country verification after connection
- A minimal root-owned helper; the GTK application itself is unprivileged

## Arch Linux installation

Install the AUR `softethervpn` package first, then build this package:

```bash
makepkg -si
sudo systemctl enable --now softethervpn-client.service
```

Launch **SoftEther Japan** from your application menu or run:

```bash
softether-jp
```

The administrator dialog authorizes only the networking helper used to install
the temporary firewall and NetworkManager route. Disconnect other VPN clients
before connecting.

## Leak model

The kill switch is installed *before* SoftEther establishes the tunnel. While
active, the selected relay is the only public IPv4 destination permitted on the
physical interface; public IPv6 and physical-interface DNS are blocked. Local
RFC1918/link-local traffic remains available. If setup fails, the tunnel is
disconnected before the firewall is removed.

No VPN can conceal the source address from the selected VPN server itself. The
VPN Gate directory also sees the address used to refresh its public server list.
See [SECURITY.md](SECURITY.md) for the audit, threat model, and limitations.

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile softether_jp.py
sh -n softether-jp-helper
```

This project is an independent client and is not affiliated with the University
of Tsukuba, VPN Gate, or the SoftEther VPN Project.
