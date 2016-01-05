import cache.CacheModelNaive
from  datastruct.scapegoat_tree import SGTree, normal_insert 

# For use comparing tree to verify rebalancing
# As long as we go level by level we should be ok
# The order should be preserved in the cache list
# So not too much work
def convert_cache_to_tree(cache):
  sgtree = SGTree(cache[0])
  for elt in cache[1:]:
    sgtree = normal_insert(sgtree.root, elt.cipher_text, sgtree)

  return sgtree


def main():
  cache = CacheModel(100)
  print("inserting 5")
  cache.insert(5)
  print(str(cache))
  print("inserting 2")
  cache.insert(2)
  print(str(cache))
  print("inserting 7")
  cache.insert(7)
  print(str(cache))

  sgtree = SGTree(80)
  sgtree = normal_insert(sgtree.root, 15, sgtree)
  sgtree = normal_insert(sgtree.root, 15, sgtree)
  sgtree = normal_insert(sgtree.root, 65, sgtree)
  sgtree = normal_insert(sgtree.root, 25, sgtree)
  print(sgtree)
  sgtree = normal_insert(sgtree.root, 30, sgtree)
  sgtree = normal_insert(sgtree.root, 40, sgtree)
  print(sgtree)
  sgtree = normal_insert(sgtree.root, 100, sgtree)
  sgtree = normal_insert(sgtree.root, 101, sgtree)
  print(sgtree)
  sgtree = normal_insert(sgtree.root, 15, sgtree)
  sgtree = normal_insert(sgtree.root, 320, sgtree)
  print(sgtree)


if __name__ == '__main__':
  main()