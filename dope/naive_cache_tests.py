from cache.CacheModelNaive import CacheModel
from  datastruct.scapegoat_tree import SGTree, insert, enc_insert

# For use comparing tree to verify rebalancing
# As long as we go level by level we should be ok
# The order should be preserved in the cache list
# So not too much work
def convert_cache_to_tree(cache):
  # sort cache by encoding length
  cache = sorted(cache, key = lambda x: len(x.encoding))
  sgtree = SGTree(cache[0].cipher_text)
  for elt in cache[1:]:
    enc_insert(sgtree, elt.cipher_text, elt.encoding)

  return sgtree


def main():

  # Test Simple inserts
  cache = CacheModel(100)
  print("inserting 5")
  cache.insert(5)
  print(str(cache))
  print("inserting 2")
  cache.insert(2)
  print(str(cache))
  print("inserting 7")
  #import pdb; pdb.set_trace()
  cache.insert(7)
  print(str(cache))



  # A few more, none to cause rebalance yet
  cache.insert(8)
  cache.insert(6)
  cache.insert(3)
  cache.insert(1)
  print(str(cache))
  sgtree = convert_cache_to_tree(cache.cache)
  print(sgtree)


  cache = CacheModel(100)
  cache.insert(1)
  cache.insert(0)
  cache.insert(2)
  cache.insert(3)
  print(str(cache))
  sgtree = convert_cache_to_tree(cache.cache)
  print(sgtree)


  #import pdb; pdb.set_trace()

  # Test rebalancing
  cache = CacheModel(100)
  for i in range(10):
    cache.insert(i)
    print(str(cache))
    print("=========================================\n")
    sgtree = convert_cache_to_tree(cache.cache)
    print(sgtree)

  print(str(cache))
  sgtree = convert_cache_to_tree(cache.cache)
  print(sgtree)

  # sgtree = SGTree(80)
  # insert(sgtree, 15)
  # print(sgtree)
  # print("\n")
  # insert(sgtree, 15)
  # insert(sgtree, 65)
  # print(sgtree)
  # print("\n")
  # insert(sgtree, 25)
  # print(sgtree)
  # print("\n")
  # insert(sgtree, 30)
  # insert(sgtree, 40)
  # insert(sgtree, 100)
  # print(sgtree)
  # print("\n")
  # insert(sgtree, 101)
  # insert(sgtree, 15)
  # insert(sgtree, 320)
  # print(sgtree)
  # print("\n")

  
if __name__ == '__main__':
  main()