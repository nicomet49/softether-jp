import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "softether_jp.py"
SPEC = importlib.util.spec_from_file_location("softether_jp", MODULE_PATH)
APP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APP
SPEC.loader.exec_module(APP)


class RelayParsingTests(unittest.TestCase):
    def test_filters_japan_validates_ip_and_sorts_score(self):
        payload = """*vpn_servers
#HostName,IP,Score,Ping,Speed,CountryLong,CountryShort,NumVpnSessions,Uptime,TotalUsers,TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64
jp-low,192.0.2.1,10,30,1000000,Japan,JP,1,2,3,4,none,op,msg,x
us,192.0.2.2,100,1,9000000,United States,US,2,3,4,5,none,op,msg,x
jp-high,192.0.2.3,20,20,2000000,Japan,JP,3,4,5,6,none,op,msg,x
bad,not-an-ip,99,1,1,Japan,JP,1,1,1,1,none,op,msg,x
*\n"""
        relays = APP.parse_relays(payload)
        self.assertEqual([relay.host for relay in relays], ["jp-high", "jp-low"])
        self.assertTrue(all(relay.ip.startswith("192.0.2.") for relay in relays))

    def test_empty_response_is_empty(self):
        self.assertEqual(APP.parse_relays("*vpn_servers\n*\n"), [])


if __name__ == "__main__":
    unittest.main()
