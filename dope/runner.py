__author__ = 'lauril, wDaviau'

import sys, os, argparse


def run(numTics, dataTics, networkTics, data_queue_len, distribution):
    # import here because we need to set up syspath prior importing
    from mope.mope import mOPE_baseline
    
    # Run basline simulation
    mOPE_baseline(numTics, dataTics, networkTics, data_queue_len, distribution)


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
    parser = argparse.ArgumentParser(description= 'Naive dope simulation.')
    parser.add_argument("-tics", "--numTics", type=int, help= "Set the number of tics in the simulation")
    parser.add_argument("-dtics", "--dataTics", type=int, help= "Set the number of tics it takes for new data to arrive from the sensor")
    parser.add_argument("-ntics", "--networkTics", type=int, help= "Set the number of tics it takes for the network to send a message round trip")
    parser.add_argument("-qlen", "--data_queue_len", type=int, help= "Set the sensor's data queue length")
    parser.add_argument("-dist", "--distribution", help= "Set the data model of the simulation")
    args = parser.parse_args();

    # Set default values of arguments not taken from the command line
    numTics = args.numTics
    dataTics = args.dataTics
    networkTics = args.networkTics
    data_queue_len = args.data_queue_len
    distribution = args.distribution
    if (numTics is None):
      numTics = 1000
    if (dataTics is None):
      dataTics = 1
    if (networkTics is None):
      networkTics = 1
    if (data_queue_len is None):
      data_queue_len = 50
    if (distribution is None):
      distribution = 'random'

    sys.exit(run(numTics, dataTics, networkTics, data_queue_len, distribution))
