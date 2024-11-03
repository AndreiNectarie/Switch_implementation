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


def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()

    # Printing interface names
    for i in interfaces:
        print(get_interface_name(i))
    

    vlan_config, switch_priority = load_vlan_config(switch_id)
    while True:
        # Note that data is of type bytes([...]).
        # b1 = bytes([72, 101, 108, 108, 111])  # "Hello"
        # b2 = bytes([32, 87, 111, 114, 108, 100])  # " World"
        # b3 = b1[0:2] + b[3:4].
        interface, data, length = recv_from_any_link()

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        # Print the MAC src and MAC dst in human readable format
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)
        
        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')

        print("Received frame of size {} on interface {}".format(length, interface), flush=True)

        # TODO: Implement forwarding with learning
        update_MAC_table(src_mac, interface)
        
        
        interface_name = get_interface_name(interface)
        # Implement VLAN support
        if vlan_id == -1:
            # check vlan_config for the vlan_id
            for i in vlan_config:
                if interface_name == i:
                    vlan_id = vlan_config[i][0]
        
        print (f"VLAN ID: {vlan_id}")
        # Forward the frame based on the destination MAC address
        if dest_mac in mac_table:
            # Forward the frame to the interface where the destination MAC is located
            dest_interface = mac_table[dest_mac]
            if dest_interface != interface:
                dest_interface_name = get_interface_name(dest_interface)
                if dest_interface_name in vlan_config:
                    # check if interface is trunk or access
                    if vlan_config[dest_interface_name] == -1:
                        # Add 802.1Q header if forwarding to a trunk port
                        # check first if data already has a VLAN tag
                        if data[12] != 0x81 and data[13] != 0x00:
                            data = add_8021Q_header(data, vlan_id)
                    else:
                        # Remove 802.1Q header if forwarding to an access port
                        # check first if data already has a VLAN tag
                        if data[12] == 0x81 and data[13] == 0x00:
                            data = remove_8021Q_header(data)
                    send_to_link(dest_interface, len(data), data)
                else:
                    print(f"Destination interface {dest_interface} not in VLAN {vlan_id}. Dropping frame.")
        else:
            # Flood the frame to all interfaces except the one where it came from, keeping in mind the VLAN
            
            #########################33
            # make the for from 1 to interface number max and pick only the ones in the vlan_config
            # so u have access to both the nr and the name of the interface - for the send_link function
            ########################3##
            for i in vlan_config.keys():
                if i != interface_name:
                    if vlan_id == -1:
                        # Add 802.1Q header if forwarding to a trunk port
                        # check first if data already has a VLAN tag
                        if data[12] != 0x81 and data[13] != 0x00:
                            data = add_8021Q_header(data, vlan_id)
                    else:
                        # Remove 802.1Q header if forwarding to an access port
                        # check first if data already has a VLAN tag
                        if data[12] == 0x81 and data[13] == 0x00:
                            data = remove_8021Q_header(data)
                    print(f"Flooding frame to interface {i}")
                    send_to_link(get_interface(i), len(data), data)
                else:
                    print(f"Interface {i} not in VLAN {vlan_id}. Dropping frame.")
        
        # TODO: Implement STP support

        # data is of type bytes.
        # send_to_link(i, length, data)

if __name__ == "__main__":
    main()
