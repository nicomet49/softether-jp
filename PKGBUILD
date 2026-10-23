pkgname=softether-jp
pkgver=0.1.0
pkgrel=1
pkgdesc="Native GTK client for Japanese VPN Gate relays using SoftEther"
arch=('any')
url="https://github.com/nicomet49/softether-jp"
license=('MIT')
depends=('gtk4' 'networkmanager' 'nftables' 'polkit' 'python' 'python-gobject' 'python-requests' 'softethervpn')
source=('softether_jp.py' 'relays.py' 'softether-jp-helper' 'net.vpngate.SoftEtherJapan.desktop')
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
  install -Dm755 "$srcdir/softether_jp.py" "$pkgdir/usr/lib/softether-jp/softether_jp.py"
  install -Dm644 "$srcdir/relays.py" "$pkgdir/usr/lib/softether-jp/relays.py"
  install -d "$pkgdir/usr/bin"
  ln -s /usr/lib/softether-jp/softether_jp.py "$pkgdir/usr/bin/softether-jp"
  install -Dm755 "$srcdir/softether-jp-helper" "$pkgdir/usr/libexec/softether-jp-helper"
  install -Dm644 "$srcdir/net.vpngate.SoftEtherJapan.desktop" \
    "$pkgdir/usr/share/applications/net.vpngate.SoftEtherJapan.desktop"
}
