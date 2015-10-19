__author__ = 'lauril'

import sys, os


def run():
    # import here because we need to set up syspath prior importing
    from mope.mope import mOPE_baseline
    # Number of simulation steps
    nSIMSTEPS = 100
    # Run basline simulation
    mOPE_baseline(nSIMSTEPS)
    
if __name__ == "__main__":
    sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
    sys.exit(run())
