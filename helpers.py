import os
from switch import create_vlan_tag

mac_table = {}

def update_MAC_table(mac_addr, interface):
    # Update the MAC table with the new MAC address
    if(mac_addr not in mac_table) or (mac_table[mac_addr] != interface):
        # add the new MAC address to the table if it doesn t exit 
        # or if it is on a different interface
        mac_table[mac_addr] = interface

def add_vlan(vlan_config, vlan_id, interface):
    if interface not in vlan_config:
        vlan_config[interface] = []
    if vlan_id not in vlan_config[interface]:
        vlan_config[interface].append(vlan_id)

def load_vlan_config(switch_id):
    vlan_config = {}
    switch_priorities = {}
    config_dir = 'configs'
    
    for filename in os.listdir(config_dir):
        if filename.startswith('switch') and filename.endswith('.cfg') and filename[6] == switch_id:
            try:
                with open(os.path.join(config_dir, filename), 'r') as f:
                    lines = f.readlines()
                    switch_priorities[switch_id] = int(lines[0])
                    
                    for line in lines[1:]:  # Skip the first line (priority)
                        if line[0] == 'r' and line[1] == '-':
                            # format interface - vlan ID
                            interface, vlan_id = line.strip().split(' ')
                            vlan_id = int(vlan_id)
                            add_vlan(vlan_config, vlan_id, interface)
                        elif ' T' in line:
                            # we have a trunk
                            trunk_interface, _ = line.strip().split(' ')
                            # Add trunk interface to all VLANs
                            vlan_id = -1
                            add_vlan(vlan_config, vlan_id, trunk_interface)
                            
            except ValueError as e:
                print(f"Error processing file {filename}: {e}")
            break
    
    return vlan_config, switch_priorities

def add_8021Q_header(data, vlan_id):
    # Add a VLAN tag to the frame
    return data[0:12] + create_vlan_tag(vlan_id) + data[12:]

def remove_8021Q_header(data):
    # Remove the VLAN tag from the frame
    return data[0:12] + data[16:]
