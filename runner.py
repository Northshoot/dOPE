__author__ = 'lauril, wDaviau'

import sys, os, argparse
import logging
import pstats
import profile
from dope import dOPE_B as dOPE
console = logging.StreamHandler()
console.setLevel(logging.CRITICAL)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def run(numTics, dataTics, networkTics, data_queue_len, distribution,
        cacheS_len, cacheG_len,data_file, num_data, verbose):
    # import here because we need to set up syspath prior importing
    from dope import mOPE_baseline
    #
    # # Run basline simulation
    k = 10 # Talos value for k-ary tree branching
    mOPE_baseline(numTics, dataTics, networkTics, data_queue_len, k,
                  distribution, data_file, num_data)

    from dope import dOPE_B as dOPE
    #from dope import dOPE_full as dOPE# To run with scapegoat tree

    # Run the current dOPE simulation 
    profile.runctx('print(dOPE(numTics, dataTics, networkTics, data_queue_len, cacheS_len, cacheG_len, distribution, k, data_file, num_data, not verbose))',
                None, locals(), "profile_stats.stats")
    stats = pstats.Stats("profile_stats.stats")
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats()


    

# def get_plot_data(numTics, dataTics, networkTics, data_queue_len, distribution):
#     # import here because we need to set up syspath prior importing
#     from mope.mope import mOPE_baseline

#     mOPE_baseline(numTics, dataTics, networkTics, data_queue_len, distribution)
    
    
if __name__ == "__main__":
    sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
    ## This is the format of command line flags and arguments ##
    ## -tics x : for a simulation of x tics
    ## -dtics x : for new data arriving every x tics
    ## -ntics x : for network transfer of messages every x tics
    ## -qlen l : for data queue of length l
    ## -dist 'd' : for a data arrival model following distribution d
    ##  choices for d are currently random, uniform, increasing, NOAA_temp
    # python3 runner.py -dist increasing
    # python3 runner.py -dist NOAA_temp
    parser = argparse.ArgumentParser(description= 'Naive dope simulation.')
    parser.add_argument("-tics", "--numTics", type=int, 
                        help= "Set the number of tics in the simulation")
    parser.add_argument("-dtics", "--dataTics", type=int, 
                        help= "Set the number of tics it takes for new data " +
                        "to arrive from the sensor")
    parser.add_argument("-ntics", "--networkTics", type=int, 
                        help= "Set the number of tics it takes for the " +
                        "network to send a message round trip")
    parser.add_argument("-qlen", "--data_queue_len", type=int, 
                        help= "Set the sensor's data queue length")
    parser.add_argument("-dist", "--distribution", 
                        help= "Set the data model of the simulation")
    parser.add_argument("-cacheSL", "--sensorcacheLength", type=int, 
                        help= "Set the cache length of the dOPE sensor")
    parser.add_argument("-cacheGL", "--gatewaycacheLength", type=int, 
                        help = "Set the cache length of the dOPE gateway")
    parser.add_argument("-f", "--file", type=str,
                        help="File with NOAA data")
    parser.add_argument("-dn", "--data_number", type=int)
    parser.add_argument("-v", action='store_true')
    args = parser.parse_args()

    # Set default values of arguments not taken from the command line
    numTics = args.numTics
    if numTics is None:
        numTics = 100000000

    dataTics = args.dataTics
    if dataTics is None:
         dataTics = 1

    networkTics = args.networkTics
    if networkTics is None:
        networkTics = 1

    data_queue_len = args.data_queue_len
    if data_queue_len is None:
        data_queue_len = 10000000

    data_file = None
    distribution = args.distribution
    if distribution is None:
        distribution = 'increasing'
    
    if distribution == 'NOAA_temp':
        data_file = args.file
        if data_file is None:
           # data_file = 'data_sets/CRNS0101-05-2015-CA_Santa_Barbara_11_W.txt'
            data_file = "data_sets/CRNS0101-05-2015-MO_Chillicothe_22_ENE.txt"
            #data_file = 'data_sets/CRNS0101-05-2008-KY_Bowling_Green_21_NNE
            # .txt'

    cacheLengthS = args.sensorcacheLength
    if cacheLengthS is None:
        cacheLengthS = 500

    cacheLengthG = args.gatewaycacheLength
    if cacheLengthG is None:
        cacheLengthG = 10000000

    data_number = args.data_number
    if data_number is None:
        data_number = 100000

    sys.exit(run(numTics, dataTics, networkTics, data_queue_len, distribution,
                 cacheLengthS, cacheLengthG, data_file, data_number, args.v))
