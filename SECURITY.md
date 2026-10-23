# Security audit and threat model

## Security objective

When the user presses Connect, ordinary public traffic must not fall back to the
physical interface while the application expects SoftEther to provide privacy.

## Controls

1. The GUI validates relay addresses as IPv4 values and never passes shell text
   from the VPN Gate directory.
2. A root-owned helper adds a host route to the selected relay and atomically
   installs an `nftables` output chain before the tunnel is started.
3. The physical interface permits only the selected relay, DHCP renewal, and
   local RFC1918/link-local destinations. Public IPv4, public IPv6, and DNS on
   the physical interface are dropped.
4. The VPN connection uses a literal relay IP, avoiding pre-tunnel DNS.
5. DHCP and routing are delegated to NetworkManager only after SoftEther reports
   an established session.
6. The application checks an independent public-IP endpoint and rejects a
   result whose country is not `JP`.
7. On setup failure, SoftEther is disconnected while the kill switch remains in
   place, after which the helper restores normal networking.
8. The privileged helper is installed root-owned in `/usr/libexec`; the GUI and
   remote relay data cannot replace it.
9. PolicyKit permits only the packaged helper for an active local desktop
   session, so connection and cleanup do not create repeated password dialogs.

## Privileged surface

`softether-jp-helper` accepts only `prepare <IPv4>`, `up`, and `down`. It validates
the IPv4 argument, derives the physical gateway/interface from the kernel route
table, and uses fixed `nft`, `ip`, and `nmcli` operations. It does not evaluate
remote text or invoke a shell constructed by the GUI.

The PolicyKit grant is deliberately narrower than passwordless access to
`nft`, `ip`, `nmcli`, a shell, or arbitrary commands. Inactive and remote
sessions are denied. An interactive user can already originate or stop their
own network traffic, so letting that user operate this application's validated
kill-switch helper does not add access to another user's data.

## Limitations

- The chosen VPN Gate volunteer relay necessarily observes the user's source IP.
- VPN Gate volunteer relays do not provide a stable certificate trust anchor;
  server-certificate verification is therefore disabled for these dynamic
  profiles. The tunnel is encrypted but the relay is not strongly authenticated.
- Refreshing the VPN Gate directory before connection reveals the source IP to
  VPN Gate's web service.
- Applications can identify users through accounts, cookies, browser
  fingerprinting, or other identifiers even when the network IP is Japanese.
- Local-network traffic is intentionally allowed and can reveal a private LAN
  address to local devices, but is not routed to the public Internet.
- A root process can alter or bypass the firewall.
- Abrupt power loss requires no cleanup; `nftables` runtime state disappears on
  reboot. If the GUI is killed while connected, the fail-closed firewall remains
  until the user reopens the app and disconnects or runs the helper's `down`
  action as root.

## Audit result

The reviewed connection path is fail-closed for public traffic on the selected
physical interface. This substantially reduces accidental IP and DNS leaks, but
it is not a claim of anonymity and cannot defend against a malicious relay,
privileged malware, application-layer tracking, or kernel compromise.

Report security issues privately to the repository owner rather than opening a
public issue containing exploit details.
