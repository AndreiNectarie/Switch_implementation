#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from helpers import *
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
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

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))
    
    vlan_config, switch_priority = load_vlan_config(switch_id)
    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()
    

    print (vlan_config)
    
    mac_table = {}
    while True:
        src_interface, data, length = recv_from_any_link()
        data_to_send = data

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data_to_send)
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)
        
        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print("Received frame of size {} on interface {}".format(length, get_interface_name(src_interface)), flush=True)

        # TODO: Implement forwarding with learning
        mac_table[src_mac] = src_interface
        
        
        interface_name = get_interface_name(src_interface)
        # Implement VLAN support
        
        if vlan_id == -1 and vlan_config[interface_name] != -1:
            # associate the VLAN ID with the interface
            vlan_id = vlan_config[interface_name]
        
        print (f"VLAN ID: {vlan_id}")
        print (mac_table)
        # Forward the frame based on the destination MAC address
        if dest_mac in mac_table:
            # Forward the frame to the interface where the destination MAC is located
            dest_interface = mac_table[dest_mac]
            if dest_interface != src_interface:
                dest_interface_name = get_interface_name(dest_interface)
                print("FOUND INTERFACE")
                if vlan_config[dest_interface_name] == -1:
                    # Add 802.1Q header if forwarding to a trunk port
                    # check first if data already has a VLAN tag
                    if not has_vlan_tag(data_to_send):
                        data_to_send = add_8021Q_header(data_to_send, vlan_id)
                    print(f"FORWARDING frame to TRUNK {dest_interface_name}")
                    send_to_link(dest_interface, len(data_to_send), data_to_send)
                elif vlan_id == vlan_config[dest_interface_name]:
                    # Remove 802.1Q header if forwarding to an access port
                    # check first if data already has a VLAN tag
                    if has_vlan_tag(data_to_send):
                        data_to_send = remove_8021Q_header(data_to_send)
                    print(f"FORWARDING frame to interface {dest_interface_name}")
                    send_to_link(dest_interface, len(data_to_send), data_to_send)
            else:
                print(f"Destination MAC is on the same interface. Dropping frame.")
        else:
            # Flood the frame to all interfaces except the one where it came from, keeping in mind the VLAN
            print ("FLOODING")
            for i in interfaces:
                if i != src_interface:
                    i_name = get_interface_name(i)
                    if vlan_config[i_name] == -1:
                        # Add 802.1Q header if forwarding to a trunk port
                        # check first if data already has a VLAN tag
                        if not has_vlan_tag(data_to_send):
                            data_to_send = add_8021Q_header(data_to_send, vlan_id)
                        print(f"Flooding frame to trunk interface {i_name}")
                        send_to_link(i, len(data_to_send), data_to_send)
                    elif vlan_id == vlan_config[i_name]:
                        # Remove 802.1Q header if forwarding to an access port
                        # check first if data already has a VLAN tag
                        if has_vlan_tag(data_to_send):
                            data_to_send = remove_8021Q_header(data_to_send)
                        print(f"Flooding frame to access interface {i_name}")
                        send_to_link(i, len(data_to_send), data_to_send)
        
        # TODO: Implement STP support

        # data is of type bytes.
        # send_to_link(i, length, data)

if __name__ == "__main__":
    main()
