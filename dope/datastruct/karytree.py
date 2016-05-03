
class KAryLevel:
    def __init__(self):
        self.isLeaf = True
        self.size = 0
        self.rootNode = None

class KAryNode:
    def __init__(self,val,right_of_root):
        self.right_of_root = False
        self.data = val
        self.left = None
        self.right = None
        self.left_level = None
        self.right_level = None


class KAryTree:
    def __init__(self, val):
        self.root = KAryLevel()
        self.root.rootNode = KAryNode(val, False)
        self.root.size = 1


def leftmostnode(node):
    prev_node = node
    while node.left is not None:
        prev_node = node
        node = node.left
    return prev_node

def thirdnode(root_node):
    leftnode = leftmostnode(root_node)
    return (leftnode.right).right

def fifthnode(root_node):
    leftnode = leftmostnode(root_node)
    return (((leftnode.right).right).right).right

def seventhnode(root_node):
    leftnode = leftmostnode(root_node)
    return (((((leftnode.right).right).right).right).right).right

def sixthnode(root_node):
    leftnode = leftmostnode(root_node)
    return (((((leftnode.right).right).right).right).right)

def ninethnode(root_node):
    leftnode = leftmostnode(root_node)
    return (((((((leftnode.right).right).right).right).right).right).right).right

def insert_between_nodes(l, r, new):
    assert(l.right == r and r.left == l)
    if l is None:
        r.left = new
        new.right = r
        return
    if r is None:
        l.right = new
        new.left = l
        return
    l.right = new
    new.left = l
    new.right = r
    r.left = new




# (Addition for parent, l level, r level, child level)
def rebalance(parent_level, level):
    # Rebalancing the root
    #assert(level.size == 11)
    if level.size > 10:
        new_left_level = KAryLevel()
        new_right_level = KAryLevel()

        new_left_level.size = 5
        new_left_level.isLeaf = level.isLeaf
        new_right_level.size = 5
        new_left_level.isLeaf = level.isLeaf
        new_left_level.rootNode = thirdnode(level.rootNode)
        new_right_level.rootNode = ninethnode(level.rootNode)

        clearleftnode = fifthnode(level.rootNode)
        clearrightnode = seventhnode(level.rootNode)

        new_root = sixthnode(level.rootNode)
        new_root.left = None
        new_root.right = None

        clearleftnode.right = None
        clearrightnode.left = None


        if parent_level is None or parent_level.size >= 10:
            # Make a new level and put root in it
            new_root_level = KAryLevel()
            new_root_level.rootNode = new_root
            new_root_level.size = 1
            new_root_level.isLeaf = False
            new_root.left_level = new_left_level
            new_root.right_level = new_right_level
            return (None, None, None, new_root_level)
        else:
            return (new_root, new_left_level, new_right_level, None)

        # Otherwise the new root gets added to the parent

      # No rebalance needed here, search through rest of the tree
    else:
        search_node = leftmostnode(level.rootNode)
        (insert, new_left, new_right, new_level) = rebalance(level, search_node.left_level)
        search_node.left_level = new_level
        if insert is not None:
            insert_between_nodes(search_node.left, search_node, insert)
            search_node.left_level = new_left
            search_node.right_level = new_right
            return

        while search_node != level.rootNode:
            search_node = search_node.r
            (insert, new_left, new_right, new_level) = rebalance(level, search_node.right_level)
            search_node.left_level = new_level
            if insert is not None:
                insert_between_nodes(search_node, search_node.right, insert)
                search_node.right_level = new_left
                insert.right_level = new_right
                return (None, None, None, level)
            search_node = search_node.right

        while search_node.right != None:
            (insert, new_left, new_right, new_level) = rebalance(level, search_node.left_level)
            if insert is not None:
                insert_between_nodes(search_node.left, search_node, insert)
                search_node.left_level = new_left
                insert.left_level = new_right
                return (None, None, None, level)
            search_node = search_node.right

        (insert, new_left, new_right, new_level) = rebalance(level, search_node.left_level)
        if insert is not None:
            if insert is not None:
                insert_between_nodes(search_node.left, search_node, insert)
                search_node.left_level = new_left
                insert.left_level = new_right
                return (None, None, None, level)


        (insert, new_left, new_right, new_level) = rebalance(level, search_node.right_level)
        if insert is not None:
            insert_between_nodes(search_node, search_node.right, insert)
            insert.left_level = new_left
            insert.right_level = new_right
            return (None, None, None, level)



# ( Data to compare, new node, data added to this level, level added)
def _traverse_insert_node(node, encoding, val, right_of_root, is_leaf):
    #print("Node")
    if encoding == []:
        if node is None:
            # Add node
            print("Adding node with value: " + str(val) + " to our level")
            return (None, KAryNode(val, right_of_root), True, False)
        else:
            if val == node.data:
                #Found the data
                return (None, node, False, False)
            else:
                # Need to decrypt data at this node to continue
                return (node.data, node, False, False)
    else:
        if node is None:
            raise ValueError("Encoding points beyond this tree")
        # Search the left branch
        elif encoding[0] == 0:
            # Left edge of level
            if node.left is None and not is_leaf:
                (out_data, new_level) = _traverse_insert_level(node.left_level, encoding[1:], val)
                node.left_level = new_level
                return (out_data, node, False, True)

            # Left of root stay on this level
            if not right_of_root:
                (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.left, encoding[1:], val, right_of_root, is_leaf)
                node.left = new_node
                return (out_data, node, data_added, level_added)

            # Right of root go down left child level
            if right_of_root:
                (out_data, new_level) = _traverse_insert_level(node.left_level, encoding[1:], val)
                node.left_level = new_level
                return (out_data, node, False, True)


        # Search the right branch
        else:
            # Right edge of level
            if node.right is None and not is_leaf:
                (out_data, new_level) = _traverse_insert_level(node.right_level, encoding[1:], val)
                node.right_level = new_level
                return (out_data, node, False, True)

            # Right of root stay on this level
            if right_of_root:
                print("We are staying on this level moving right ")
                (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.right, encoding[1:], val, right_of_root, is_leaf)
                node.right = new_node
                return (out_data, node, data_added, level_added)

            # Left of root go down right child level
            if not right_of_root:
                print("We are going down a level because we are left of the root")
                (out_data, new_level) = _traverse_insert_level(node.right_level, encoding[1:], val)
                node.right_level = new_level
                return (out_data, node, False, True)



# (Data to compare, new level)
def _traverse_insert_level(level, encoding, val):
    #print("level")
    if encoding == []:
        #print("Enc []")
        if level is None:
            level = KAryLevel()
            level.rootNode = KAryNode(val, False)
            level.size += 1
            return (None, level)

        node = level.rootNode

        if val == node.data:
            # Found the value
            return (None, level)
        else:
            # Need to decrypt data at this node to continue traversal
            return (node.data, level)

    else:
        if level is None:
            raise ValueError("Encoding points beyond tree")
            #Traverse the next level 
        # Search to the left
        node = level.rootNode
        if encoding[0]==0:
            #print("Enc 0")
            # Case where root is left end
            if node.left is None and not level.isLeaf:
                (out_data, new_level) = _traverse_insert_level(node.left_level, encoding[1:], val)
                node.left_level = new_level
                level.isLeaf = False
                return (out_data, level)
            (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.left, encoding[1:], val, False, level.isLeaf)
            node.left = new_node
            new_node.right = node
            if level_added:
                level.isLeaf = False
            if data_added:
                level.size += 1
            return (out_data, level)

        # Search to the right
        else: 
            #print("Enc 1")
            # Case where root is right end
            if node.right is None and not level.isLeaf:
                (out_data, new_level) = _traverse_insert_level(node.right_level, encoding[1:], val)
                node.right_level = new_level
                level.isLeaf = False
                return (out_data, level)
            print("traversing nodes at this level")
            (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.right, encoding[1:], val, True, level.isLeaf)
            node.right = new_node
            new_node.left = node
            if level_added:
                level.isLeaf = False
            if data_added:
                level.size += 1
            return (out_data, level)




def traverse_insert(ktree, encoding, val):
    if ktree is None:
        print("Starting up")
        return (None, KAryTree(val), False)

    print(ktree.root)
    data, new_top_level = _traverse_insert_level(ktree.root, encoding, val)

    ktree.root = rebalance(None, new_top_level)[3]
    return data, ktree, True




