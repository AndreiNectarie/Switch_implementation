import time
import threading

class Switch:
    def __init__(self, priority_value, trunk_ports):
        self.priority_value = priority_value
        self.own_bridge_ID = priority_value
        self.root_bridge_ID = self.own_bridge_ID
        self.root_path_cost = 0
        self.trunk_ports = trunk_ports
        self.port_states = {port: 'BLOCKING' for port in trunk_ports}
        self.root_port = None

        # Set all ports to DESIGNATED if this switch is the root bridge
        if self.own_bridge_ID == self.root_bridge_ID:
            for port in self.trunk_ports:
                self.port_states[port] = 'DESIGNATED_PORT'

        # Start periodic BPDU sending
        self.start_bpdu_sending()

    def start_bpdu_sending(self):
        def send_bpdu_periodically():
            while True:
                if self.own_bridge_ID == self.root_bridge_ID:
                    self.send_bpdu()
                time.sleep(1)

        threading.Thread(target=send_bpdu_periodically, daemon=True).start()

    def send_bpdu(self):
        bpdu = {
            'root_bridge_ID': self.root_bridge_ID,
            'sender_bridge_ID': self.own_bridge_ID,
            'sender_path_cost': self.root_path_cost
        }
        for port in self.trunk_ports:
            self.send_to_port(port, bpdu)

    def send_to_port(self, port, bpdu):
        # Placeholder for sending BPDU to a port
        print(f"Sending BPDU on port {port}: {bpdu}")

    def receive_bpdu(self, port, bpdu):
        if bpdu['root_bridge_ID'] < self.root_bridge_ID:
            self.root_bridge_ID = bpdu['root_bridge_ID']
            self.root_path_cost = bpdu['sender_path_cost'] + 10
            self.root_port = port

            for p in self.trunk_ports:
                if p != self.root_port:
                    self.port_states[p] = 'BLOCKING'

            if self.port_states[self.root_port] == 'BLOCKING':
                self.port_states[self.root_port] = 'LISTENING'

            self.forward_bpdu(bpdu)

        elif bpdu['root_bridge_ID'] == self.root_bridge_ID:
            if port == self.root_port and bpdu['sender_path_cost'] + 10 < self.root_path_cost:
                self.root_path_cost = bpdu['sender_path_cost'] + 10
            elif port != self.root_port:
                if bpdu['sender_path_cost'] > self.root_path_cost:
                    if self.port_states[port] != 'DESIGNATED_PORT':
                        self.port_states[port] = 'LISTENING'

        elif bpdu['sender_bridge_ID'] == self.own_bridge_ID:
            self.port_states[port] = 'BLOCKING'
        else:
            pass  # Discard BPDU

        if self.own_bridge_ID == self.root_bridge_ID:
            for port in self.trunk_ports:
                self.port_states[port] = 'DESIGNATED_PORT'

    def forward_bpdu(self, bpdu):
        updated_bpdu = {
            'root_bridge_ID': self.root_bridge_ID,
            'sender_bridge_ID': self.own_bridge_ID,
            'sender_path_cost': self.root_path_cost
        }
        for port in self.trunk_ports:
            if port != self.root_port:
                self.send_to_port(port, updated_bpdu)
                