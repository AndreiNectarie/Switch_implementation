



mac_table = {}

def update_MAC_table(mac_addr, interface):
    # Update the MAC table with the new MAC address
    if(mac_addr not in mac_table) or (mac_table[mac_addr] != interface):
        # add the new MAC address to the table if it doesn t exit 
        # or if it is on a different interface
        mac_table[mac_addr] = interface