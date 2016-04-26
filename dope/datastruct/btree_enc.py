import pdb

class BTNode:
    def __init__(self, isLeaf):
        self.n = 0
        self.isLeaf = isLeaf
        self.children = []
        self.keys = []

    def __str__(self):


class BTree:
    def __init__(self, k):
        self.root = BTNode(True)
        self.k = k
        self.t = int(k/2)
        self.num_rebal = 0

    def __str__(self):
        # Traverse level by level to get all keys, then print
        


    def insert_direct(self, val, enc, node_idx):
        '''
        Put val into this tree exactly at encoding enc
        '''
        node = self.root
        # Find the node to add
        for index in enc:
            new_node = node.children[index]
            if new_node is None:
                new_node = BTNode(True)
                node.children[index] = new_node
            node = new_node

        # Add at the specified index
        node.keys.insert(node_idx, val)
        node.n += 1

    def node_at_enc(self, enc):
        '''
        Return the values contained in this node of the B tree
        '''
        node = self.root
        for index in enc:
            node = node.children[index]
        return node


    def trigger_rebalance(self, enc):
        '''
        Trigger a rebalance in the overfull node located at enc
        '''
        t = self.t

        # Root rebalance
        if self.root.n == 2*t -1:
            old_root = self.root
            self.root = BTNode(False)
            self.root.n = 0
            self.root.children.append(old_root)
            self.split_child(self.root, 0)
        # Non-root rebalance
        else:
            node = self.root
            while enc != []:
                child_idx = enc.pop(0)
                if node.children[child_idx].n == 2*t - 1:
                    # Calculate new encoding
                    self.split_child(node,child_idx)
                    if enc != []:
                        child_idx = child_idx if enc[0] < t else child_idx + 1
                        node = node.children[child_idx]
                        enc[0] = enc[0] if enc[0] < t else enc[0] - t
                else:
                    node = node.children[child_idx]



    def split_child(self, x, i):
        '''
        Break child node into two children and bring median key into x
        '''
        self.num_rebal += 1
        t = self.t
        y = x.children[i]
        z = BTNode(y.isLeaf)

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

    def insert_nonfull_enc(self, x, val, enc):
        '''
        Traverse b tree looking to insert val starting at x
        using encoding enc
        '''
        t = self.t
        if x.isLeaf:
            # insert index calculated
            if len(enc) == 1:
                # Index should be within 1 of the number of keys at the node
                assert(enc[0] < x.n +1) 
                x.keys.insert(enc[0], val)
                x.n += 1
                return None, -1
            # query sensor for insert index calculation
            else:
                # Only query if no duplicate found
                if val in x.keys:
                    return None, -1
                else:
                    return x.keys, -1
                
        # Search recursively through internal nodes
        else:
            # query sensor for next child index
            if enc == []:
                # Only query if no duplicates found
                if val in x.keys:
                    return None, -1
                else:
                    return x.keys, -1

            # Our first search through this node
            else:
                # Only add non-repeats
                if val in x.keys:
                    return None, -1

                assert(enc[0] < x.n + 1)
                # Check if a split is necessary
                if x.children[enc[0]].n == 2*t -1:
                    self.split_child(x,enc[0])
                    if val in x.keys:
                        return None, -1
                    # Redo query 
                    return x.keys, len(enc)
                return self.insert_nonfull_enc(x.children[enc[0]], val, enc[1:])

           

    def insert_enc(self, val, enc):
        '''
        Traverse B tree down the path specified by enc and attempt
        to insert val.  If enc points to a leaf node then val is 
        inserted and the return value is None, else the node's values
        will be returned for sending to the sensor for comparison.
        enc is a list of numbers between 0 and k-1 indicating which
        child index should be searched next at every node.
        '''
        #pdb.set_trace()
        t = self.t
        # Root is full, rebalance before continuing traversal
        if self.root.n == 2*t -1:
            old_root = self.root
            new_root = BTNode(False)
            self.root = new_root
            new_root.n = 0
            new_root.children.append(old_root)
            self.split_child(new_root, 0)
            if enc != []:
                return self.root.keys, len(enc)
            return self.insert_nonfull_enc(self.root, val, enc)
        else:
            return self.insert_nonfull_enc(self.root, val, enc)

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



