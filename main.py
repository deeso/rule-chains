from rule_chains import get_names, get_patterns, get_grokit_config
from rule_chains.frontend import GrokFrontend

msg = '''<134>Aug 30 21:45:14 filterlog: 143,16777216,,1000018511,igb1,match,pass,out,4,0x0,,63,10592,0,DF,17,udp,1378,188.169.56.209,172.217.9.10,9692,443,1358'''

# PFSense patterns loaded to pygrok
ip_pattern = 'PFSENSE_IP_RULE_V4'
udp_pattern = 'PFSENSE_UDP_RULE_V4'
gr = GrokFrontend(  # default chains configuration
                  config=get_grokit_config(),
                  # patterns created for pfsense filterlog and openvpn
                  custom_patterns_dir=get_patterns(),
                  # patterns to load individual groks for
                  patterns_names=get_names())

# matching the patterns by name
print(gr.match_pattern(ip_pattern, msg))
print(gr.match_pattern(udp_pattern, msg))

# try all the patterns of interest
print(gr.match_any_pattern(msg))
