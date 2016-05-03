class BTNode:
    def __init__(self, isLeaf, k):
        self.n = 0
        self.isLeaf = isLeaf
        self.k = k
        self.children = []
        self.keys = []


class BTree:
    def __init__(self, val, k):
        self.root = BTNode(True, k)
        self.k = k
        self.t = int(k/2)

    def split_child(self, x, i):
        '''
        Break child node into two children and bring median key into x
        '''
        t = self.t
        y = x.children[i]
        z = BTNode(y.isLeaf, self.k)

        # Set up new child z with the right half of y's keys and children
        z.n = t - 1
        for j in range(t - 1):
            z.keys.append(y.keys[j+t])
        median = y.keys[t-1]
        del y.keys[t-1:]
        if not y.isLeaf:
            for j in range(t):
                z.children.append(y.children[j+t])
            del y.children[t:]
        y.n = t-1

        # Update node x to contain the median
        x.children.insert(i+1,z)
        x.keys.insert(i,median)
        x.n += 1

    def insert_nonfull(self, x,val):
        '''
        Insert value into the btree starting at node x
        Precondition: x is not a full node
        '''
        t = self.t
        i = x.n - 1
        # Insert val into leaf node x
        if x.isLeaf:
            while i >= 0 and val < x.keys[i]:
                i = i - 1
            # Only add non-repeats
            if not val in x.keys:
                x.keys.insert(i + 1, val)
                x.n += 1
        # Continue searching for the insert leaf node
        else:
            while i >= 0 and val < x.keys[i]:
                i = i - 1
            i += 1
            # Check if a split is necessary
            if x.children[i].n == 2*t -1:
                self.split_child(x, i)
                if val > x.keys[i]:
                    i = i + 1
            # Only add non-repeats
            if not val in x.keys:
                self.insert_nonfull(x.children[i], val)

    def insert(self, val):
        '''
        Insert val into this b tree.  Begin traversal at the root
        '''
        t = self.t
        # Root is full, rebalance before continuing traversal
        if self.root.n == 2*t - 1:
            old_root = self.root
            new_root = BTNode(False, self.k)
            self.root = new_root
            new_root.n = 0
            new_root.children.append(old_root)
            self.split_child(new_root, 0)
            self.insert_nonfull(new_root, val)
        else:
            self.insert_nonfull(self.root, val)

    def __iter__(self):
        def _recurse(node):
            if node.children:
                for child, item in zip(node.children, node.keys):
                    for child_item in _recurse(child):
                        yield child_item
                    yield item
                for child_item in _recurse(node.children[-1]):
                    yield child_item
            else:
                for item in node.keys:
                    yield item

        for item in _recurse(self.root):
            yield item

