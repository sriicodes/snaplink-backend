import hashlib

class ConsistentHashRing:
    def __init__(self):
        self.ring = {}
        self.sorted_keys = []

    def add_node(self, node):
        # Hash the node name to get its position on the ring
        key = self._hash(node)
        self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())
        print(f"Node '{node}' added at position {key}")

    def remove_node(self, node):
        key = self._hash(node)
        del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())
        print(f"Node '{node}' removed")

    def get_node(self, short_code):
        if not self.ring:
            return None
        # Hash the short code to find its position
        key = self._hash(short_code)
        # Find nearest node clockwise
        for node_key in self.sorted_keys:
            if key <= node_key:
                return self.ring[node_key]
        # Wrap around — return first node
        return self.ring[self.sorted_keys[0]]

    def _hash(self, value):
        return int(hashlib.md5(value.encode()).hexdigest(), 16)