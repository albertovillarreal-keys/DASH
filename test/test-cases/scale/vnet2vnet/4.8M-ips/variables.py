import ipaddress
import os

import macaddress

ipp = ipaddress.ip_address


ENI_START = 1
ENI_COUNT = 24  # 8
ENI_MAC_STEP = '00:00:00:18:00:00'
ENI_STEP = 1
ENI_L2R_STEP = 1000

PAL = ipp("221.1.0.1")
PAR = ipp("221.2.0.1")

ACL_TABLE_MAC_STEP = '00:00:00:04:00:00'
ACL_POLICY_MAC_STEP = '00:00:00:00:01:00'

ACL_RULES_NSG = 1000  # 1000
ACL_TABLE_COUNT = 5

IP_PER_ACL_RULE = 1  # 128
IP_MAPPED_PER_ACL_RULE = IP_PER_ACL_RULE # 40
IP_ROUTE_DIVIDER_PER_ACL_RULE = 16 # 8, must be a power of 2 number


IP_STEP1 = int(ipp('0.0.0.1'))
IP_STEP2 = int(ipp('0.0.1.0'))
IP_STEP3 = int(ipp('0.1.0.0'))
IP_STEP4 = int(ipp('1.0.0.0'))
IP_STEP_ENI = int(ipp('0.64.0.0')) # IP_STEP4
IP_STEP_NSG = int(ipp('0.4.0.0')) # IP_STEP3 * 4
IP_STEP_ACL = int(ipp('0.0.1.0')) # IP_STEP2 * 2
IP_STEPE = int(ipp('0.0.0.2'))


IP_L_START = ipaddress.ip_address('1.1.0.1')
IP_R_START = ipaddress.ip_address('1.4.0.1')


MAC_L_START = macaddress.MAC('00:1A:C5:00:00:01')
MAC_R_START = macaddress.MAC('00:1B:6E:00:00:01')
