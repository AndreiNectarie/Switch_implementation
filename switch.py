#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from helpers import *
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name
import Switch

def parse_ethernet_header(data):
    dest_mac = data[0:6]
    src_mac = data[6:12]
    
    # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    # 0x8100 for the Ethertype for 802.1Q
    # vlan_id & 0x0FFF ensures that only the last 12 bits are used
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def send_bdpu_every_sec():
    while True:
        # TODO Send BDPU every second if necessary
        time.sleep(1)

def has_vlan_tag(data):
    # Check if the packet has an 802.1Q VLAN tag
    ether_type = (data[12] << 8) + data[13]
    return ether_type == 0x8200


def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)
    
    vlan_config, switch_priority = load_vlan_config(switch_id)
    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()
    
    mac_table = {}
    while True:
        src_interface, data, length = recv_from_any_link()
        data_to_send = data

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data_to_send)
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)
        
        # TODO: Implement forwarding with learning
        mac_table[src_mac] = src_interface
        
        
        interface_name = get_interface_name(src_interface)
        
        if vlan_id == -1 and vlan_config[interface_name] != -1:
            vlan_id = vlan_config[interface_name]
        
        # try to forward the frame based on the destination MAC address
        if dest_mac in mac_table:
            dest_interface = mac_table[dest_mac]
            if dest_interface != src_interface:
                dest_interface_name = get_interface_name(dest_interface)
                if vlan_config[dest_interface_name] == -1:
                    # Add 802.1Q header if forwarding to a trunk port
                    # check first if data already has a VLAN tag
                    if not has_vlan_tag(data_to_send):
                        data_to_send = add_8021Q_header(data_to_send, vlan_id)
                    send_to_link(dest_interface, len(data_to_send), data_to_send)
                elif vlan_id == vlan_config[dest_interface_name]:
                    # Remove 802.1Q header if forwarding to an access port
                    # check first if data already has a VLAN tag
                    if has_vlan_tag(data_to_send):
                        data_to_send = remove_8021Q_header(data_to_send)
                    send_to_link(dest_interface, len(data_to_send), data_to_send)
        else:
            # Flood the frame to all interfaces except the one where it came from, keeping in mind the VLAN
            for i in interfaces:
                if i != src_interface:
                    i_name = get_interface_name(i)
                    if vlan_config[i_name] == -1:
                        # Add 802.1Q header if forwarding to a trunk port
                        # check first if data already has a VLAN tag
                        if not has_vlan_tag(data_to_send):
                            data_to_send = add_8021Q_header(data_to_send, vlan_id)
                        send_to_link(i, len(data_to_send), data_to_send)
                    elif vlan_id == vlan_config[i_name]:
                        # Remove 802.1Q header if forwarding to an access port
                        # check first if data already has a VLAN tag
                        if has_vlan_tag(data_to_send):
                            data_to_send = remove_8021Q_header(data_to_send)
                        send_to_link(i, len(data_to_send), data_to_send)

if __name__ == "__main__":
    main()
