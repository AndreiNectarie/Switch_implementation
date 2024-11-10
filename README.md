# switch.py

This file contains the main logic for a network switch implementation with VLAN redirecting and MAC address learning capabilities.

## Workflow

1. **Initialization**:
    - The switch is initialized with a unique ID and a list of network interfaces.
    - The `wrapper.init()` function initializes the interfaces and returns the number of interfaces.
    - VLAN configuration and switch priority are loaded using `load_vlan_config(switch_id)`.

2. **Thread for BDPU**:
    - A separate thread is started to send BDPUs every second using the `send_bdpu_every_sec()` function.

3. **Main Loop**:
    - The switch enters an infinite loop where it listens for incoming frames on any interface using `recv_from_any_link()`.
    - For each received frame:
        - The Ethernet header is parsed using `parse_ethernet_header(data)`.
        - Then the program checks if the destination MAC address is known, using the MAC table. If it does know the path, it will send it directly. If it doesn't, it will start flooding the network.
        - The VLAN ID is determined based on the frame and the interface configuration. VLAN ID = -1 means that we have a trunk interface which accepts packets with any VLAN ID.
        - When a packet is sent through a trunk interface, It will have an added header, 802.1Q. So every time a packet is sent to a destination, we first check if it has the added header. If it's being send through a trunk, i ll leave it in. If it s send to a host, i ll take it out and forward it.

## Added Functions

### `has_vlan_tag(data)`

Checks if the given data has a VLAN tag.

- **Parameters**: 
  - `data` (bytes): The raw Ethernet frame data.
- **Returns**: 
  - `bool`: `True` if the frame has a VLAN tag, `False` otherwise.

### `main()`

The main function that initializes the switch, starts the BDPU thread, and enters the main loop to process incoming frames.

## Dependencies

- `sys`
- `struct`
- `wrapper`
- `threading`
- `time`
- `helpers`
- `Switch`
