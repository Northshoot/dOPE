import matplotlib.pyplot as plt
#import numpy as np

def main(cache_sizes, misses):
    plt.figure(0, figsize=(10,6.2))
    plt.plot(cache_sizes, misses)
    plt.title("Simulated Cache Size Sweep")
    plt.ylabel("Fraction of data causing cache miss")
    plt.xlabel("Size of cache")
    plt.xlim([0, 100])
    plt.ylim([0, 0.5])
    plt.savefig('cache_sweep.pdf', bbox_inches='tight', format='pdf')
    plt.show()


if __name__ == "__main__":
    cache_sizes = [18, 20, 21, 22, 23, 25, 30, 35, 40, 45, 50, 55, 65, 70, 75, 80, 85, 90]
    misses = [ 47246, 27455, 22295, 19397, 17093, 14774, 11961, 10564, 9687, 9040, 8416, 7879, 7007, 6555, 6121, 5738, 5333, 4939 ]
    minus92 = lambda x: x -92
    dividedby100k = lambda x: x / 105119
    adjusted_misses = list(map(dividedby100k, list(map(minus92, misses))))
    print(adjusted_misses)
    main(cache_sizes, adjusted_misses)
    
