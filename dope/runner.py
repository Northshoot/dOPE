__author__ = 'lauril'


def run():
    # initialize sink
    from .tiers.DataGenerator import DataGenerator as DG
    sink_random = DG('random')
    from .cache import CacheModel as CM
    node_cache = CM()
    gateway_cache = CM()
    from .datastruct import DataStructureModel as DSM
    data_struct = DSM()
    from .comm import CommunicationModel as comm
    communication = comm



if __name__ == "__main__":
    #sys.path.insert(1,'')
    sys.exit(run())
