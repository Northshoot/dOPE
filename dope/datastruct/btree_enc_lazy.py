import pdb

class BTNode:
    def __init__(self, isLeaf):
        self.n = 0
        self.isLeaf = isLeaf
        self.children = []
        self.keys = []

class BTree:
    def __init__(self, k):
        self.root = BTNode(True)
        self.k = k
        self.t = int(k/2)

    def split_child(self, x, i):
        '''
        Break child node into two children and bring median key into x
        '''
        pdb.set_trace()
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
                return None
            # query sensor for insert index calculation
            else:
                # Only query if no duplicate found
                if val in x.keys:
                    return None
                else:
                    return x.keys
                
        # Search recursively through internal nodes
        else:
            # query sensor for next child index
            if enc == []:
                # Only query if no duplicates found
                if val in x.keys:
                    return None
                else:
                    return x.keys

            # Passing through this node 
            else:
                if val in x.keys:
                    return None
                return self.insert_nonfull_enc(x.children[enc[0]], val, enc[1:])

    def rebalance_enc(self, x, enc):
        '''
        Probe the tree for a 
        '''
        if x.isLeaf:
            # Finished traversal
            return
        if x.children[enc[0]].n == 2*t - 1:
            # Store pointer to child
            next_child = x.children[enc[0]]
            # Rebalance child
            self.split_child(x, i)

            # Change encoding to point to next child
            if x.children[enc[0]] != next_child:
                enc[0] += 1



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
        compare = self.insert_nonfull_enc


        t = self.t
        # Root is full, rebalance before continuing rebalance probe
        if self.root.n == 2*t -1:
            old_root = self.root
            new_root = BTNode(False)
            self.root = new_root
            new_root.n = 0
            new_root.children.append(old_root)
            self.split_child(new_root, 0)
            return self.insert_nonfull_enc(self.root, val, enc)
        else:
            return self.insert_nonfull_enc(self.root, val, enc)


