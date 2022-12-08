from ixload import IxLoadUtils as IxLoadUtils
from ixnetwork_restpy import SessionAssistant
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant
from copy import deepcopy
from tabulate import tabulate
from future.utils import iteritems

import sys
sys.path.append('../.')
from variables import *
from threading import Thread

import ipaddress
import macaddress
import requests
import json
import time


class HeroHelper:
    save_rxf_path = "C:\\automation\\"

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    url_patch_dict = {
        'base_url': '',
        'split_networks': True,
        'traffic_maps': {
            'meshType_setting': {'meshType': 'vlanRangePairs'},
            #'meshType_setting': {'meshType': 'ipRangePairs'},
            'subMapsIPv4_url': "/ixload/test/activeTest/communityList/0/activityList/0/destinations/0/customPortMap/submapsIPv4/0",
            'destinations_url': "/ixload/test/activeTest/communityList/0/activityList/0/destinations/0"
        },
        'allow_routes': {
            'json': {'allowRouteConflicts': True},
            'url': "/ixload/preferences"
        },
        'auto_mac_setting': {
            "autoMacGeneration": False
        },
        'userObjectiveType_cps': "connectionRate",
        'userObjectiveType_tcp_bg': "concurrentConnections",
        'initial_objective': 15000000,
        'initial_objective_tcp_bg': 4000000,
        'threshold': 100000,
        'target_failures': 1000,
        'MAX_CPS': 32000000,
        'MIN_CPS': 0,
        'ip_settings': {
            'client': {
                'host_count': 128000,
                'increment_by': "0.0.0.2"
            },
            'server': {
                'host_count': 1,
                'increment_by': "0.0.0.2"
            },
        },
        'ip_settings_babyhero': {
            'client': {
                'host_count': 500,
                'increment_by': "0.0.2.0"
            },
            'server': {
                'host_count': 1,
                'increment_by': "0.0.0.2"
            },
        },
        'mac_settings': {
            'client': {'increment': "00:00:00:00:00:02"},
            'server': {'increment': "00:00:00:00:00:02"}
        },
        'mac_settings_babyhero': {
            'client': {'increment': "00:00:00:00:02:00"},
            'server': {'increment': "00:00:00:00:00:02"}
        },
        'timeline_settings': {
            # basic timeline
            'timelineType': 0,
            'url': "/ixload/test/activetest/communitylist/0/activitylist/0/timeline",
            'activitylist_url': "/ixload/test/activetest/communitylist/0/activitylist/0",
            'advanced': {
                'rampUpValue': 1000000,
                'sustainTime': 240,
            },
            'activitylist_cps': {
                'constraintType': 'SimulatedUserConstraint',
                'secondaryConstraintType': 'SimulatedUserConstraint',
                'constraintValue': 3150,
                'enableConstraint': True,
            },
            'activitylist_constraint_cps': {
                'constraintType': 'SimulatedUserConstraint',
            },
            'basic_cps': {
                'rampDownTime': 20,
                'rampDownValue': 0,
                'rampUpInterval': 1,
                'rampUpValue': 3150,
                'standbyTime': 0,
                'sustainTime': 240,
            },
            'basic_tcp_bg': {
                'rampDownTime': 20,
                'rampDownValue': 0,
                'rampUpInterval': 1,
                'standbyTime': 0,
                'sustainTime': 300,
            },
            'advancedIteration': {
                'd0': {'duration': 30, 'endObjectiveScale': 0},
                'd1': {'duration': 20, 'endObjectiveScale': 0.1000002875},
                'd2': {'duration': 200, 'endObjectiveScale': 0.1000002875},
                'd3': {'duration': 10, 'endObjectiveScale': 0.1000002875},
                'd4': {'duration': 10, 'endObjectiveScale': 0},
            },
            'advancedIteration_tcp_bg': {
                'd0': {'duration': 20, 'endObjectiveScale': 0.1000002875},
                'd1': {'duration': 200, 'endObjectiveScale': 0.1000002875},
                'd2': {'duration': 10, 'endObjectiveScale': 0.1000002875},
                'd3': {'duration': 10, 'endObjectiveScale': 0},
            },
        },
        'client_range_setting': {
            'json': {},
            'url': "/ixload/test/activeTest/communityList/0/network/stack/childrenList/2/childrenList/3/rangeList/%s"
        },
        'server_range_setting': {
            'json': {},
            'url': "/ixload/test/activeTest/communityList/1/network/stack/childrenList/5/childrenList/6/rangeList/%s"
        },
        'client_vlan_settings': {
            'json': {'firstId': ENI_START + ENI_L2R_STEP, 'uniqueCount': 1},
            'url': "/ixload/test/activeTest/communityList/0/network/stack/childrenList/2/childrenList/3/rangeList/%s/vlanRange"
        },
        'server_vlan_settings': {
            'json': {'firstId': ENI_START, 'uniqueCount': 1},
            'url': "/ixload/test/activeTest/communityList/1/network/stack/childrenList/5/childrenList/6/rangeList/%s/vlanRange"
        },
        'http_version': {
            'json': {"httpVersion": 0},
            'url': "/ixload/test/activeTest/communityList/0/activityList/0/agent"
        },
        'http_version_tcp_bg': {
            'json': {'httpVersion': 1},
            'url': "/ixload/test/activeTest/communityList/0/activityList/0/agent"
        },
        'http_tcp_conns_per_user': {
            'json': {'maxSessions': 1},
            'url': "/ixload/test/activeTest/communityList/0/activityList/0/agent"
        },
        'http_tcp_max_persist': {
            'json': {'maxPersistentRequests': 0},
            'url': "/ixload/test/activeTest/communityList/0/activityList/0/agent"
        },
        'http_ssl_version': {
            'json': {'sslVersion': 5},
            'url': "/ixload/test/activeTest/communityList/0/activityList/0/agent"
        },
        'tcp_adjust_tcp_buffers': {
            'json': {'adjust_tcp_buffers': False, 'tcp_rmem_default': 1024, 'tcp_wmem_default': 1024},
            'url': "/ixload/test/activeTest/communityList/0/network/globalPlugins/2"
        },
        'client_disable_tcp_tw_recycle': {
            'json': {'tcp_tw_recycle': False},
            'url': "/ixload/test/activeTest/communityList/0/network/globalPlugins/2"
        },
        'server_disable_tcp_tw_recycle': {
            'json': {"tcp_tw_recycle": False},
            'url': "/ixload/test/activeTest/communityList/1/network/globalPlugins/5"
        },
        'client_tcp_tw_rfc1323': {
            'json': {'tcp_tw_rfc1323_strict': True},
            'url': "/ixload/test/activeTest/communityList/0/network/globalPlugins/2"
        },
        'server_tcp_tw_rfc1323': {
            'json': {"tcp_tw_rfc1323_strict": True},
            'url': "/ixload/test/activeTest/communityList/1/network/globalPlugins/5"
        },
        'stats_configured': {
            'url': "/ixload/stats/HTTPClient/configuredStats"
        },
        'cps_aggregation_type': {
            'json': {'aggregationType': "kRate"},
            'url': ""
        },
        'cps_stat_caption': {
            'json': {'caption': "TCP CPS"},
            'url': ""
        }
    }

    kCommunities = [
        # format: {option1: value1, option2: value2}
        {},  # default community with no options
        {'tcpAccelerationAllowedFlag': True},  # community with tcpAccelerationAllowedFlag set to True
    ]

    kActivities = {
        'Traffic1@Network1': ['HTTP Client'],
        'Traffic2@Network2': ['HTTP Server']
    }

    kNewCommands_tcp_bg = {
        # format: { agent name : [ { field : value } ] }
        'HTTPClient1': [
            {
                'commandType': "LoopBeginCommand",
                'LoopCount': "20000",
            },
            {
                'commandType': "GET",
                'destination': "Traffic2_HTTPServer1:80",
                'pageObject': "/1b.html",
            },
            {
                'commandType': "THINK",
                'maximumInterval': "950",
                'minimumInterval': "950",

            },
            {
                'commandType': "LoopEndCommand",
            },
        ],
    }

    kNewCommands_cps = {
        # format: { agent name : [ { field : value } ] }
        'HTTPClient1': [
            {
                'commandType': "GET",
                'destination': "Traffic2_HTTPServer1:80",
                'pageObject': "/1b.html",
            },
        ],
    }

    stats_test_settings = {
        'HTTPClient': ['HTTP Simulated Users',
                       'HTTP Concurrent Connections',
                       'TCP CPS',
                       'HTTP Connect Time (us)',
                       ],
        'HTTPServer': ['HTTP Requests Failed',
                       'TCP Retries',
                       'TCP Resets Sent',
                       'TCP Resets Received',
                       ],
    }
    vlan_enabled = {'enabled': True}

    def __init__(self, create_hero_config, test_config_type, id):

        # Configure right traffic generator
        self.id = id
        self.test_config_type = test_config_type

        if self.test_config_type == 'udp_bg':
            self.ixnetwork = self._createconfig_ixn(create_hero_config, create_hero_config['num_of_cards'])
        else:
            # Adjust these values by number of cards used in test if needed
            self.user_init_obj = self.url_patch_dict['initial_objective']
            self.user_init_obj_tcp_bg = self.url_patch_dict['initial_objective_tcp_bg']
            self.eni_count = ENI_COUNT

            # Network settings used for generating client and server networks
            self.split_networks = self.url_patch_dict['split_networks']  # If True assigns odd ENIs to IxL test
            self.enis = self.eni_count
            self.ip_ranges_per_vpc = ACL_TABLE_COUNT * 2
            self.nsgs = self.enis * self.ip_ranges_per_vpc
            self.ip_client_range_adjust = 0
            self.ip_server_range_adjust = 0

            # Specific test object info created here
            self.session = create_hero_config
            self.connection = self.session['connection']
            self.test_settings = self.session['test_settings']
            self.slot_total = self._adjust_to_port_settings()

            # adjust MAX_CPS stat to slot_total
            if self.split_networks is True:
                self.url_patch_dict['MAX_CPS'] = int((self.slot_total-1) * 1000000 * 4.5)
            else:
                self.url_patch_dict['MAX_CPS'] = int(self.slot_total * 1000000 * 4.5)

            self.test_run_results = []
            self.test_iteration = 0
            self.test_value = 0
            self.obtained_cps = 0
            self.MAX_CPS = self.url_patch_dict['MAX_CPS']
            self.MIN_CPS = self.url_patch_dict['MIN_CPS']

            self.session_url = IxLoadUtils.createNewSession(self.connection, self.test_settings.ixLoadVersion)
            self.session_no = int(self.session_url.split('/')[1])
            self.base_url = "http://" + self.test_settings.gatewayServer + ":{}".format(self.test_settings.gatewayPort) + \
                       "/api/v1/" + self.session_url

            self.url_patch_dict['base_url'] = self.base_url

            ## build up config and save rxf but don't runit
            self._build_config()

    def __del__(self):
        try:
            IxLoadUtils.deleteAllSessions(self.connection)
        except:
            pass

    def _adjust_cps_stat(self):

        #  Change TCP Connections Established to CPS caption name and to use kRate aggregationType
        stats_configured_url = self.url_patch_dict['base_url'] + self.url_patch_dict['stats_configured']['url']
        response = requests.get(stats_configured_url, params=None)
        stat_url_list = response.json()
        for stat in stat_url_list:
            if stat['caption'] == 'TCP Connections Established':
                objectID = stat['objectID']

        cps_url = self.url_patch_dict['stats_configured']['url'] + '/' + str(objectID)
        self.url_patch_dict['cps_aggregation_type']['url'] = cps_url
        self.url_patch_dict['cps_stat_caption']['url'] = cps_url

        response = self._patch_test_setting(self.url_patch_dict, 'cps_aggregation_type')
        response = self._patch_test_setting(self.url_patch_dict, 'cps_stat_caption')

    def _adjust_to_port_settings(self):

        slot_total = len(self.test_settings.portListPerCommunity['Traffic1@Network1'])

        traffic1 = deepcopy(self.test_settings.portListPerCommunity['Traffic1@Network1'])
        traffic2 = deepcopy(self.test_settings.portListPerCommunity['Traffic2@Network2'])

        if self.test_config_type == 'cps':
            del traffic1[-1]
            del traffic2[-1]
            self.test_settings.portListPerCommunity['Traffic1@Network1'] = traffic1
            self.test_settings.portListPerCommunity['Traffic2@Network2'] = traffic2
        elif self.test_config_type == 'tcp_bg':
            self.test_settings.portListPerCommunity['Traffic1@Network1'] = [traffic1[-1]]
            self.test_settings.portListPerCommunity['Traffic2@Network2'] = [traffic2[-1]]

        if slot_total == 4:
            self.user_init_obj = 3600000
            self.user_init_obj_tcp_bg = 1000000
            self.url_patch_dict['initial_objective'] = self.user_init_obj
            self.url_patch_dict['initial_objective_tcp_bg'] = self.user_init_obj_tcp_bg
            self.enis = ENI_COUNT
            self.nsgs = self.enis * self.ip_ranges_per_vpc

        return slot_total

    def _adjust_tcp_settings(self):
        if self.test_config_type == 'cps':
            IxLoadUtils.log("Adjusting Test Settings, TCP, HTTP session {}...".format(self.session_no))
            response = self._patch_test_setting(self.url_patch_dict, 'http_version')
        elif self.test_config_type == 'tcp_bg':
            IxLoadUtils.log("Adjusting Test Settings, TCP, HTTP session {}...".format(self.session_no))
            response = self._patch_test_setting(self.url_patch_dict, 'http_version_tcp_bg')
            response = self._patch_test_setting(self.url_patch_dict, 'http_tcp_max_persist')
            response = self._patch_test_setting(self.url_patch_dict, 'http_ssl_version')
            response = self._patch_test_setting(self.url_patch_dict, 'tcp_adjust_tcp_buffers')

        response = self._patch_test_setting(self.url_patch_dict, 'http_tcp_conns_per_user')

    def _adjust_timeline_settings(self):

        IxLoadUtils.log("Adjusting Test Timeline settings session {}...".format(self.session_no))
        url_timeline = self.url_patch_dict['base_url'] + self.url_patch_dict['timeline_settings']['url']
        url_activitylist = self.url_patch_dict['base_url'] + \
                                self.url_patch_dict['timeline_settings']['activitylist_url']
        if self.url_patch_dict['timeline_settings']['timelineType'] == 0:
            if self.test_config_type == 'cps':
                activitylist_json = self.url_patch_dict['timeline_settings']['activitylist_cps']
                activitylist_constraint_json = self.url_patch_dict['timeline_settings']['activitylist_constraint_cps']
                timeline_json = self.url_patch_dict['timeline_settings']['basic_cps']

                response = requests.patch(url_timeline, json=timeline_json)
                response = requests.patch(url_activitylist, json=activitylist_json)
                response = requests.patch(url_activitylist, json=activitylist_constraint_json)
            else:
                timeline_json = self.url_patch_dict['timeline_settings']['basic_tcp_bg']
                response = requests.patch(url_timeline, json=timeline_json)
        else:
            timelineType_json = {'timelineType': self.url_patch_dict['timeline_settings']['timelineType']}
            response = requests.patch(url_timeline, json=timelineType_json)

            timeline_json = self.url_patch_dict['timeline_settings']['advanced']
            response = requests.patch(url_timeline, json=timeline_json)

            if self.test_config_type == 'cps':
                if len(self.url_patch_dict['timeline_settings']['advancedIteration']) > 4:
                    timelines_to_create = len(self.url_patch_dict['timeline_settings']['advancedIteration']) - 4

                    url_new_segmentList = url_timeline + "/advancedIteration/segmentList"
                    for segmentList in range(timelines_to_create):
                        data = {'segmentType': 'Linear Segment'}
                        response = requests.post(url_new_segmentList, headers=self.headers, data=json.dumps(data))

            advanced_url = url_timeline + "/advancedIteration/segmentList/%s"

            if self.test_config_type == 'cps':
                for i in range(len(self.url_patch_dict['timeline_settings']['advancedIteration'])):
                    url = advanced_url % (i)
                    d_json = self.url_patch_dict['timeline_settings']['advancedIteration']['d{}'.format(i)]
                    response = requests.patch(url, json=d_json)
            elif self.test_config_type == 'tcp_bg':
                for i in range(len(self.url_patch_dict['timeline_settings']['advancedIteration_tcp_bg'])):
                    url = advanced_url % (i)
                    d_json = self.url_patch_dict['timeline_settings']['advancedIteration_tcp_bg']['d{}'.format(i)]
                    response = requests.patch(url, json=d_json)

    def _build_config(self):

        # typical IxLoad config happens here
        self._create_ixl_foundations(self.connection, self.session_url)

        # client/server IP ranges created here
        ip_range_list = self._create_ip_ranges_info(self.connection, self.session_url, self.nsgs,
                                                    self.enis, self.ip_ranges_per_vpc)
        self.client_ip_range_names = ip_range_list[0]
        self.client_range_list_info = ip_range_list[1]
        self.server_ip_range_names = ip_range_list[2]
        self.server_range_list_info = ip_range_list[3]

        # Create Client/Server Networks
        client_ipmacvlan_list = self._creat_client_ipmacvlan(self.nsgs, self.enis, self.ip_ranges_per_vpc)
        self.client_ip_range_settings = client_ipmacvlan_list[0]
        self.client_mac_range_settings = client_ipmacvlan_list[1]
        self.client_vlan_range_settings = client_ipmacvlan_list[2]

        server_ipmacvlan_list = self._create_server_ipmacvlan(self.nsgs, self.enis, self.ip_ranges_per_vpc)
        self.server_ip_range_settings = server_ipmacvlan_list[0]
        self.server_mac_range_settings = server_ipmacvlan_list[1]
        self.server_vlan_range_settings = server_ipmacvlan_list[2]

        # Turn off unused IPs
        self._disable_unused_ips()
        # Turn off TCP settings
        self._adjust_tcp_settings()
        # adjust IxL CPS stat
        self._adjust_cps_stat()
        # create custom traffic maps
        if self.split_networks is True and self.test_config_type == 'cps':
            self._create_custom_traffic_maps()
        # finish config
        self._complete_ixl_config()
        # adjust timeline
        self._adjust_timeline_settings()
        # save rxf
        self._save_rxf()

    def _build_node_ips(self, count, vpc, nodetype="client"):

        if nodetype in "client":
            ip = ipaddress.ip_address(int(IP_R_START) + (IP_STEP3 * count * 4) + (IP_STEP4 * (vpc - 1)))

        if nodetype in "server":
            ip = ipaddress.ip_address(int(IP_L_START) + (IP_STEP4 * (vpc - 1)))

        return ip

    def _build_node_macs(self, count, vpc, nodetype="client"):

        if nodetype in "client":
            m = macaddress.MAC(int(MAC_R_START) + int(macaddress.MAC(ENI_MAC_STEP)) *
                               (vpc - 1) + (int(macaddress.MAC(ACL_TABLE_MAC_STEP)) * count))

        if nodetype in "server":
            m = macaddress.MAC(int(MAC_L_START) + int(macaddress.MAC(ENI_MAC_STEP)) * (vpc - 1))

        return m

    def _complete_ixl_config(self):
        IxLoadUtils.log("Clearing chassis list session {}...".format(self.session_no))
        IxLoadUtils.clearChassisList(self.connection, self.session_url)
        IxLoadUtils.log("Chassis list cleared session {}.".format(self.session_no))

        IxLoadUtils.log("Adding chassis %s session %s..." % (self.test_settings.chassisList, self.session_no))
        IxLoadUtils.addChassisList(self.connection, self.session_url, self.test_settings.chassisList)
        IxLoadUtils.log("Chassis added session {}.".format(self.session_no))

        IxLoadUtils.log("Assigning new ports session {}...".format(self.session_no))
        IxLoadUtils.assignPorts(self.connection, self.session_url, self.test_settings.portListPerCommunity)
        IxLoadUtils.log("Ports assigned session {}.".format(self.session_no))

        if self.test_config_type == 'cps':
            kActivityOptionsToChange = {
                # format: { activityName : { option : value } }
                "HTTPClient1": {
                    "userIpMapping": "1:ALL",
                    "userObjectiveType": self.url_patch_dict['userObjectiveType_cps'],
                    "userObjectiveValue": self.user_init_obj,
                }
            }
        elif self.test_config_type == 'tcp_bg':
            kActivityOptionsToChange = {
                # format: { activityName : { option : value } }
                'HTTPClient1': {
                    'userIpMapping': "1:1",
                    'enableConstraint': False,
                    'userObjectiveType': self.url_patch_dict['userObjectiveType_tcp_bg'],
                    'userObjectiveValue': self.user_init_obj_tcp_bg,
                }
            }

        IxLoadUtils.log("Updating the objective value settings session {}...".format(self.session_no))
        IxLoadUtils.changeActivityOptions(self.connection, self.session_url, kActivityOptionsToChange)
        IxLoadUtils.changeActivityOptions(self.connection, self.session_url, kActivityOptionsToChange)
        IxLoadUtils.log("Objective value updated for session {}.".format(self.session_no))

    def _createconfig_ixn(self, settings_dict, no_of_cards):

        tb = settings_dict['ixn']
        tb_ixn = tb['stateless'][0]

        session_assistant = SessionAssistant(
            IpAddress=tb_ixn['server'][0]['addr'],
            RestPort=tb_ixn['server'][0]['rest'],
            UserName=tb["CR"][tb_ixn['server'][0]['addr']]['user'],
            Password=tb["CR"][tb_ixn['server'][0]['addr']]['password'],
            SessionName="HeroTest",
            ClearConfig=True
        )

        ixnetwork = session_assistant.Ixnetwork
        ixnetwork.Traffic.Statistics.Latency.Mode = "cutThrough"

        #ixnetwork = None
        obj_map = {"enis":{},"clients":{}}
        obj_map["enis"]["bgp"] = (
            ixnetwork.Topology.add(Vports=ixnetwork.Vport.add().add().add().add(),Name="Servers")
            .DeviceGroup.add(Name="ENIs-Servers", Multiplier=1)
            .Ethernet.add(Name='ENIs_Ethernet',UseVlans=True)
            .Ipv4.add(Name="ENIs_IPv4")
            .BgpIpv4Peer.add(Name="ENIs_BGP")
        )
        obj_map["enis"]["bgp"].Active.Single(False)
        obj_map["enis"]["ip"]		 		= obj_map["enis"]["bgp"].parent
        obj_map["enis"]["ethernet"]			= obj_map["enis"]["ip"].parent
        obj_map["enis"]["devicegroup"]		= obj_map["enis"]["ethernet"].parent
        obj_map["enis"]["local"]			= obj_map["enis"]["devicegroup"].NetworkGroup.add(Name="Local", Multiplier=1).Ipv4PrefixPools.add()
        obj_map["enis"]["ng"]				= obj_map["enis"]["local"].parent

        #enis ethernet
        vlan = obj_map["enis"]["ethernet"].Vlan.find()
        vlan.VlanId.Increment(start_value=ENI_START+1,step_value=0)
        vlan.VlanId.Steps[0].Enabled = True
        vlan.VlanId.Steps[0].Step = 2
        obj_map["enis"]["ethernet"].Mac.Increment(start_value = str(macaddress.MAC(int(MAC_L_START) + int(macaddress.MAC(ENI_MAC_STEP)))).replace('-', ':'), step_value='00:00:00:30:00:00')
        obj_map["enis"]["ethernet"].Mac.Steps[0].Enabled = False
        #enis ips
        obj_map["enis"]["ip"].Address.Increment  (start_value=str(ipaddress.ip_address(int(IP_L_START)+IP_STEP4)), step_value="0.1.0.0")
        obj_map["enis"]["ip"].GatewayIp.Increment(start_value=str(ipaddress.ip_address(int(IP_R_START)+IP_STEP4)), step_value="0.1.0.0")
        obj_map["enis"]["ip"].Address.Steps[0].Enabled = True
        obj_map["enis"]["ip"].Address.Steps[0].Step = "2.0.0.0"
        obj_map["enis"]["ip"].GatewayIp.Steps[0].Enabled = True
        obj_map["enis"]["ip"].GatewayIp.Steps[0].Step = "2.0.0.0"
        obj_map["enis"]["ip"].Prefix.Single(32)
        #enis(Local) ips
        obj_map["enis"]["local"].NetworkAddress.Increment(start_value=str(ipaddress.ip_address(int(IP_L_START)+IP_STEP4)), step_value="0.1.0.0")
        obj_map["enis"]["local"].PrefixLength.Single(32)
        obj_map["enis"]["local"].NetworkAddress.Steps[1].Enabled=True
        obj_map["enis"]["local"].NetworkAddress.Steps[1].Step = "2.0.0.0"

        obj_map["clients"]["bgp"] = (
            ixnetwork.Topology.add(Vports=ixnetwork.Vport.add().add().add().add(), Name="TClients")
            .DeviceGroup.add(Name="Clients", Multiplier=1)
            .Ethernet.add(Name='Clients_Ethernet',UseVlans=True)
            .Ipv4.add(Name="Clients_IPv4")
            .BgpIpv4Peer.add(Name="Clients_BGP")
        )

        obj_map["clients"]["bgp"].Active.Single(False)
        obj_map["clients"]["ip"]		 	= obj_map["clients"]["bgp"].parent
        obj_map["clients"]["ethernet"]		= obj_map["clients"]["ip"].parent
        obj_map["clients"]["devicegroup"]	= obj_map["clients"]["ethernet"].parent
        obj_map["clients"]["remote"]		= obj_map["clients"]["devicegroup"].NetworkGroup.add(Name="Remote",Multiplier=6).Ipv4PrefixPools.add()
        obj_map["clients"]["ng"]			= obj_map["clients"]["remote"].parent

        #client ethernet
        vlan = obj_map["clients"]["ethernet"].Vlan.find()
        vlan.VlanId.Increment(start_value=ENI_L2R_STEP+ENI_START+1,step_value=0)
        vlan.VlanId.Steps[0].Enabled = True
        vlan.VlanId.Steps[0].Step = 2
        obj_map["clients"]["ethernet"].Mac.Custom(
            start_value=str(macaddress.MAC(int(MAC_R_START) + int(macaddress.MAC(ENI_MAC_STEP)))).replace('-', ':'),
            step_value = "00:00:00:04:00:00",
            increments = [("00:00:00:04:00:00", 6,[("00:00:00:00:00:02", 21333,[])])]
        )
        obj_map["clients"]["ethernet"].Mac.Steps[0].Enabled = True
        obj_map["clients"]["ethernet"].Mac.Steps[0].Step = '00:00:00:30:00:00'
        #client ips
        obj_map["clients"]["ip"].Address.Increment  (start_value=str(ipaddress.ip_address(int(IP_R_START)+IP_STEP4)), step_value="0.0.0.1")
        obj_map["clients"]["ip"].GatewayIp.Increment(start_value=str(ipaddress.ip_address(int(IP_L_START)+IP_STEP4)), step_value="0.0.0.1")
        obj_map["clients"]["ip"].Address.Steps[0].Enabled = True
        obj_map["clients"]["ip"].Address.Steps[0].Step = "2.0.0.0"
        obj_map["clients"]["ip"].GatewayIp.Steps[0].Enabled = True
        obj_map["clients"]["ip"].GatewayIp.Steps[0].Step = "2.0.0.0"
        obj_map["clients"]["ip"].Prefix.Single(32)
        #client(Remote) ips
        obj_map["clients"]["remote"].NetworkAddress.Increment(start_value=str(ipaddress.ip_address(int(IP_R_START)+IP_STEP4)), step_value="0.4.0.0")
        obj_map["clients"]["remote"].PrefixAddrStep.Single(2)
        obj_map["clients"]["remote"].NumberOfAddressesAsy.Single(128000)
        obj_map["clients"]["remote"].PrefixLength.Single(32)
        obj_map["clients"]["remote"].NetworkAddress.Steps[1].Enabled=True
        obj_map["clients"]["remote"].NetworkAddress.Steps[1].Step = "2.0.0.0"

        ###########Get it from Variable
        if no_of_cards == 8:
            rate, arg5 = 30, 4
        else:
            rate, arg5 = 12, 2

        trafficItem = ixnetwork.Traffic.TrafficItem.add(Name="BackgroundTraffic", TrafficType='ipv4', BiDirectional=True)  # BiDirectional=True
        print ("Creating Endpoint S2C")
        endpoint_s2c = trafficItem.EndpointSet.add(Name="S2C",Sources		=[obj_map["enis"]["ng"].href], 	ScalableDestinations	=[{"arg1": obj_map["clients"]["remote"].href,"arg2": 1,"arg3": 4,"arg4": 1,"arg5": arg5  }])
        ce_s2c = trafficItem.ConfigElement.find()[-1]
        print ("Creating Endpoint C2S")
        endpoint_c2s = trafficItem.EndpointSet.add(Name="C2S",Destinations	=[obj_map["enis"]["ng"].href],	ScalableSources			=[{"arg1": obj_map["clients"]["remote"].href,"arg2": 1,"arg3": 4,"arg4": 1,"arg5": arg5  }])
        ce_c2s = trafficItem.ConfigElement.find()[-1]
        udp_template = ixnetwork.Traffic.ProtocolTemplate.find(StackTypeId='^udp$')

        for indx,ce in enumerate([ce_s2c,ce_c2s]):
            ce.FrameRate.update(Type='PercentLineRate', Rate=rate)
            ce.TransmissionControl.Type = 'continuous'
            ce.FrameRateDistribution.PortDistribution 	= 'applyRateToAll'
            ce.FrameRateDistribution.StreamDistribution = 'splitRateEvenly'

            ce.FrameSize.FixedSize = 1454
            ipv4_template 	= ce.Stack.find(TemplateName="ipv4-template.xml")[-1]
            inner_udp 		= ce.Stack.read(ipv4_template.AppendProtocol(udp_template))
            if indx==0:
                inn_sp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
                inn_dp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')
            else:
                inn_dp = inner_udp.Field.find(DisplayName='^UDP-Source-Port')
                inn_sp = inner_udp.Field.find(DisplayName='^UDP-Dest-Port')

            inn_sp.Auto = inn_dp.Auto = False
            inn_sp.ValueType, inn_dp.ValueType 	= "increment", "repeatableRandomRange"
            inn_sp.StartValue, inn_sp.StepValue, inn_sp.CountValue = 10000, 1, 10000

            inn_dp.MaxValue, inn_dp.MinValue = 20003, 20000
            inn_dp.StepValue = inn_dp.Seed	= inn_dp.CountValue = 1

        trafficItem.Tracking.find()[0].TrackBy = ['trackingenabled0', 'sourceDestEndpointPair0']
        vports = ixnetwork.Vport.find()
        pports = [port['location'] for port in tb_ixn['tgen'][0]['interfaces']]
        ixnetwork.AssignPorts(pports,vports,True)
        ixnetwork.StartAllProtocols(Arg1='sync')
        time.sleep(15)

        udp_ti = ixnetwork.Traffic.TrafficItem.find()
        udp_ti.Generate()
        ixnetwork.Traffic.Apply()

        return ixnetwork

    def _create_custom_traffic_maps(self):

        IxLoadUtils.log("Creating custom traffic maps session {}".format(self.session_no))
        self._create_traffic_map(self.connection, self.url_patch_dict, self.nsgs, self.enis,
                                 self.ip_ranges_per_vpc)
        IxLoadUtils.log("Traffic Maps completed session {}".format(self.session_no))

    def _create_ip_ranges_info(self, connection, session_url, nsgs, enis, ip_ranges_per_vpc):

        ip_range_list = []
        IxLoadUtils.log("Adding IPv4 ranges session {}...".format(self.session_no))
        # Create Client and Server IP Ranges
        if self.split_networks is True:
            self.ip_client_range_adjust = int(enis/2 * ip_ranges_per_vpc)
            self.ip_server_range_adjust = int(enis/2)

            if self.test_config_type == 'cps':
                self.ip_client_range_adjust = self.ip_client_range_adjust + ip_ranges_per_vpc
                self.ip_server_range_adjust = self.ip_server_range_adjust + 1
        else:
            self.ip_client_range_adjust = 0
            self.ip_server_range_adjust = 0

        if self.split_networks is True and self.test_config_type == 'tcp_bg':
            for _ in range(self.ip_ranges_per_vpc):
                self._create_ip_ranges(connection, session_url, "Traffic1@Network1", "IP-1")
            for _ in range(1):
                self._create_ip_ranges(connection, session_url, "Traffic2@Network2", "IP-2")
        else:
            for _ in range(nsgs - self.ip_client_range_adjust):
                self._create_ip_ranges(connection, session_url, "Traffic1@Network1", "IP-1")
            for _ in range(enis - self.ip_server_range_adjust):
                self._create_ip_ranges(connection, session_url, "Traffic2@Network2", "IP-2")

        # Get Client/Server IP range info
        client_ip_range_names, client_range_list_info = self._get_ip_range_names(connection,
                                session_url, "Traffic1@Network1", "IP-1", self.url_patch_dict)
        server_ip_range_names, server_range_list_info = self._get_ip_range_names(connection,
                                session_url, "Traffic2@Network2", "IP-2", self.url_patch_dict)

        IxLoadUtils.log("Disabling autoMacGeneration session {} ...".format(self.session_no))
        if self.split_networks is True and self.test_config_type == 'tcp_bg':
            for i in range(self.ip_ranges_per_vpc):
                url_ip = self._get_url_ip("client", client_ip_range_names, i)
                response = requests.patch(url_ip, json=self.url_patch_dict['auto_mac_setting'])
                #response = self.make_request('PATCH', url_ip, url_patch_dict['auto_mac_setting'])
            for i in range(1):
                url_ip = self._get_url_ip("server", server_ip_range_names, i)
                response = requests.patch(url_ip, json=self.url_patch_dict['auto_mac_setting'])
                #response = self.make_request('PATCH', url_ip, url_patch_dict['auto_mac_setting'])
        else:
            for i in range(enis - self.ip_server_range_adjust):
                url_ip = self._get_url_ip("server", server_ip_range_names, i)
                response = requests.patch(url_ip, json=self.url_patch_dict['auto_mac_setting'])
                #response = self.make_request('PATCH', url_ip, url_patch_dict['auto_mac_setting'])

            for i in range(nsgs - self.ip_client_range_adjust):
                url_ip = self._get_url_ip("client", client_ip_range_names, i)
                response = requests.patch(url_ip, json=self.url_patch_dict['auto_mac_setting'])
                #response = self.make_request('PATCH', url_ip, url_patch_dict['auto_mac_setting'])

        ip_range_list.append(client_ip_range_names)
        ip_range_list.append(client_range_list_info)
        ip_range_list.append(server_ip_range_names)
        ip_range_list.append(server_range_list_info)

        return ip_range_list

    def _create_ixl_foundations(self, connection, session_url):

        IxLoadUtils.log("Creating communities session {} {}...".format(self.session_no, self.test_config_type))
        IxLoadUtils.addCommunities(connection, session_url, self.kCommunities)
        IxLoadUtils.log("Communities created for session {}.".format(self.session_no))

        IxLoadUtils.log("Creating activities session {}...".format(self.session_no))
        IxLoadUtils.addActivities(connection, session_url, self.kActivities)
        IxLoadUtils.log("Activities created session {}...".format(self.session_no))

        IxLoadUtils.log("Enabling Forceful Ownership of Ports session {}...".format(self.session_no))
        IxLoadUtils.enableForcefullyTakeOwnershipAndResetPorts(connection, session_url)
        IxLoadUtils.log("Forceful Ownership Complete session {}...".format(self.session_no))

        response = self._patch_test_setting(self.url_patch_dict, 'allow_routes')

        if self.test_config_type == 'cps':
            IxLoadUtils.log("Clearing commands %s session %s..." % (list(self.kNewCommands_cps), self.session_no))
            IxLoadUtils.clearAgentsCommandList(connection, session_url, list(self.kNewCommands_cps))
            IxLoadUtils.log("Command lists cleared session {}.".format(self.session_no))

            IxLoadUtils.log("Adding new commands %s session %s..." % (list(self.kNewCommands_cps), self.session_no))
            IxLoadUtils.addCommands(connection, session_url, self.kNewCommands_cps)
            IxLoadUtils.log("Commands added session {}.".format(self.session_no))
        elif self.test_config_type == 'tcp_bg':
            IxLoadUtils.log("Clearing commands %s session %s..." % (list(self.kNewCommands_tcp_bg), self.session_no))
            IxLoadUtils.clearAgentsCommandList(self.connection, self.session_url, list(self.kNewCommands_tcp_bg))
            IxLoadUtils.log("Command lists cleared session {}.".format(self.session_no))

            IxLoadUtils.log("Adding new commands %s session %s..." % (list(self.kNewCommands_tcp_bg), self.session_no))
            IxLoadUtils.addCommands(self.connection, self.session_url, self.kNewCommands_tcp_bg)
            IxLoadUtils.log("Commands added session {}.".format(self.session_no))


    def _creat_client_ipmacvlan(self, nsgs, enis, ip_ranges_per_vpc):

        client_ipmacvlan_list = []
        IxLoadUtils.log("Creating Client IPs, MACs, and VLANIDs session {}".format(self.session_no))
        client_ip_range_settings = []
        client_mac_range_settings = []
        client_vlan_range_settings = []
        eni_index = 1
        ip_count = 0
        nodetype = "client"
        # Build Client IPs and MACs
        if self.split_networks is True and self.test_config_type == 'tcp_bg':
            eni_index = enis - 1
            for i in range(ip_ranges_per_vpc):
                # --- ixNet objects need to be added in the list before they are configured.
                client_ip_range_settings.append(self._set_ip_range_options(ip_count, eni_index, nodetype))
                client_mac_range_settings.append(self._set_mac_range_options(ip_count, eni_index, nodetype))
                client_vlan_range_settings.append(self._set_vlan_range_options(self.url_patch_dict, eni_index-1, nodetype))
                ip_count += 1
        else:
            for i in range(nsgs + ip_ranges_per_vpc + (enis-1)):
                if ip_count < ip_ranges_per_vpc and eni_index <= enis:
                    # --- ixNet objects need to be added in the list before they are configured.
                    client_ip_range_settings.append(self._set_ip_range_options(ip_count, eni_index, nodetype))
                    client_mac_range_settings.append(self._set_mac_range_options(ip_count, eni_index, nodetype))
                    client_vlan_range_settings.append(self._set_vlan_range_options(self.url_patch_dict, eni_index-1, nodetype))
                    ip_count += 1
                else:
                    if self.split_networks and eni_index % 2 == 1:
                        eni_index += 2
                        if eni_index == (enis-1) and self.test_config_type == 'cps':
                            break
                    else:
                        eni_index += 1
                    ip_count = 0

        if self.split_networks is True:
            nsgs_split = int(nsgs/2)
        else:
            nsgs_split = nsgs

        IxLoadUtils.log("Setting Client Ranges: IPs, MACs, VLANs sesion {}".format(self.session_no))
        for i in range(nsgs_split):
            if self.split_networks is True and i >= len(client_ip_range_settings):
                break
            range_url = self.url_patch_dict['client_range_setting']['url']
            r_index = self.client_ip_range_names[i].split("-")[1][1:]

            url_ip = self.url_patch_dict['base_url'] + range_url % (r_index)
            url_mac = self.url_patch_dict['base_url'] + range_url % (r_index) + "/macRange"
            url_vlan = self.url_patch_dict['base_url'] + range_url % (r_index) + "/vlanRange"

            response = requests.patch(url_ip, json=client_ip_range_settings[i])
            response = requests.patch(url_mac, json=client_mac_range_settings[i])
            response = requests.patch(url_vlan, json=self.vlan_enabled)
            response = requests.patch(url_vlan, json=client_vlan_range_settings[i])

        client_ipmacvlan_list.append(client_ip_range_settings)
        client_ipmacvlan_list.append(client_mac_range_settings)
        client_ipmacvlan_list.append(client_vlan_range_settings)

        return client_ipmacvlan_list

    def _create_server_ipmacvlan(self, nsgs, enis, ip_ranges_per_vpc):

        server_ipmacvlan_list = []
        IxLoadUtils.log("Creating Server IPs, MACs, and VLANIDs session {}".format(self.session_no))
        nodetype = "server"
        server_ip_range_settings = []
        server_mac_range_settings = []
        server_vlan_range_settings = []

        if self.split_networks is True and self.test_config_type == 'tcp_bg':
            eni = enis - 1
            server_ip_range_settings.append(self._set_ip_range_options(0, eni, nodetype))
            server_mac_range_settings.append(self._set_mac_range_options(0, eni, nodetype))
            server_vlan_range_settings.append(self._set_vlan_range_options(self.url_patch_dict,
                                                                            eni-1, nodetype))
        else:
            for eni in range(enis):
                if self.split_networks is True and eni % 2 == 1 and eni < enis-1:
                    server_ip_range_settings.append(self._set_ip_range_options(0, eni, nodetype))
                    server_mac_range_settings.append(self._set_mac_range_options(0, eni, nodetype))
                    server_vlan_range_settings.append(self._set_vlan_range_options(self.url_patch_dict,
                                                                                   eni-1, nodetype))
                elif self.split_networks is False:
                    server_ip_range_settings.append(self._set_ip_range_options(0, eni+1, nodetype))
                    server_mac_range_settings.append(self._set_mac_range_options(0, eni+1, nodetype))
                    server_vlan_range_settings.append(self._set_vlan_range_options(self.url_patch_dict,
                                                                                   eni, nodetype))

        IxLoadUtils.log("Setting Server Ranges: IPs, MACs, VLANs session {}".format(self.session_no))
        for i in range(enis):
            if i < len(server_ip_range_settings):
                range_url = self.url_patch_dict['server_range_setting']['url']
                r_index = self.server_ip_range_names[i].split("-")[1][1:]

                url_ip = self.url_patch_dict['base_url'] + range_url % (r_index)
                url_mac = self.url_patch_dict['base_url'] + range_url % (r_index) + "/macRange"
                url_vlan = self.url_patch_dict['base_url'] + range_url % (r_index) + "/vlanRange"

                response = requests.patch(url_ip, json=server_ip_range_settings[i])
                response = requests.patch(url_mac, json=server_mac_range_settings[i])
                response = requests.patch(url_vlan, json=self.vlan_enabled)
                response = requests.patch(url_vlan, json=server_vlan_range_settings[i])

        server_ipmacvlan_list.append(server_ip_range_settings)
        server_ipmacvlan_list.append(server_mac_range_settings)
        server_ipmacvlan_list.append(server_vlan_range_settings)

        return server_ipmacvlan_list

    def _disable_unused_ips(self):

        IxLoadUtils.log("Disabling Unused IP ranges session {}...".format(self.session_no))
        kIpOptionsToChange = {
            # format : { IP Range name : { optionName : optionValue } }
            self.client_ip_range_names[-1]: {
                'count': 1,
                'enabled': False,
            },
            self.server_ip_range_names[-1]: {
                'count': 1,
                'enabled': False,
            }
        }
        IxLoadUtils.changeIpRangesParams(self.connection, self.session_url, kIpOptionsToChange)

    def _patch_test_setting(self, url_patch_dict, setting):

        url = url_patch_dict['base_url'] + url_patch_dict[setting]['url']
        return requests.patch(url, json=url_patch_dict[setting]['json'])

    def _get_timeline_link(self, timelines, timeline_key):

        link = ""
        link_test = ""

        for elem in timelines:
            if elem['name'] in timeline_key:
                link_init = elem['links'][0]['href']
                link_init_list = link_init.split("/")
                link_init_list.pop(len(link_init_list) - 1)
                link_test = '/'.join(link_init_list)

        shaved = link_test.split("/")
        for i in range(5):
            shaved.pop(0)
        shaved.insert(0, "")
        link = "/".join(shaved)

        return link

    def _set_timeline_settings(self, test_settings, rampDownTime, sustainTime):

        timeline_url = 'http://' + test_settings.gatewayServer + ":{}".format(
            test_settings.gatewayPort) + '/api/v1/' + self.session_url + '/ixload/test/activeTest/timelineList'
        response = requests.get(timeline_url, headers=self.headers)
        timelines = response.json()

        timeline1_url = 'http://' + test_settings.gatewayServer + ":{}".format(
            test_settings.gatewayPort) + '/api/v1/' + self.session_url + \
                        self._get_timeline_link(timelines, "Timeline1")
        timeline1_settings = {"rampDownTime": rampDownTime, "sustainTime": sustainTime}
        requests.patch(timeline1_url, json=timeline1_settings)

        timeline2_url = 'http://' + test_settings.gatewayServer + ":{}".format(
            test_settings.gatewayPort) + '/api/v1/' + self.session_url + \
                        self._get_timeline_link(timelines, "Timeline2")
        timeline2_settings = {"rampDownTime": rampDownTime, "sustainTime": sustainTime}
        requests.patch(timeline2_url, json=timeline2_settings)

        timeline_matchLongest_url = 'http://' + test_settings.gatewayServer + ":{}".format(
            test_settings.gatewayPort) + '/api/v1/' + self.session_url + \
                                    self._get_timeline_link(timelines, "<Match Longest>")
        matchLongest_settings = {"sustainTime": sustainTime}
        requests.patch(timeline_matchLongest_url, json=matchLongest_settings)

        return

    def _getTestCurrentState(self, connection, sessionUrl):

        activeTestUrl = "%s/ixload/test/activeTest" % (sessionUrl)
        testObj = connection.httpGet(activeTestUrl)

        return testObj.currentState

    def _print_final_table(self, test_run_results, test_config_type):
        stat_table = []

        if test_config_type == 'cps':
            stat_columns = ["It", "Obtained CPS", "HTTP Requests Failed", "TCP Retries",
                            "TCP Resets TX", "TCP Resets RX"]
        elif test_config_type == 'tcp_bg':
            stat_columns = ["It", "Concurrent Connections", "HTTP Requests Failed", "TCP Retries",
                            "TCP Resets TX", "TCP Resets RX"]

        for iter in test_run_results:
            stat_table.append(iter)
        print("\n%s" % tabulate(stat_table, headers=stat_columns, tablefmt='psql', floatfmt=".2f"))

    def _poll_stats(self, connection, sessionUrl, watchedStatsDict, pollingInterval=4):

        statSourceList = list(watchedStatsDict)

        # retrieve stats for a given stat dict
        # all the stats will be saved in the dictionary below

        # statsDict format:
        # {
        #   statSourceName: {
        #                       timestamp:  {
        #                                       statCaption : value
        #                                   }
        #                   }
        # }
        stats_dict = {}

        # remember the timstamps that were already collected - will be ignored in future
        collectedTimestamps = {}  # format { statSource : [2000, 4000, ...] }
        testIsRunning = True

        # check stat sources
        for statSource in statSourceList[:]:
            statSourceUrl = "%s/ixload/stats/%s/values" % (sessionUrl, statSource)
            statSourceReply = connection.httpRequest("GET", statSourceUrl)
            if statSourceReply.status_code != 200:
                statSourceList.remove(statSource)

        # check the test state, and poll stats while the test is still running
        while testIsRunning:

            # the polling interval is configurable. by default, it's set to 4 seconds
            time.sleep(pollingInterval)

            for statSource in statSourceList:
                valuesUrl = "%s/ixload/stats/%s/values" % (sessionUrl, statSource)
                valuesObj = connection.httpGet(valuesUrl)
                valuesDict = valuesObj.getOptions()

                # get just the new timestamps - that were not previously retrieved in another stats polling iteration
                newTimestamps = [int(timestamp) for timestamp in list(valuesDict) if
                                 timestamp not in collectedTimestamps.get(statSource, [])]
                newTimestamps.sort()

                for timestamp in newTimestamps:
                    timeStampStr = str(timestamp)
                    collectedTimestamps.setdefault(statSource, []).append(timeStampStr)
                    timestampDict = stats_dict.setdefault(statSource, {}).setdefault(timestamp, {})

                    # save the values for the current timestamp, and later print them
                    for caption, value in iteritems(valuesDict[timeStampStr].getOptions()):
                        if caption in watchedStatsDict[statSource]:
                            timestampDict[caption] = value
                            stat_table_row = []
                            for table_row in timestampDict.keys():
                                stat_table_row.append(table_row)
                            table = []
                            columns = ['Stat Source', 'Time Stamp', 'Stat Name', 'Value']
                            for i, stat in enumerate(stat_table_row):
                                table.append([statSource, timeStampStr, stat, timestampDict[stat]])
                            # print("\n%s" % tabulate(table, headers=columns, tablefmt='psql'))
            testIsRunning = self._getTestCurrentState(connection, sessionUrl) == "Running"

        print("Stopped receiving stats.")
        return stats_dict

    def _get_stats_global(self, stats_dict):
        stats_global = []

        for key in stats_dict['HTTPClient'].keys():
            if key in stats_dict['HTTPClient'] and key in stats_dict['HTTPServer']:
                stats_global.append([key, stats_dict['HTTPClient'][key]['HTTP Simulated Users'],
                                     stats_dict['HTTPClient'][key]['HTTP Concurrent Connections'],
                                     stats_dict['HTTPClient'][key]['TCP CPS'],
                                     stats_dict['HTTPClient'][key]['HTTP Connect Time (us)'],
                                     stats_dict['HTTPServer'][key]['HTTP Requests Failed'],
                                     stats_dict['HTTPServer'][key]['TCP Retries'],
                                     stats_dict['HTTPServer'][key]['TCP Resets Sent'],
                                     stats_dict['HTTPServer'][key]['TCP Resets Received']])

        return stats_global

    def _check_for_error_stats(self, test_stats, error_type):

        error_dict = {
            error_type: {
                "first_time": 0,
                "last_time": 0,
                "num_of_seq_timestamps": 0
            }
        }

        timestamps_l = [i[0] for i in test_stats]
        errors_l = [i[1] for i in test_stats]
        seen = set()
        dupes = {}

        first_time = 0
        for i, x in enumerate(errors_l):
            if x in seen:
                dupes.setdefault(x, []).append(i)
            else:
                seen.add(x)

        # insert timestamp index location at beginning of list
        for key in dupes.keys():
            dupes[key].insert(0, dupes[key][0] - 1)

        # make list of lens of each duplicates, then remove and remove rest of error entries from dupes dict
        errors_l = [len(dupes[x]) for x in dupes.keys()]
        max_index = errors_l.index(max(errors_l))
        errors_l.pop(max_index)

        # keep only the highest number of stable
        for i, key in enumerate(list(dupes)):
            if i != max_index:
                dupes.pop(key, None)

        for key in dupes.keys():
            error_dict[error_type]["first_time"] = dupes[key][0]
            error_dict[error_type]["last_time"] = dupes[key][-1]

            if list(dupes.keys())[0] != 0:
                error_dict[error_type]["num_of_seq_timestamps"] = len(dupes[key])
            else:
                error_dict[error_type]["num_of_seq_timestamps"] = 0

        return error_dict

    def _get_max_cc(self, test_stats, cc_stats):

        cc_list = []
        for cc in cc_stats:
            cc_list.append(cc[1])

        stats = deepcopy(cc_list)
        for i, elem in enumerate(stats):
            if elem == '""':
                stats[i] = 0

        stats.sort()
        max_cc = stats[-1]
        cc_max_w_ts = cc_stats[cc_list.index(max_cc)]

        return cc_max_w_ts

    def _get_max_cps(self, test_stats, cps_stats):

        cps_list = []
        for cps in cps_stats:
            cps_list.append(cps[1])

        stats = deepcopy(cps_list)
        for i, elem in enumerate(stats):
            if elem == '""':
                stats[i] = 0

        stats.sort()
        max_cps = stats[-1]
        cps_max_w_ts = cps_stats[cps_list.index(max_cps)]

        return cps_max_w_ts

    def _get_effective_cps(self, cps_stats, http_requests_dict, tcp_retries_dict, tcp_resets_tx_dict, tcp_resets_rx_dict):

        error_list = [http_requests_dict, tcp_retries_dict, tcp_resets_tx_dict, tcp_resets_rx_dict]
        num_of_timestamps = len(cps_stats)

        seq_l = [list(x.values())[0]["num_of_seq_timestamps"] for x in error_list]
        error_list[seq_l.index(max(seq_l))]
        key = list(error_list[seq_l.index(max(seq_l))].keys())[0]
        first_time = error_list[seq_l.index(max(seq_l))][key]["first_time"]
        last_time = error_list[seq_l.index(max(seq_l))][key]["last_time"]

        effective_cps_ts = {
            "first_time": cps_stats[first_time][0],
            "last_time": cps_stats[last_time][0]
        }

        if max(seq_l) != 0:
            avg = 0
            effective_cps_l = []
            for i, cps in enumerate(cps_stats):
                if i >= first_time and i <= last_time:
                    effective_cps_l.append(cps)
                    avg += cps[1]
            effective_cps = avg / error_list[seq_l.index(max(seq_l))][key]["num_of_seq_timestamps"]
        else:
            effective_cps = 0
            effective_cps_ts = {"first_time": 0, "last_time": cps_stats[last_time][0]}

        return effective_cps, effective_cps_ts

    def _get_latency_ranges(self, test_stats):

        latency_stats = {
            "latency_min": 0,
            "latency_max": 0,
            "latency_avg": 0
        }

        only_lat_stats = []
        for lat_stat in test_stats:
            if lat_stat[4] == '""':
                lat_stat[4] = 0
            only_lat_stats.append(lat_stat[4])

        latency_stats["latency_min"] = min(only_lat_stats)
        latency_stats["latency_max"] = max(only_lat_stats)

        lat_addr = 0
        for elem in only_lat_stats:
            lat_addr += elem

        latency_stats["latency_avg"] = lat_addr / len(only_lat_stats)

        return latency_stats

    def _get_testrun_results(self, stats_dict, url_patch_dict, hero_test_config_type):

        stats_global = self._get_stats_global(stats_dict)

        failures_dict = {"http_requests_failed": 0, "tcp_retries": 0, "tcp_resets_tx": 0,
                         "tcp_resets_rx": 0, "total": 0}

        # get and compare stats
        http_requests_failed_l = [[x[0], x[5]] for x in stats_global]
        http_requests_failed = max([x[1] for x in http_requests_failed_l])
        failures_dict["http_requests_failed"] = http_requests_failed

        tcp_retries_l = [[x[0], x[6]] for x in stats_global]
        tcp_retries = max([x[1] for x in tcp_retries_l])
        failures_dict["tcp_retries"] = tcp_retries

        tcp_resets_tx_l = [[x[0], x[7]] for x in stats_global]
        tcp_resets_tx = max([x[1] for x in tcp_resets_tx_l])
        failures_dict["tcp_resets_tx"] = tcp_resets_tx

        tcp_resets_rx_l = [[x[0], x[8]] for x in stats_global]
        tcp_resets_rx = max([x[1] for x in tcp_resets_rx_l])
        failures_dict["tcp_resets_rx"] = tcp_resets_rx

        failures = http_requests_failed + tcp_retries + tcp_resets_tx + tcp_resets_rx
        failures_dict["total"] = failures

        steady_time_start = int(url_patch_dict['timeline_settings']['advancedIteration']['d0']['duration']) * 1000
        if hero_test_config_type == 'cps':
            cps_stats = [[x[0], x[3]] for x in stats_global if x[0] >= steady_time_start]
            obj_max_w_ts = self._get_max_cps(stats_global, cps_stats)
            obj_max = obj_max_w_ts[1]
        elif hero_test_config_type == 'tcp_bg':
            cc_stats = [[x[0], x[2]] for x in stats_global if x[0] >= steady_time_start]
            obj_max_w_ts = self._get_max_cc(stats_global, cc_stats)
            obj_max = obj_max_w_ts[1]

        latency_ranges = self._get_latency_ranges(stats_global)

        return failures_dict, obj_max, obj_max_w_ts, latency_ranges

    def _create_ip_ranges(self, connection, session_url, traffic_network, plugin_name):

        IxLoadUtils.HttpUtils.addIpRange(connection, session_url, traffic_network,
                                         plugin_name, {"ipType": "IPv4"})

    def _create_traffic_map(self, connection, url_patch_dict, nsgs, enis, ip_ranges_per_vpc):

        # Make Traffic Map Settings
        portMapPolicy_json = {'portMapPolicy': 'customMesh'}
        destinations_url = url_patch_dict['base_url'] + url_patch_dict['traffic_maps']['destinations_url']
        response = requests.patch(destinations_url, json=portMapPolicy_json)

        # meshType
        submapsIPv4_url = url_patch_dict['base_url'] + url_patch_dict['traffic_maps']['subMapsIPv4_url']
        meshType_json = url_patch_dict['traffic_maps']['meshType_setting']
        response = requests.patch(submapsIPv4_url, json=meshType_json)

        # map source-to-destination
        sourceRanges_url = submapsIPv4_url + "/sourceRanges/%s"
        destId = ENI_START
        if url_patch_dict['traffic_maps']['meshType_setting']['meshType'] == 'ipRangePairs':
            ip_count = 0
            for i in range(nsgs):
                destinationId_json = {'destinationId': destId}
                url = sourceRanges_url % (i)
                response = requests.patch(url, json=destinationId_json)
                ip_count += 1
                if ip_count == ip_ranges_per_vpc:
                    destId += 1
                    ip_count = 0
        else:
            # vlanRangePairs meshType
            # TODO --- vlanRangePairs configured correctly in sequence out of box but not custom
            pass

        # destinationRanges
        destRanges_json = {'enable': False}
        destinationRanges_url = url_patch_dict['base_url'] + "/destinationRanges/%s"
        for i in range(enis):
            url = destinationRanges_url % (i)
            if i == 0:
                response = requests.patch(url, json=destRanges_json)

        return

    def _get_ip_range_names(self, connection, session_url, traffic_network, plugin_names, url_patch_dict):

        ip_range_names = []
        range_string = IxLoadUtils.HttpUtils.getRangeListUrl(connection, session_url, traffic_network, plugin_names,
                                                             "rangeList")
        string_split = range_string.split("/")
        range_url = "/" + "/".join(string_split[2:])
        url = url_patch_dict["base_url"] + range_url

        response = requests.get(url, params=None)
        range_list_info = response.json()

        for elem in range_list_info:
            ip_range_names.append(elem['name'])

        return ip_range_names, range_list_info

    def _get_url_ip(self, nodetype, node_ip_range_names, index):

        if nodetype == "client":
            range_url = self.url_patch_dict['client_range_setting']['url']
        else:
            range_url = self.url_patch_dict['server_range_setting']['url']

        r_index = node_ip_range_names[index].split("-")[1][1:]
        url_ip = self.url_patch_dict['base_url'] + range_url % (r_index)

        return url_ip

    def _print_stat_table(self, obj_max_w_ts, failures_dict, latency_ranges, test_config_type):

        if self.test_config_type == 'cps':
            stat_columns = ["Timestamp (s)", "TCP Max CPS", "Total Failures"]
        elif self.test_config_type == 'tcp_bg':
            stat_columns = ["Timestamp (s)", "Max CC", "Total Failures"]

        stat_table = []
        stat_table.append([int(obj_max_w_ts[0]) / 1000, int(obj_max_w_ts[1]), failures_dict["total"]])

        stat_f_table = []
        stat_f_columns = ["HTTP Requests Failed", "TCP Retries", "TCP Resets TX", "TCP Resets RX"]
        stat_f_table.append([failures_dict["http_requests_failed"], failures_dict["tcp_retries"],
                             failures_dict["tcp_resets_tx"], failures_dict["tcp_resets_rx"]])

        lat_table = []
        lat_table.append(
            [latency_ranges["latency_min"], latency_ranges["latency_max"], latency_ranges["latency_avg"]]
        )
        lat_stat_columns = ["Connect Time min (us)", "Connect Time max (us)", "Connect Time avg (us)"]

        print("\n%s" % tabulate(stat_table, headers=stat_columns, tablefmt='psql'))
        print("\n%s" % tabulate(stat_f_table, headers=stat_f_columns, tablefmt='psql'))
        print("\n%s" % tabulate(lat_table, headers=lat_stat_columns, tablefmt='psql'))

    def run2(self, hero_tcp_bg):

        connection = self.connection
        session_url = self.session_url

        initial_objective = self.url_patch_dict['initial_objective']
        MAX_CPS = self.MAX_CPS
        MIN_CPS = self.MIN_CPS
        threshold = self.url_patch_dict['threshold']
        target_failures = self.url_patch_dict['target_failures']

        start_value = initial_objective
        test_run_results = []
        self.test_value = start_value
        self.test_iteration = 1

        ## tcp_bg
        hero_tcp_bg.test_iteration = 1
        IxLoadUtils.log("Applying config session {}, {}...".format(hero_tcp_bg.session_no, hero_tcp_bg.test_config_type))
        IxLoadUtils.applyConfiguration(hero_tcp_bg.connection, hero_tcp_bg.session_url)

        while ((MAX_CPS - MIN_CPS) > threshold):
            if self.test_config_type == 'cps':
                test_result = ""
                IxLoadUtils.log(
                    "----Test Iteration %d------------------------------------------------------------------"
                    % self.test_iteration)
                old_value = self.test_value
                IxLoadUtils.log("Testing CPS Objective = %d" % self.test_value)
                kActivityOptionsToChange = {
                    # format: { activityName : { option : value } }
                    "HTTPClient1": {
                        "enableConstraint": False,
                        "userObjectiveType": "connectionRate",
                        "userObjectiveValue": int(self.test_value),
                    }
                }

            ## cps
            IxLoadUtils.log("Updating CPS objective value settings...")
            IxLoadUtils.changeActivityOptions(connection, session_url, kActivityOptionsToChange)
            IxLoadUtils.log("CPS objective value updated.")

            IxLoadUtils.log("Applying config session {}, {}...".format(self.session_no, self.test_config_type))
            IxLoadUtils.applyConfiguration(self.connection, self.session_url)

            test_type = ['tcp_bg', 'cps']
            child_threads = []
            for test in test_type:
                if test == 'tcp_bg':
                    t = Thread(target=hero_tcp_bg._run_bg2, args=())
                else:
                    t = Thread(target=self._run_cps_search2, args=())

                t.start()
                child_threads.append(t)
                time.sleep(10)

            for t in child_threads:
                t.join()

            hero_tcp_bg.test_iteration = self.test_iteration

            ## release configs
            IxLoadUtils.releaseConfiguration(self.connection, self.session_url)

        IxLoadUtils.releaseConfiguration(hero_tcp_bg.connection, hero_tcp_bg.session_url)
        IxLoadUtils.log("Test Complete Final Values session {} {}".format(self.session_no, self.test_config_type))
        self._print_final_table(hero_tcp_bg.test_run_results, hero_tcp_bg.test_config_type)
        self._print_final_table(self.test_run_results, self.test_config_type)

    def _run_cps_search2(self):

        old_value = self.test_value
        IxLoadUtils.log("Starting the test...")
        IxLoadUtils.runTest(self.connection, self.session_url)
        IxLoadUtils.log("Test started.")

        IxLoadUtils.log("Test running and extracting stats...")
        stats_dict = self._poll_stats(self.connection, self.session_url, self.stats_test_settings)
        IxLoadUtils.log("Test finished.")

        failures_dict, cps_max, cps_max_w_ts, latency_ranges = self._get_testrun_results(stats_dict,
                                                        self.url_patch_dict, self.test_config_type)

        self._print_stat_table(cps_max_w_ts, failures_dict, latency_ranges, self.test_config_type)

        if cps_max < self.test_value:
            test = False
        else:
            test = True

        if test:
            IxLoadUtils.log('Test Iteration Pass')
            test_result = "Pass"
            self.MIN_CPS = self.test_value
            self.test_value = (self.MAX_CPS + self.MIN_CPS) / 2
        else:
            IxLoadUtils.log('Test Iteration Fail')
            test_result = "Fail"
            self.MAX_CPS = self.test_value
            self.test_value = (self.MAX_CPS + self.MIN_CPS) / 2

            objective_cps = old_value
            self.obtained_cps = cps_max_w_ts[1]
            self.test_run_results.append(
                [self.test_iteration, objective_cps, self.obtained_cps, failures_dict["http_requests_failed"],
                 failures_dict["tcp_retries"], failures_dict["tcp_resets_tx"],
                 failures_dict["tcp_resets_rx"], test_result])
            IxLoadUtils.log("Iteration Ended...")
            IxLoadUtils.log('MIN_CPS = %d' % self.MIN_CPS)
            IxLoadUtils.log('Current MAX_CPS = %d' % self.MAX_CPS)
            IxLoadUtils.log('Previous CPS Objective value = %d' % old_value)
            print(' ')
            self.test_iteration += 1

        cps_max_w_ts[1] = self.MIN_CPS

    def _run_bg2(self):

        test_value = self.url_patch_dict['userObjectiveType_tcp_bg']

        test_result = ""
        IxLoadUtils.log(
            "----Test Iteration %d------------------------------------------------------------------"
            % self.test_iteration)
        old_value = test_value

        IxLoadUtils.log("Starting the test session {} {}...".format(self.session_no, self.test_config_type))
        IxLoadUtils.runTest(self.connection, self.session_url)
        IxLoadUtils.log("Test started session {} {}.".format(self.session_no, self.test_config_type))

        IxLoadUtils.log("Test running and extracting stats session {} {}...".format(self.session_no, self.test_config_type))
        stats_dict = self._poll_stats(self.connection, self.session_url, self.stats_test_settings)
        IxLoadUtils.log("Test finished session {} {}.".format(self.session_no, self.test_config_type))

        failures_dict, cc_max, cc_max_w_ts, latency_ranges = self._get_testrun_results(stats_dict, self.url_patch_dict, self.test_config_type)

        self._print_stat_table(cc_max_w_ts, failures_dict, latency_ranges, self.test_config_type)

        self.test_run_results.append(
            [self.test_iteration, cc_max, failures_dict['http_requests_failed'],
             failures_dict['tcp_retries'], failures_dict['tcp_resets_tx'],
             failures_dict['tcp_resets_rx']]
        )

    def run(self):

        if self.test_config_type == 'cps':
            initial_objective = self.url_patch_dict['initial_objective']
            MAX_CPS = self.url_patch_dict['MAX_CPS']
            MIN_CPS = self.url_patch_dict['MIN_CPS']
            threshold = self.url_patch_dict['threshold']
            target_failures = self.url_patch_dict['target_failures']

            cps_max_w_ts, failures_dict, test_run_results, latency_ranges = self._run_cps_search(self.connection, self.session_url,
                                                                                           MAX_CPS,
                                                                                           MIN_CPS, threshold,
                                                                                           target_failures, self.test_settings,
                                                                                           initial_objective)
        elif self.test_config_type == 'tcp_bg':
            initial_objective = self.url_patch_dict['initial_objective_tcp_bg']
            cps_max_w_ts, failures_dict, test_run_results, latency_ranges = self._run_bg(self.connection, self.session_url,
                                                                                         self.url_patch_dict,
                                                                                         self.test_settings)

        IxLoadUtils.log("Test Complete Final Values session {} {}".format(self.session_no, self.test_config_type))
        self._print_final_table(test_run_results, self.test_config_type)

    def _run_cps_search(self, connection, session_url, MAX_CPS, MIN_CPS,
                        threshold, target_failures, test_settings, start_value=0):

        test_run_results = []
        test_value = start_value
        test_iteration = 1
        while ((MAX_CPS - MIN_CPS) > threshold):
            test_result = ""
            IxLoadUtils.log(
                "----Test Iteration %d------------------------------------------------------------------"
                % test_iteration)
            old_value = test_value
            IxLoadUtils.log("Testing CPS Objective = %d" % test_value)
            kActivityOptionsToChange = {
                # format: { activityName : { option : value } }
                "HTTPClient1": {
                    "enableConstraint": False,
                    "userObjectiveType": "connectionRate",
                    "userObjectiveValue": int(test_value),
                }
            }
            IxLoadUtils.log("Updating CPS objective value settings...")
            IxLoadUtils.changeActivityOptions(connection, session_url, kActivityOptionsToChange)
            IxLoadUtils.log("CPS objective value updated.")

            IxLoadUtils.log("Applying config...")
            IxLoadUtils.applyConfiguration(connection, session_url)

            # IxLoadUtils.log("Saving rxf")
            # IxLoadUtils.saveRxf(connection, session_url, "C:\\automation\\1ip_test.rxf")

            IxLoadUtils.log("Starting the test...")
            IxLoadUtils.runTest(connection, session_url)
            IxLoadUtils.log("Test started.")

            IxLoadUtils.log("Test running and extracting stats...")
            stats_dict = self._poll_stats(connection, session_url, self.stats_test_settings)
            IxLoadUtils.log("Test finished.")

            failures_dict, cps_max, cps_max_w_ts, latency_ranges = self._get_testrun_results(stats_dict,
                                                                            self.url_patch_dict, self.test_config_type)

            self._print_stat_table(cps_max_w_ts, failures_dict, latency_ranges, self.test_config_type)

            if cps_max < test_value:
                test = False
            else:
                test = True

            if test:
                IxLoadUtils.log('Test Iteration Pass')
                test_result = "Pass"
                MIN_CPS = test_value
                test_value = (MAX_CPS + MIN_CPS) / 2
            else:
                IxLoadUtils.log('Test Iteration Fail')
                test_result = "Fail"
                MAX_CPS = test_value
                test_value = (MAX_CPS + MIN_CPS) / 2
            objective_cps = old_value
            obtained_cps = cps_max_w_ts[1]
            test_run_results.append(
                [test_iteration, objective_cps, obtained_cps, failures_dict["http_requests_failed"],
                 failures_dict["tcp_retries"], failures_dict["tcp_resets_tx"],
                 failures_dict["tcp_resets_rx"], test_result])
            IxLoadUtils.log("Iteration Ended...")
            IxLoadUtils.log('MIN_CPS = %d' % MIN_CPS)
            IxLoadUtils.log('Current MAX_CPS = %d' % MAX_CPS)
            IxLoadUtils.log('Previous CPS Objective value = %d' % old_value)
            print(' ')
            test_iteration += 1
            IxLoadUtils.releaseConfiguration(connection, session_url)

        cps_max_w_ts[1] = MIN_CPS

        return cps_max_w_ts, failures_dict, test_run_results, latency_ranges

    def _run_bg(self, connection, session_url, url_patch_dict, start_value=0):

        test_run_results = []
        test_value = start_value
        test_iteration = 1

        test_result = ""
        IxLoadUtils.log(
            "----Test Iteration %d------------------------------------------------------------------"
            % test_iteration)
        old_value = test_value

        IxLoadUtils.log("Applying config session {}, {}...".format(self.session_no, self.test_config_type))
        IxLoadUtils.applyConfiguration(connection, session_url)

        IxLoadUtils.log("Starting the test session {} {}...".format(self.session_no, self.test_config_type))
        IxLoadUtils.runTest(connection, session_url)
        IxLoadUtils.log("Test started session {} {}.".format(self.session_no, self.test_config_type))

        IxLoadUtils.log("Test running and extracting stats session {} {}...".format(self.session_no, self.test_config_type))
        stats_dict = self._poll_stats(connection, session_url, self.stats_test_settings)
        IxLoadUtils.log("Test finished session {} {}.".format(self.session_no, self.test_config_type))

        failures_dict, cps_max, cps_max_w_ts, latency_ranges = self._get_testrun_results(stats_dict, url_patch_dict,
                                                                                         self.test_config_type)

        self._print_stat_table(cps_max_w_ts, failures_dict, latency_ranges, self.test_config_type)

        test_run_results.append(
            [test_iteration, cps_max, failures_dict['http_requests_failed'],
             failures_dict['tcp_retries'], failures_dict['tcp_resets_tx'],
             failures_dict['tcp_resets_rx']]
        )

        return cps_max_w_ts, failures_dict, test_run_results, latency_ranges

    def _save_rxf(self):
        IxLoadUtils.log("Saving rxf session {}".format(self.session_no))
        file_path = "{}Hero_{}{}.rxf".format(self.save_rxf_path, self.test_config_type, self.id)
        IxLoadUtils.saveRxf(self.connection, self.session_url, file_path)

    def _set_ip_range_options(self, ip_count, eni_index, nodetype):

        client_host_count = self.url_patch_dict['ip_settings']['client']['host_count']
        client_increment = self.url_patch_dict['ip_settings']['client']['increment_by']
        server_host_count = self.url_patch_dict['ip_settings']['server']['host_count']
        server_increment = self.url_patch_dict['ip_settings']['server']['increment_by']

        if nodetype in "client":
            #host_count = int((ACL_RULES_NSG * IP_PER_ACL_RULE)/2)
            host_count = client_host_count
            incrementBy = client_increment
        else:
            host_count = server_host_count
            incrementBy = server_increment

        ip = str(self._build_node_ips(ip_count, eni_index, nodetype))

        IpOptionsToChange = {'count': host_count, 'ipAddress': ip, 'prefix': 8, 'incrementBy': incrementBy,
                             'gatewayAddress': "0.0.0.0", 'gatewayIncrement': '0.0.0.0'}


        return IpOptionsToChange

    def _set_mac_range_options(self, ip_count=0, eni_index=0, nodetype="client"):

        client_mac_increment = self.url_patch_dict['mac_settings']['client']['increment']
        server_mac_increment = self.url_patch_dict['mac_settings']['server']['increment']

        if nodetype in "client":
            mac_increment = client_mac_increment
        else:
            mac_increment = server_mac_increment

        mac_address = str(self._build_node_macs(ip_count, eni_index, nodetype))
        mac_address = mac_address.replace("-", ":")

        macOptionsToChange = {"mac": mac_address, "incrementBy": mac_increment}

        return macOptionsToChange

    def _set_vlan_range_options(self, url_patch_dict, index, nodetype="client"):

        if nodetype == 'client':
            firstId = url_patch_dict['client_vlan_settings']['json']['firstId'] + index
            uniqueCount = url_patch_dict['client_vlan_settings']['json']['uniqueCount']
        else:
            firstId = url_patch_dict['server_vlan_settings']['json']['firstId'] + index
            uniqueCount = url_patch_dict['server_vlan_settings']['json']['uniqueCount']

        vlan_settings = {'firstId': firstId, 'uniqueCount': uniqueCount}

        return vlan_settings
