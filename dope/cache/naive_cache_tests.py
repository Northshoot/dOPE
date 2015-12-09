import CacheModelNaive

def main():
  cache = CacheModelNaive.CacheModel(100)
  cache.insert(5)
  print(str(cache))
  cache.insert(2)
  print(str(cache))
  cache.insert(7)
  print(str(cache))


if __name__ == '__main__':
  main()