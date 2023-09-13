# High Availability Test Plan

- [High Availability Test Plan](#high-availability-test-plan)
    - [Overview](#overview)
        - [Scope](#scope)
        - [Keysight Testbed](#keysight-testbed)
    - [Topology](#topology)
        - [Configuration for SmartSwitch Testing](#configuration-for-smartswitch-testing)
    - [Setup configuration](#setup-configuration)
    - [Test Methodology](#test-methodology)
    - [Test cases](#test-cases)
        - [Test case # 1 - Link Loss Local SmartSwitch](#test-case1-link-loss-local-smartswitch-)
            - [Test objective 1](#test-objective-1)
            - [Steps for Test Case 1](#steps-for-test-case-1)
        - [Test case # 2 - Link Loss Seperate SmartSwitch](#test-case2-link-loss-separate-smartswitch)
            - [Test objective 2](#test-objective-2)
            - [Test steps 2](#steps-for-test-case-2)
        - [Test case # 3 – DPU Loss Local SmartSwitch](#test-case3-dpuloss-local-smartswitch)
            - [Test objective 3](#test-objective-3)
            - [Test steps 3](#steps-for-test-case-3)
        - [Test case # 4 – DPU Loss Separate SmartSwitch](#test-case4-dpuloss-separate-smartswitch)
            - [Test objective 4](#test-objective-4)
            - [Test steps 4](#steps-for-test-case-4)
        - [Test case # 5 – Tor Loss Local SmartSwitch](#test-case5-tor-loss-local-smartswitch)
            - [Test objective 5](#test-objective-5)
            - [Test steps 5](#steps-for-test-case-5)
        - [Test case # 6 – Tor Loss Separate SmartSwitch](#test-case6-tor-loss-separate-smartswitch)
            - [Test objective 6](#test-objective-6)
            - [Test steps 6](#steps-for-test-case-6)

## Overview
The purpose of these tests is to evaluate various High Availability (HA) scenarios associated with testing planned and unplanned events in the SmartSwitch system.

### Scope
These tests are targeted on a fully functioning SmartSwitch system. We will be measuring the system as a whole while evaluating HA scenarios such as 100% link loss, DPU, and Grey failover.

### Keysight Testbed
Tests will run on the following testbeds.

![HA_TestBed](images/ha_testbed.png)

Model expanded to show Keysight chassis, UHD, and SmartSwitch.  The UHD and SmartSwitchs can be used to conifgure various test case scenarios and network configurations.  For example, simulating DPUs within the same SmartSwitch or pairing distant DPUs to form HA sets.  The UHD has the ability to be configured in such a way to simulate individual ToRs.  The UHD shall additionally be used with Stateful traffic for VxLan encapsulation and decapsulation.

![HA_SmartSwitch_Topology](images/smartswtich_ha_topology.png)

## Topology
### Configuration for HA testing
![HA_topology](images/ha_test_topology.png)

## Setup Configuration
Two DPUs will use similar network configurations (VxLAN, ENI) forming an HA set.  One DPU will be designated as the Active the second Standby.

## Test Methodology
Following test methodology will be used for measuring HA switchover and performance.
* Traffic generator will be used to configure ENI peering between DPU ports.
* Data traffic will be sent from  server to server, server to T1 and T1 to server.
* Depending on the test case, switchovers/failovers will be generated and measured.
* Switchover between DPUs will be measured by noting down the precise time of the switchover/failover event.  Traffic generator will create those timestamps and provide us with the recovery statistics.


## Test cases
### Test case1 Link Loss Local SmartSwitch 
#### Test Objective 1
In this scenario we will test the switchover between an Active DPU to it's paired Standby DPU.

![HA_LinkLoss](images/ha_linkloss_test.png)
#### Steps for Test Case 1
* Configure 2 DPUs networked within the same SmartSwitch forming a HA set between DPU0 and DPU1.
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU1.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU1.
* The HA set shall be configured within the same SmartSwitch.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port remove link connection between Tor1 and DPU0 port 1.
* Mark start time at beginning of test as link connection is removed.
* There should be 100% link failure with the Active DPU during switchover.
* DPU1 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU1 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.


### Test case2 Link Loss Separate SmartSwitch
#### Test Objective 2
In this scenario we will test the switchover between an Active DPU to it's paired DPU from a separate SmartSwitch

![HA_LinkLoss](images/ha_linkloss_test_notlocal.png)
#### Steps for Test Case 2
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.  Both DPUs will be placed into their own SmartSwitch.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU3.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU3.
* The HA set shall be in separate SmartSwitches.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port remove link connection between Tor1 and DPU0 port 1.
* Mark start time at beginning of test as link connection is removed.
* There should be 100% link failure with the Active DPU during switchover.
* DPU1 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU3 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.


### Test case3 DPULoss Local SmartSwitch
#### Test Objective 3

![HA_DPULoss_Local](images/ha_dpuloss_test.png)
#### Steps for Test Case 3
* Configure 2 DPUs networked within the same SmartSwitch forming a HA set.
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU1.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU1.
* The HA set shall be configured within the same SmartSwitch.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port poweroff or reboot Active DPU.
* Mark start time at beginning of test as DPU is removed from topology.
* There should be 100% failure with the Active DPU during switchover.
* DPU1 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU1 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.


### Test case4 DPULoss Separate SmartSwitch
#### Test Objective 4

![HA_DPULoss_NotLocal](images/ha_dpuloss_not_local.png)

#### Steps for Test Case 4
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.  Both DPUs will be placed into their own SmartSwitch.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU3.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU3.
* The HA set shall be in separate SmartSwitches.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port poweroff or reboot Active DPU.
* Mark start time at beginning of test as DPU is removed from topology.
* There should be 100% failure with the Active DPU during switchover.
* DPU3 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU3 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.


### Test case5 ToR Loss Local SmartSwitch
#### Test Objective 5

![HA_LinkLoss](images/ha_torloss_test.png)
#### Steps for Test Case 5
* Configure 2 DPUs networked within the same SmartSwitch forming a HA set.
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU1.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU1.
* The HA set shall be configured within the same SmartSwitch.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port poweroff or reboot Tor1.
* Mark start time at beginning of test as DPU is removed from topology.
* There should be 100% failure with the Active DPU during switchover.
* DPU1 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU1 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.


### Test case6 ToR Loss Separate SmartSwitch
#### Test Objective 6

![HA_LinkLoss](images/ha_torloss_not_local.png)
#### Steps for Test Case 6
* The SmartSwitch configuration will consist of 2 DPUs sharing the same network configurations such as: IPs, MACs, VLan/VxLan, ENIs.  Both DPUs will be placed into their own SmartSwitch.
* The UHD will be configured to split ToR traffic into two separate entities.
* There will be a physical link between Tor1 and port1 of both DPU0 and DPU3.  Additionally, a physical connection between Tor2 and port2 of DPU0 and DPU3.
* The HA set shall be in separate SmartSwitches.
* Verify links are up and start all protocols and verify traffic is established.
* Enable csv logging and check the state of the DPUs through the API.
* Apply and start traffic stateful and stateless.
* Verify traffic is flowing without any loss.
* Through mgmt port poweroff or reboot Tor1.
* Mark start time at beginning of test as Tor1 is removed from topology.
* There should be 100% failure with the Active DPU during switchover.
* DPU3 shall become the new Active DPU in the HA set.
* Mark time when the Standby DPU becomes Active and fully running traffic.
* Measure convergence time from start of the link removal on DPU0 and DPU3 switchover.
* Using traffic generator tools to verify metrics associated with number of Concurrent Connections, Connection rate, and TCP/UDP failures collect data before, during and after switchover.