from scapegoat_tree import SGTree, insert

W = SGTree(1)
for i in range(1,800):
  print('inserting' + str(i))
  insert(W,i)
print(W)