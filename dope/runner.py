__author__ = 'lauril'

import sys, os


def run():
    # import here because we need to set up syspath prior importing
    from mope.mope import mOPE_baseline
    # Number of simulation steps
    numINSERTSMAX = 1000
    # Run basline simulation
    out_data = mOPE_baseline(numINSERTSMAX)
    out_file = open('output_trial','w')
    for item in out_data:
      out_file.write("%s,\n" % item)
    out_file.close
    
if __name__ == "__main__":
    sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
    sys.exit(run())
