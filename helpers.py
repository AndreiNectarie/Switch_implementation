import os
from switch import create_vlan_tag

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
                            vlan_config[interface] = vlan_id
                        elif ' T' in line:
                            # we have a trunk
                            trunk_interface, _ = line.strip().split(' ')
                            # Add trunk interface to all VLANs
                            vlan_config[trunk_interface] = -1
                            
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
