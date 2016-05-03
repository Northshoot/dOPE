import karytree
import pdb

testtree = karytree.KAryTree(1)

data, new_top_level = karytree._traverse_insert_level(testtree.root, [], 2)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
print(str(data) + " should be old root 1")

data, new_top_level = karytree._traverse_insert_level(testtree.root, [1], 2)
print("level size: " +str(new_top_level.size))
testtree.root = new_top_level
print(str(data) + " should be none")

# Insert over 10 elements into the first level
#pdb.set_trace()
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1], 3)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))


data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1], 4)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1], 5)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1], 6)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1,1], 7)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1,1,1], 8)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1,1,1,1], 9)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1,1,1,1,1], 10)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))
data, new_top_level = karytree._traverse_insert_level(testtree.root, [1,1,1,1,1,1,1,1,1,1], 11)
testtree.root = new_top_level
print("level size: " +str(new_top_level.size))

testtree.root = karytree.rebalance(None, testtree.root)[3]
pdb.set_trace()

