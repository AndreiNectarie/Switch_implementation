import wrapper
import threading
import time
from helpers import *
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name
from stp import Switch  # Import the Switch class from the STP implementation

def parse_ethernet_header(data):
    dest_mac = data[0:6]
    src_mac = data[6:12]
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def send_bdpu_every_sec(stp_switch):
    while True:
        if stp_switch.own_bridge_ID == stp_switch.root_bridge_ID:
            stp_switch.send_bpdu()
        time.sleep(1)

def has_vlan_tag(data):
    ether_type = (data[12] << 8) + data[13]
    return ether_type == 0x8200

# Initialize the STP switch
priority_value = 1  # Example priority value
trunk_ports = ['port1', 'port2', 'port3']  # Example trunk ports
stp_switch = Switch(priority_value, trunk_ports)

# Start the thread to send BPDUs every second
threading.Thread(target=send_bdpu_every_sec, args=(stp_switch,), daemon=True).start()

# Existing code for frame forwarding
interface_name = get_interface_name(src_interface)

if vlan_id == -1 and vlan_config[interface_name] != -1:
    vlan_id = vlan_config[interface_name]

print(f"VLAN ID: {vlan_id}")
print(mac_table)

# Check if the port is in a state that allows forwarding
if stp_switch.port_states.get(interface_name) in ['LISTENING', 'DESIGNATED_PORT']:
    # Try to forward the frame based on the destination MAC address
    if dest_mac in mac_table:
        dest_interface = mac_table[dest_mac]
        if dest_interface != src_interface:
            dest_interface_name = get_interface_name(dest_interface)
            if vlan_config[dest_interface_name] == -1:
                # Add 802.1Q header if forwarding to a trunk port
                if not has_vlan_tag(data_to_send):
                    data_to_send = add_8021Q_header(data_to_send, vlan_id)
                print(f"FORWARDING frame to TRUNK {dest_interface_name}")
                send_to_link(dest_interface, len(data_to_send), data_to_send)
            elif vlan_id == vlan_config[dest_interface_name]:
                # Remove 802.1Q header if forwarding to an access port
                if has_vlan_tag(data_to_send):
                    data_to_send = remove_8021Q_header(data_to_send)
                print(f"FORWARDING frame to interface {dest_interface_name}")
                send_to_link(dest_interface, len(data_to_send), data_to_send)
        else:
            print(f"Destination MAC is on the same interface.")
    else:
        # Flood the frame to all interfaces except the one where it came from, keeping in mind the VLAN
        for i in interfaces:
            if i != src_interface:
                i_name = get_interface_name(i)
                if vlan_config[i_name] == -1:
                    # Add 802.1Q header if forwarding to a trunk port
                    if not has_vlan_tag(data_to_send):
                        data_to_send = add_8021Q_header(data_to_send, vlan_id)
                    print(f"FLOODING frame to TRUNK {i_name}")
                    send_to_link(i, len(data_to_send), data_to_send)
                elif vlan_id == vlan_config[i_name]:
                    # Remove 802.1Q header if forwarding to an access port
                    if has_vlan_tag(data_to_send):
                        data_to_send = remove_8021Q_header(data_to_send)
                    print(f"FLOODING frame to interface {i_name}")
                    send_to_link(i, len(data_to_send), data_to_send)
else:
    print(f"Port {interface_name} is BLOCKING, frame not forwarded.")

# Example function to handle incoming BPDU packets
def handle_bpdu_packet(port, bpdu):
    stp_switch.receive_bpdu(port, bpdu)

# Example usage of handle_bpdu_packet
# handle_bpdu_packet('port1', received_bpdu)