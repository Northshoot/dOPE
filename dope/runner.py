__author__ = 'lauril'
from mope import mOPE_baseline

def run():
    # Number of simulation steps
    nSIMSTEPS = 100
    # Run basline simulation
    mOPE_baseline(nSIMSTEPS)


    
if __name__ == "__main__":
    #sys.path.insert(1,'')
    sys.exit(run())
