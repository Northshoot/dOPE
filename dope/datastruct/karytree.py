
class KAryLevel:
    def __init__(self):
        self.isLeaf = True
        self.size = 0
        self.rootNode = None

class KAryNode:
    def __init__(self,val,right_of_root):
        self.right_of_root = right_of_root
        self.data = val
        self.left = None
        self.right = None
        self.left_level = None
        self.right_level = None


class KAryTree:
    def __init__(self, val):
        self.root = KAryLevel
        self.root.rootNode = KAryNode(val, False)
        self.root.size = 1


#def rebalance


# ( Data to compare, new node, data added to this level, level added)
def _traverse_insert_node(node, encoding, val, right_of_root, is_leaf):
    if encoding == []:
        if node is None:
            # Add node
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
                (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.right, encoding[1:], val, right_of_root, is_leaf)
                node.right = new_node
                return (out_data, node, data_added, level_added)

            # Left of root go down right child level
            if not right_of_root:
                (out_data, new_level) = _traverse_insert_level(node.right_level, encoding[1:], val)
                node.right_level = new_level
                return (out_data, node, False, True)



# (Data to compare, new level)
def _traverse_insert_level(level, encoding, val):
    
    if encoding == []:
        if level is None:
            level = KAryLevel()
            level.rootNode = KAryNode(val)
            level.size += 1
            return (None, level)

        node = level.rootNode

        if val == node.data
            # Found the value
            return (None, KAryNode(val, False))
        else:
            # Need to decrypt data at this node to continue traversal
            return (node.data, node)

    else:
        if level is None:
            raise ValueError("Encoding points beyond tree")
            #Traverse the next level 
        # Search to the left
        node = level.rootNode
        if encoding[0]==0:
            # Case where root is left end
            if node.left is None and not level.isLeaf:
                (out_data, new_level) = _traverse_insert_level(node.left_level, encoding[1:], val)
                node.left_level = new_level
                level.isLeaf = False
                return (out_data, level)
            (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.left, encoding[1:], val, False, level.isLeaf)
            node.left = new_node
            if level_added:
                level.isLeaf = False
            if data_added:
                level.size += 1
            return (out_data, level)

        # Search to the right
        else: 
            # Case where root is right end
            if node.right is None and not level.isLeaf:
                (out_data, new_level) = _traverse_insert_level(node.right_level, encoding[1:], val)
                node.right_level = new_level
                level.isLeaf = False
                return (out_data, level)
            (out_data, new_node, data_added, level_added) = _traverse_insert_node(node.right, encoding[1:], val, True, level.isLeaf)
            node.right = new_node
            if level_added:
                level.isLeaf = False
            if data_added:
                level.size += 1
            return (out_data, level)




def traverse_insert(ktree, encoding, val):
    if ktree is None:
        return (None, KAryTree(val), False)

    data, new_top_level = _traverse_insert_level(ktree.toplevel, encoding, val)
    ktree.root = new_top_level
    return data, ktree, True




