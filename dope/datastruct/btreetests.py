# from btree_enc import BTNode, BTree

# bt = BTree(None, 8)
# left = BTNode(True, 8)
# left.keys = [1,2]
# right = BTNode(True, 8)
# right.keys = [27, 38]
# center = BTNode(True, 8)
# center.keys = [6,7,8,9,10,11,12]
# bt.root.keys = [5,15]
# bt.root.children = [left, center, right]

# bt.split_child(bt.root, 1)

# c = BTree(None, 8)
# l = range(2000)
# for i, item in enumerate(l):
#     c.insert(item)
#     c.insert(item)

# for i, item in enumerate(l):
#     c.insert(item)


from btree_enc import BTree
import random


bt = BTree(10)
l = [random.randint(0,999) for r in xrange(2000)]

def inserter(bt, l):
    for i, item in enumerate(l):
        # Perform a traversing insert of this item into tree bt
        enc = []
        compare, overwrite = bt.insert_enc(item, enc)
        while compare is not None:
            # Find next index
            if compare == []:
                next = 0
            else:
                i = 0
                while i < len(compare) and compare[i] < item:
                    i += 1
                next = i
            # Append to or overwrite encoding
            if overwrite >= 0:
                # clear last overwrite elements from enc
                del enc[-1*overwrite:]
            # add next
            enc.append(next)
            print(enc)
            compare, overwrite = bt.insert_enc(item, enc)




