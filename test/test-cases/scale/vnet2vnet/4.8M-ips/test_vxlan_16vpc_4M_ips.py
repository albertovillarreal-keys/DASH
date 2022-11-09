import inspect
import json
import sys
import time
from copy import deepcopy

import ipaddress
import macaddress
import pytest
import requests

from hero_helper.hero_helper import HeroHelper
from ixload import IxLoadUtils as IxLoadUtils
from ixnetwork_restpy import SessionAssistant
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant
from tabulate import tabulate
from testdata_vxlan_16vpc_4M_ips import testdata, ip_type
from datetime import datetime
from threading import Thread
from future.utils import iteritems
from variables import *

data = []
final_result_data=[]
setup_information=None
ixnetwork=None
config_elements_sets=[]
val_map={}
tiNo = 16
captions = ["Test","PPS", "Tx Frames", "Rx Frames", "Frames Delta", "Loss %","PossibleBoundary"]


@pytest.fixture(scope="class")
def setup(smartnics, tbinfo,utils):
    """Gather all required test information from DUT and tbinfo.
        A Dictionary with required test information.
    """
    print ("*"*50+"SETUP"+"*"*50)
    setup_information = {"nics": smartnics, "tbinfo": tbinfo, }
    smartnics.configure_target(testdata)
    yield setup_information

def find_boundary(utils):
    global data, final_result_data
    hls = ixnetwork.Traffic.TrafficItem.find()[0].HighLevelStream.find()

    def boundary_check(test_boundary_val):
        for hl in hls:
            hl.FrameRate.update(Type='framesPerSecond', Rate=test_boundary_val)

        utils.start_traffic(ixnetwork)
        utils.ss("\t\t\tLet Traffic run for  ", 10)
        utils.ss("\t\t\tPrint Stats Before issuing Clear Stats  ", 2)
        utils.printStats(ixnetwork, "Traffic Item Statistics", {"Traffic Item Statistics": {'transpose': False, 'toprint': ["Traffic Item", "Tx Frames", "Rx Frames", "Frames Delta", "Loss %"]}})
        utils.ss("\t\t\tLet Clear Stats  ", 2)
        ixnetwork.ClearStats()
        utils.ss("\t\t\tLet Traffic run for another ", 90)
        utils.stop_traffic(ixnetwork)
        utils.ss("\t\t\tLets wait for stats to settle down for ", 10)
        #print("\tVerify Traffic stats")
        ti = StatViewAssistant(ixnetwork, 'Traffic Item Statistics')
        if float(ti.Rows[0]['Frames Delta']) == float(0):
            ixnetwork.ClearStats()
            return False
        else:
            ixnetwork.ClearStats()
            return True

    poss_val, step, tolerance, pass_val, fail_val = int(20000000 / tiNo), int(20000000 / tiNo), 100000, None, None
    #poss_val, step, tolerance, pass_val, fail_val = int(20000000 / tiNo), int(20000000 / tiNo), 50000, None, None

    while True:
        print("="*50)
        print(f"Test running for {utils.human_format(poss_val * tiNo)} framesPerSecond")
        print(" POSSPASS|FAIL|PASS=", poss_val, fail_val, pass_val)
        print("="*50)
        result = boundary_check(poss_val)
        row = utils.printStats(ixnetwork, "Traffic Item Statistics", {"Traffic Item Statistics": {'transpose': False, 'toprint': ["Traffic Item", "Tx Frames", "Rx Frames", "Frames Delta", "Loss %"]}})
        utils.printStats(ixnetwork, "Flow Statistics", {"Flow Statistics": {'transpose': False, 'toprint': ["Traffic Item", "Source/Dest Endpoint Pair", "Tx Frames", "Rx Frames", "Frames Delta", "Loss %"]}})
        data.append([sys._getframe().f_back.f_code.co_name,utils.human_format(poss_val * tiNo)]+row[1:])

        if result:
            fail_val = poss_val
            if pass_val:
                poss_val = int((pass_val+fail_val)/2)
            else:
                poss_val = int(poss_val/2)
        else:  # we need to continue
            pass_val = poss_val
            if not fail_val:
                poss_val = pass_val+step
            else:
                poss_val = int((pass_val+fail_val)/2)
        if fail_val:
            if abs(fail_val-poss_val) <= tolerance:
                if pass_val==None:
                    print ("Not able to find Boundary Tolerance (%d) is Less than last fail value (%d)" % (tolerance,fail_val))
                    pass_val="NA"
                else:
                    pass_val = utils.human_format(pass_val * tiNo)
                    print("Final Possible Boundary is ", pass_val)
                print(" X POSSPASS|FAIL|PASS=", poss_val, fail_val, pass_val)
                break
    data.append([sys._getframe().f_back.f_code.co_name]+["***"]*5+[pass_val])
    print(tabulate(data, headers=captions, tablefmt="psql"))
    
    final_result_data.append([sys._getframe().f_back.f_code.co_name,pass_val])



@pytest.fixture(scope="class")
def pps_config(setup,tbinfo,utils):
    """
        Description: Verify ip address can be configured in SVI.
        Topo: DUT02 ============ DUT01
        Dev. status: DONE
    """
    global ixnetwork,config_elements_sets,val_map
    testbed = setup["tbinfo"]
    snic = setup["nics"]
    def createTI(name, endpoints):
        trafficItem = ixnetwork.Traffic.TrafficItem.find(Name="^%s$" % name)
        if len(trafficItem) == 0:
            trafficItem = ixnetwork.Traffic.TrafficItem.add(Name=name, TrafficType='ipv4', BiDirectional=False)  # BiDirectional=True
        for indx,srcdst in enumerate(endpoints):
            print ("ENP UP",indx+1)
            src,dst = srcdst
            endpoint_set_up = trafficItem.EndpointSet.add(Name="%s-ENI_UP-%s" % (name,str(indx+1)),ScalableSources=src, ScalableDestinations=dst)
            ce = trafficItem.ConfigElement.find()[-1]
            ce.FrameRate.update(Type='framesPerSecond', Rate=50000)
            ce.TransmissionControl.Type = 'continuous'
            ce.FrameRateDistribution.PortDistribution = 'applyRateToAll'
            ce.FrameSize.FixedSize = 128
            udp_srcport = ce.Stack.find(StackTypeId="udp").Field.find(FieldTypeId="udp.header.srcPort")
            udp_srcport.Auto = False
            udp_srcport.SingleValue = 50687
            udp_len = ce.Stack.find(StackTypeId="udp").Field.find(FieldTypeId="udp.header.length")
            udp_len.Auto = False
            udp_len.SingleValue = 80

            udp_template = ixnetwork.Traffic.ProtocolTemplate.find(StackTypeId='^udp$')
            ipv4_template = ce.Stack.find(TemplateName="ipv4-template.xml")[-1]
            inner_udp = ce.Stack.read(ipv4_template.AppendProtocol(udp_template))
            trafficItem.Tracking.find()[0].TrackBy = ['trackingenabled0', 'sourceDestEndpointPair0']
            inn_sp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
            inn_dp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')
            inn_sp.Auto = False
            inn_dp.Auto = False
            inn_sp.SingleValue = 10000
            inn_dp.SingleValue = 10000
            ce_up = ce
            print ("ENP Down",indx+1)
            #DOWN
            endpoint_set_down = trafficItem.EndpointSet.add(Name="%s-ENI_DOWN-%s" % (name,str(indx+1)),ScalableSources=dst, ScalableDestinations=src)
            ce = trafficItem.ConfigElement.find()[-1]
            ce.FrameRate.update(Type='framesPerSecond', Rate=50000)
            ce.TransmissionControl.Type = 'continuous'
            ce.FrameRateDistribution.PortDistribution = 'applyRateToAll'
            ce.FrameSize.FixedSize = 128
            udp_srcport = ce.Stack.find(StackTypeId="udp").Field.find(FieldTypeId="udp.header.srcPort")
            udp_srcport.Auto = False
            udp_srcport.SingleValue = 50687
            udp_len = ce.Stack.find(StackTypeId="udp").Field.find(FieldTypeId="udp.header.length")
            udp_len.Auto = False
            udp_len.SingleValue = 80

            udp_template = ixnetwork.Traffic.ProtocolTemplate.find(StackTypeId='^udp$')
            ipv4_template = ce.Stack.find(TemplateName="ipv4-template.xml")[-1]
            inner_udp = ce.Stack.read(ipv4_template.AppendProtocol(udp_template))
            trafficItem.Tracking.find()[0].TrackBy = ['trackingenabled0', 'sourceDestEndpointPair0']
            inn_sp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
            inn_dp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')
            inn_sp.Auto = False
            inn_dp.Auto = False
            inn_sp.SingleValue = 10000
            inn_dp.SingleValue = 10000
            ce_down=ce
            
            if name=="Allow":
                config_elements_sets.append((ce_up,ce_down))

        print ("Done")
        #trafficItem.Generate()
        print (datetime.now(),"*"*80)
        return trafficItem


    obj_map = {}
    for k in testdata["val_map"].keys():
        obj_map[k] = deepcopy({})
    val_map = testdata["val_map"]

    print('connect to a test tool platform')
    tb=testbed['stateless'][0]

    session_assistant = SessionAssistant(
        IpAddress=tb['server'][0]['addr'],
        RestPort=tb['server'][0]['rest'],
        UserName=testbed["CR"][tb['server'][0]['addr']]['user'],
        Password=testbed["CR"][tb['server'][0]['addr']]['password'],
        SessionName="MIRTest",
        ClearConfig=True
    )

    ixnetwork = session_assistant.Ixnetwork
    

    portList = [{'xpath': '/vport[%s]' % str(indx+1), 'name': 'VTEP_0%d' % (indx+1), 'location': p['location']} for indx, p in enumerate(tb['tgen'][0]['interfaces'])]
    ixnetwork.ResourceManager.ImportConfig(json.dumps(portList), False)

    vports = list(ixnetwork.Vport.find())
    l1data = tb['tgen'][0]['interfaces']
    tmp = [{'xpath': '/vport[%d]/l1Config/%s' % (vp.InternalId, vp.Type), "ieeeL1Defaults": l1data[indx]['ieee'] } for indx, vp in enumerate(vports)]
    ixnetwork.ResourceManager.ImportConfig(json.dumps(tmp), False)
    tmp = [{'xpath': '/vport[%d]/l1Config/%s' % (vp.InternalId, vp.Type), "enableAutoNegotiation": l1data[indx]['an']} for indx, vp in enumerate(vports)]
    ixnetwork.ResourceManager.ImportConfig(json.dumps(tmp), False)
    
    tmp = [{'xpath': '/vport[%d]/l1Config/%s' % (vp.InternalId, vp.Type), "enableRsFec": l1data[indx]['fec'], "autoInstrumentation": "floating"} for indx, vp in enumerate(vports)]
    ixnetwork.ResourceManager.ImportConfig(json.dumps(tmp), False)
    for ed in [1, 2]:
        # OUTER DG
        obj_map[ed]["oeth"] = ixnetwork.Topology.add(Ports=vports[ed-1], Name="TG_%d" % ed).DeviceGroup.add(Name="O_DG_%d" % ed, Multiplier=1).Ethernet.add(Name='ETH_%d' % ed)
        if ip_type=="v4":
            obj_map[ed]["oipv4"] = obj_map[ed]["oeth"].Ipv4.add(Name="IPv4%d" % ed)
        elif ip_type=="v6":
            obj_map[ed]["oipv4"] = obj_map[ed]["oeth"].Ipv6.add(Name="IPv6%d" % ed)

        if val_map[ed]['underlay_routing']=="BGP":
            if ip_type=="v4":
                obj_map[ed]["obgp"] = obj_map[ed]["oipv4"].BgpIpv4Peer.add(Name="BGP_%d" % ed)
            elif ip_type=="v6":
                obj_map[ed]["obgp"] = obj_map[ed]["oipv4"].BgpIpv6Peer.add(Name="BGP_%d" % ed)
                
        # OUTER NG
        ng = ixnetwork.Topology.find().DeviceGroup.find(Name="O_DG_%d" % ed).NetworkGroup.add(Name="NG_%d" % ed, Multiplier=val_map[ed]["oipv4pool"]["multiplier"])
        if ip_type=="v4":
            obj_map[ed]["oipv4pool"] = ng.Ipv4PrefixPools.add(NumberOfAddresses='1')
        elif ip_type=="v6":
            obj_map[ed]["oipv4pool"] = ng.Ipv6PrefixPools.add(NumberOfAddresses='1')

        # DG Behing Outer NG
        obj_map[ed]["dg_b_ong"] = ng.DeviceGroup.add(Name="DG_B_ONG_%d" % ed, Multiplier=1)
        obj_map[ed]["dg_b_ong_eth"] = obj_map[ed]["dg_b_ong"].Ethernet.add(Name='ETH_%d' % ed)
        if ip_type=="v4":
            obj_map[ed]["dg_b_ong_ipv4"] = obj_map[ed]["dg_b_ong_eth"].Ipv4.add(Name='IPv4_%d' % ed)
            obj_map[ed]["vxlan"] = obj_map[ed]["dg_b_ong_ipv4"].Vxlan.add(Name="VXLAN_%d" % ed)
        elif ip_type=="v6":
            obj_map[ed]["dg_b_ong_ipv4"] = obj_map[ed]["dg_b_ong_eth"].Ipv6.add(Name='IPv6_%d' % ed)
            obj_map[ed]["vxlan"] = obj_map[ed]["dg_b_ong_ipv4"].Vxlanv6.add(Name="VXLAN_%d" % ed)
        
        

        # ALLOW & DENY
        if ed==1:
            if ip_type=="v4":
                obj_map[ed]["iipv4_local"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Local',Multiplier=1).Ethernet.add().Ipv4.add()
            elif ip_type=="v6":
                obj_map[ed]["iipv4_local"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Local',Multiplier=1).Ethernet.add().Ipv6.add()
                
            obj_map[ed]["ieth_local"] = obj_map[ed]["iipv4_local"].parent
        else:
            if ip_type=="v4":
                obj_map[ed]["iipv4_allow"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Allow',Multiplier=val_map[ed]["iipv4_allow"]["multiplier"]).Ethernet.add().Ipv4.add()
            elif ip_type=="v6":
                obj_map[ed]["iipv4_allow"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Allow',Multiplier=val_map[ed]["iipv4_allow"]["multiplier"]).Ethernet.add().Ipv6.add()
                
            obj_map[ed]["ieth_allow"] = obj_map[ed]["iipv4_allow"].parent

            if ip_type=="v4":
                obj_map[ed]["iipv4_deny"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Deny',Multiplier=val_map[ed]["iipv4_deny"]["multiplier"]).Ethernet.add().Ipv4.add()
            elif ip_type=="v6":
                obj_map[ed]["iipv4_deny"] = obj_map[ed]["dg_b_ong"].DeviceGroup.add(Name='Deny',Multiplier=val_map[ed]["iipv4_deny"]["multiplier"]).Ethernet.add().Ipv6.add()
            obj_map[ed]["ieth_deny"] = obj_map[ed]["iipv4_deny"].parent


    for ed in [1, 2]:
        # OUTER DG
        obj_map[ed]["oeth"].Mac.Increment(start_value=val_map[ed]["oeth"]["mac"],  step_value='00:00:00:00:00:01')
        obj_map[ed]["oipv4"].Address.Increment(start_value=val_map[ed]["oipv4"]["ip"],  step_value=val_map[ed]["oipv4"]["ip_step"])
        obj_map[ed]["oipv4"].GatewayIp.Increment(start_value=val_map[ed]["oipv4"]["gip"], step_value=val_map[ed]["oipv4"]["gip_step"])
        
        
        resolve_gateway = False
        if val_map[ed]['underlay_routing']=="STATIC":
            resolve_gateway = True
            
        obj_map[ed]["oipv4"].ResolveGateway.Single(resolve_gateway)
        obj_map[ed]["oipv4"].ManualGatewayMac.Single(val_map[ed]["oipv4"]["mac"])

        # BGP
        if val_map[ed]['underlay_routing']=="BGP":
            obj_map[ed]["obgp"].DutIp.Single(val_map[ed]["obgp"]["dip"])
            obj_map[ed]["obgp"].LocalAs2Bytes.Single(val_map[ed]["obgp"]["las"])
            if ip_type=="v4":
                obj_map[ed]["obgp"].EnableBgpIdSameasRouterId.Single(True)
                obj_map[ed]["obgp"].FilterIpV4Unicast.Single(True)
            elif ip_type=="v6":
                #obj_map[ed]["obgp"].EnableBgpIdSameasRouterId.Single(True)----------------------------> This gives an error
                obj_map[ed]["obgp"].FilterIpV6Unicast.Single(True)
            
            obj_map[ed]["obgp"].FilterEvpn.Single(True)

            #obj_map[ed]["bgp"].IpVrfToIpVrfType = 'interfacefullWithUnnumberedCorefacingIRB'
            #obj_map[ed]["bgp"].EthernetSegmentsCountV4 = 128

            obj_map[ed]["obgp"].BgpId.Single(val_map[ed]["obgp"]["bid"])
            obj_map[ed]["obgp"].Type.Single('external')

        # OUTER NG
        obj_map[ed]["oipv4pool"].NetworkAddress.Increment(start_value=val_map[ed]["oipv4pool"]["ip"], step_value=val_map[ed]["oipv4pool"]["ip_step"])
        obj_map[ed]["oipv4pool"].PrefixLength.Single(32)
        ipv4_behindvxlan = obj_map[ed]["vxlan"].parent
        ipv4_behindvxlan.Address.Increment(start_value=val_map[ed]["oipv4pool"]["ip"],  step_value=val_map[ed]["oipv4pool"]["ip_step"])
        ipv4_behindvxlan.ResolveGateway.Single(False)

        # DG Behing Outer NG
        # DG Behind Outer NG Ethernet
        eth = obj_map[ed]["dg_b_ong_ipv4"].parent
        eth.Mac.Increment(start_value=val_map[ed]["dg_b_ong_eth"]["mac"], step_value='00:00:00:00:00:01')

        # DG Behind Outer NG IPv4
        for s in obj_map[ed]["dg_b_ong_ipv4"].Address.Steps:
            s.Enabled = False
        obj_map[ed]["dg_b_ong_ipv4"].Address.Increment(start_value=val_map[ed]["dg_b_ong_ipv4"]["ip"],  step_value=val_map[ed]["dg_b_ong_ipv4"]["ip_step"])
        obj_map[ed]["dg_b_ong_ipv4"].GatewayIp.Increment(start_value=val_map[ed]["dg_b_ong_ipv4"]["gip"], step_value=val_map[ed]["dg_b_ong_ipv4"]["gip_step"])
        obj_map[ed]["dg_b_ong_ipv4"].Prefix.Single(32)
            
        # VXLAN
        obj_map[ed]["vxlan"].EnableStaticInfo = True

        if ip_type=="v4":
            vxlan_sinfo=obj_map[ed]["vxlan"].VxlanStaticInfo
            vxlan_sinfo.MacStaticConfig.Single(True)
            remote_vtep_ip_obj = vxlan_sinfo.RemoteVtepIpv4
            remote_vm_mac = vxlan_sinfo.RemoteVmStaticMac
        elif ip_type=="v6":
            vxlan_sinfo=obj_map[ed]["vxlan"].VxlanIPv6StaticInfo
            vxlan_sinfo.EnableManualRemoteVMMac.Single(True)
            remote_vtep_ip_obj = vxlan_sinfo.RemoteVtepUnicastIpv6
            remote_vm_mac = vxlan_sinfo.RemoteVMMacAddress
        
        

        remote_vtep_ip_obj.Single(val_map[ed]["vxlan"]["RemoteVtepIpv4"])
        obj_map[ed]["vxlan"].Vni.Increment(start_value=val_map[ed]["vxlan"]["Vni"], step_value=1)
        vxlan_sinfo.SuppressArp.Single(True)
        obj_map[ed]["vxlan"].StaticInfoCount = val_map[ed]["vxlan"]["StaticInfoCount"]


        # LOCAL | ALLOW & DENY
        if ed==1:

            remote_vm_mac.Custom(
                                        start_value=val_map[ed]["vxlan"]["RemoteVmStaticMac"]["start_value"],
                                        step_value=val_map[ed]["vxlan"]["RemoteVmStaticMac"]["step_value"],
                                        increments=val_map[ed]["vxlan"]["RemoteVmStaticMac"]["increments"]
                                        )
            remote_vm_mac.Steps[0].Enabled = True
            remote_vm_mac.Steps[0].Step = val_map[ed]["vxlan"]["RemoteVmStaticMac"]["ng_step"]

            vxlan_sinfo.RemoteVmStaticIpv4.Custom(
                                        start_value=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["start_value"],
                                        step_value=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["step_value"],
                                        increments=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["increments"]
                                        )
            vxlan_sinfo.RemoteVmStaticIpv4.Steps[0].Enabled = True
            vxlan_sinfo.RemoteVmStaticIpv4.Steps[0].Step = val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["ng_step"]
            
            
            obj_map[ed]["ieth_local"].Mac.Increment(start_value=val_map[ed]["ieth_local"]["mac"],  step_value=val_map[ed]["ieth_local"]["step"],)
            obj_map[ed]["ieth_local"].Mac.Steps[1].Enabled=True
            obj_map[ed]["ieth_local"].Mac.Steps[1].Step = '00:00:00:08:00:00'
                
            obj_map[ed]["iipv4_local"].Prefix.Single(8)
                
            obj_map[ed]["iipv4_local"].Address.Increment(  start_value=val_map[ed]["iipv4_local"]["ip"],  step_value=val_map[ed]["iipv4_local"]["ip_step"])
            obj_map[ed]["iipv4_local"].Address.Steps[1].Enabled=True
            obj_map[ed]["iipv4_local"].Address.Steps[1].Step = val_map[ed]["iipv4_local"]["ip_ng1_step"]
                
            obj_map[ed]["iipv4_local"].GatewayIp.Increment(start_value=val_map[ed]["iipv4_local"]["gip"], step_value=val_map[ed]["iipv4_local"]["gip_step"])
            obj_map[ed]["iipv4_local"].GatewayIp.Steps[1].Enabled=True
            obj_map[ed]["iipv4_local"].GatewayIp.Steps[1].Step = val_map[ed]["iipv4_local"]["gip_ng1_step"]

                
        else:

            remote_vm_mac.Increment(start_value=val_map[ed]["vxlan"]["RemoteVmStaticMac"],step_value='00:00:00:00:00:01')
            remote_vm_mac.Steps[0].Enabled =True
            remote_vm_mac.Steps[0].Step = '00:00:00:08:00:00'
                
            #vxlan_sinfo.RemoteVmStaticIpv4.Increment(start_value=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"],step_value='0.0.0.1')
            vxlan_sinfo.RemoteVmStaticIpv4.Custom(
                                        start_value=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["start_value"],
                                        step_value=val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["step_value"],
                                        )
            
            vxlan_sinfo.RemoteVmStaticIpv4.Steps[0].Enabled =True
            vxlan_sinfo.RemoteVmStaticIpv4.Steps[0].Step = val_map[ed]["vxlan"]["RemoteVmStaticIpv4"]["ng_step"]

            eth_allow   = obj_map[ed]["ieth_allow"]
            ip_allow    = obj_map[ed]["iipv4_allow"]
            eth_deny    = obj_map[ed]["ieth_deny"]
            ip_deny     = obj_map[ed]["iipv4_deny"]


            eth_allow.Mac.Custom(
                                    start_value=val_map[ed]["ieth_allow"]["mac"]["start_value"],
                                    step_value =val_map[ed]["ieth_allow"]["mac"]["step_value"],
                                    increments =val_map[ed]["ieth_allow"]["mac"]["increments"]
                                    )
                                    
            eth_allow.Mac.Steps[1].Enabled = True
            eth_allow.Mac.Steps[1].Step = val_map[ed]["ieth_allow"]["mac"]["ng_step"]

            ip_allow.Address.Custom(
                                    start_value=val_map[ed]["iipv4_allow"]["ip"]["start_value"],
                                    step_value =val_map[ed]["iipv4_allow"]["ip"]["step_value"],
                                    increments =val_map[ed]["iipv4_allow"]["ip"]["increments"]
                                    )
            ip_allow.Address.Steps[1].Enabled = True
            ip_allow.Address.Steps[1].Step = val_map[ed]["iipv4_allow"]["ip"]["ng_step"]

            ip_allow.Prefix.Single(8)
            
            ip_allow.GatewayIp.Increment(start_value=val_map[ed]["iipv4_allow"]["gip"], step_value=val_map[ed]["iipv4_allow"]["gip_step"])         #Fix Increments
            ip_allow.GatewayIp.Steps[1].Enabled=True
            ip_allow.GatewayIp.Steps[1].Step = val_map[ed]["iipv4_allow"]["gip_ng_step"]
                

            eth_deny.Mac.Custom(
                                    start_value=val_map[ed]["ieth_deny"]["mac"]["start_value"],
                                    step_value =val_map[ed]["ieth_deny"]["mac"]["step_value"],
                                    increments =val_map[ed]["ieth_deny"]["mac"]["increments"]
                                    )
            eth_deny.Mac.Steps[1].Enabled = True
            eth_deny.Mac.Steps[1].Step = val_map[ed]["ieth_deny"]["mac"]["ng_step"]

            ip_deny.Address.Custom(
                                    start_value=val_map[ed]["iipv4_deny"]["ip"]["start_value"],
                                    step_value =val_map[ed]["iipv4_deny"]["ip"]["step_value"],
                                    increments =val_map[ed]["iipv4_deny"]["ip"]["increments"]
                                    )
                                    
            ip_deny.Address.Steps[1].Enabled = True
            ip_deny.Address.Steps[1].Step = val_map[ed]["iipv4_deny"]["ip"]["ng_step"]

            ip_deny.Prefix.Single(8)


            ip_deny.GatewayIp.Increment(start_value=val_map[ed]["iipv4_deny"]["gip"], step_value=val_map[ed]["iipv4_deny"]["gip_step"])           #Fix Increments
            ip_deny.GatewayIp.Steps[1].Enabled=True
            ip_deny.GatewayIp.Steps[1].Step = val_map[ed]["iipv4_deny"]["gip_ng_step"]

    print("Create Traffic OneIPOneVPC")
    if ip_type=="v4":
        ipv4_local = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Local").Ethernet.find().Ipv4.find()
        ipv4_allow = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Allow").Ethernet.find().Ipv4.find()
        ipv4_deny  = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Deny").Ethernet.find().Ipv4.find()
    elif ip_type=="v6":    
        ipv4_local = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Local").Ethernet.find().Ipv6.find()
        ipv4_allow = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Allow").Ethernet.find().Ipv6.find()
        ipv4_deny  = ixnetwork.Topology.find().DeviceGroup.find().NetworkGroup.find().DeviceGroup.find().DeviceGroup.find(Name="Deny").Ethernet.find().Ipv6.find()
    print("Create Traffic OneIPOneVPC")
    
    vpcs, ips = val_map[1]["oipv4pool"]["multiplier"], int(val_map[1]["vxlan"]["StaticInfoCount"]/2)
    endpoints_allow,endpoints_deny=[], []
    
    for vpc in range(vpcs):
        endpoints_allow.append(
                            (
                            deepcopy([{"arg1": ipv4_local.href,"arg2": 1,"arg3": 1,"arg4": vpc+1,"arg5": 1  }]),
                            deepcopy([{"arg1": ipv4_allow.href,"arg2": 1,"arg3": 1,"arg4": vpc*ips+1,"arg5": ips  }])
                            )
                          )
        endpoints_deny.append(
                            (
                            deepcopy([{"arg1": ipv4_local.href,"arg2": 1,    "arg3": 1,    "arg4": vpc+1,    "arg5": 1  }]),
                            deepcopy([{"arg1": ipv4_deny.href ,"arg2": 1,    "arg3": 1,    "arg4": vpc*ips+1,    "arg5": ips  }])
                            )
                          )

    ti_allow = createTI("Allow", endpoints_allow)
    ti_deny = createTI("Deny",  endpoints_deny)


#@pytest.mark.usefixtures("pps_config")
class Test_Dpu:

    def teardown_method(self, method):
        print("Clean up configuration")

    def make_request(self, method, url, rdata):

        headers = {'Accept': 'application/json'}
        if method == 'DELETE':
            response = requests.delete(url, headers=headers, params=str(rdata))
        elif method == 'GET':
            response = requests.get(url, headers=headers, params=rdata)
        elif method == 'POST':
            headers = {
                'Accept': 'application/json',
                'Content-type': 'application/json'
            }
            response = requests.post(url, headers=headers, json=rdata)
        elif method == 'PATCH':
            response = requests.patch(url, json=rdata)
        else:
            raise ValueError()

        if response.status_code == 200 or response.status_code == 204:
            return response.json()
        else:
            print("Error while making {} request to {} (error code {}) response from server: {}".format(method, url,
                                                                                                        response.status_code,
                                                                                                        response.text))
        return None

    def test_pps_001(self, setup, utils):
        print('Start All Protocols test_pps_001')
        ixnetwork.StartAllProtocols(Arg1='sync')

        try:
            print('Verify protocol sessions')
            protocolsSummary = StatViewAssistant(ixnetwork, 'Protocols Summary')
            protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, 0)
            protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, 0)
        except Exception as e:
            raise Exception(str(e))
        time.sleep(90)

        ti_allow = ixnetwork.Traffic.TrafficItem.find(Name="Allow")
        ti_deny  = ixnetwork.Traffic.TrafficItem.find(Name="Deny")
        ti_allow.Generate()
        ti_deny.Generate()
        ixnetwork.Traffic.Apply()
        utils.start_traffic(ixnetwork)
        time.sleep(30)
        utils.stop_traffic(ixnetwork)
        
        find_boundary(utils)
        print(tabulate(final_result_data, headers=["Test","Max Possible PPS"], tablefmt="psql"))

    def test_pps_increment_udp(self, setup, utils):

        print('Start All Protocols test_pps_random_udp_src_dst')
        ixnetwork.StartAllProtocols(Arg1='sync')
        try:
            print('Verify protocol sessions')
            protocolsSummary = StatViewAssistant(ixnetwork, 'Protocols Summary')
            protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, 0)
            protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, 0)
        except Exception as e:
            raise Exception(str(e))

        trafficItem = ixnetwork.Traffic.TrafficItem.find(Name="Deny")
        if len(trafficItem)==1:
            trafficItem.Enabled=False
        ti_allow =  ixnetwork.Traffic.TrafficItem.find(Name="Allow")
        vm_start_value=9000
        host_start_value=10000
        host_step = 5000
        endpoint_sets = ti_allow.EndpointSet.find()
        #for ep_up,ep_down in endpoint_sets:
        for ce_up,ce_down in config_elements_sets:
            print (ce_up,ce_down)
            inner_udp = ce_up.Stack.find(TemplateName="udp-template.xml")[-1]
            inn_sp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
            inn_dp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')
            inn_sp.ValueType = "singleValue"
            inn_dp.ValueType = "increment"
            inn_sp.SingleValue = vm_start_value
            inn_dp.StartValue = host_start_value
            inn_dp.StepValue = 1
            inn_dp.CountValue = int(val_map[1]["vxlan"]["StaticInfoCount"]/2)


            inner_udp = ce_down.Stack.find(TemplateName="udp-template.xml")[-1]
            inn_sp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
            inn_dp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')
            inn_sp.ValueType = "increment"
            inn_dp.ValueType = "singleValue"
            inn_dp.SingleValue = vm_start_value
            inn_sp.StartValue = host_start_value
            inn_sp.StepValue = 1
            inn_sp.CountValue = int(val_map[1]["vxlan"]["StaticInfoCount"]/2)

            
            
            vm_start_value+=1
            host_start_value=host_start_value+host_step

        ti_allow.Generate()
        ixnetwork.Traffic.Apply()
        utils.start_traffic(ixnetwork)
        time.sleep(30)
        utils.stop_traffic(ixnetwork)

        find_boundary(utils)
        print(tabulate(final_result_data, headers=["Test","Max Possible PPS"], tablefmt="psql"))

    def test_cps_001(self, setup, create_hero_config, utils):
        """
            Description: Verify ip address can be configured in SVI.
            Topo: DUT02 ============ DUT01
            Dev. status: DONE
        """
        stats_dict = {}
        location = inspect.getfile(inspect.currentframe())

        tcp_cps_settings = deepcopy(create_hero_config['ixl'])
        tcp_bg_settings = deepcopy(create_hero_config['ixl'])

        hero_tcp_cps = HeroHelper(tcp_cps_settings, test_config_type='cps', id=1)
        hero_tcp_bg = HeroHelper(tcp_bg_settings, test_config_type='tcp_bg', id=2)
        hero_udp_bg = HeroHelper(create_hero_config, test_config_type='udp_bg', id=3)

        ## RUN
        IxLoadUtils.log('Starting udp bg traffic')
        utils.start_traffic(hero_udp_bg.ixnetwork)
        time.sleep(30)

        hero_tcp_cps.run2(hero_tcp_bg)

        IxLoadUtils.log("Stopping udp bg traffic")
        utils.stop_traffic(hero_udp_bg.ixnetwork)
