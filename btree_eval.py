import matplotlib.pyplot as plt
import numpy as np

def label_tops(rects, labels, offsets):
    vals = zip(rects, labels, offsets)
    for rect, label, offset in vals:
        plt.text(rect.get_x() + rect.get_width()/2, offset + rect.get_height() + 100, 
                 "%d%%"%(int(label*100)), horizontalalignment='center', fontsize=12)
        # plt.text(rect.get_x() + rect.get_width()/2, offset + rect.get_height() + 100, 
        #          "%d"%label, horizontalalignment='center', fontsize=12)

def label_rects(rects, labels, offsets):
    vals = zip(rects, labels, offsets)
    for rect, label, offset in vals:
        height = rect.get_height()/2 + offset
        plt.text(rect.get_x() + rect.get_width()/2., height, "%d"%label, horizontalalignment='center', fontsize=12)



def main(mOPE_rand, mOPE_seq, mOPE_NOAA, dOPE_rand, dOPE_seq, dOPE_NOAA):
    plt.figure(0, figsize=(10,6.2))
    #ind = [1,2,3,4,7,8,9,10,13,14,15,16]
    ind = [4, 8, 12]
    width = 0.7
    mOPE = mOPE_rand + mOPE_seq + mOPE_NOAA
    dOPE = dOPE_rand + dOPE_seq + dOPE_NOAA
    percentGain = [ float(m - d) /float(m)  for (m,d) in zip(mOPE, dOPE)]
    pmope = plt.bar(ind, mOPE, width, color="#FFFFFF", label='mOPE', align='center')
    pdope = plt.bar(ind, dOPE, width, color="#D1D1D1", label = 'dOPE', align='center')

    # Add labels
    plt.ylabel("Messages From Embedded Device")
    # xtick_strings = ['k=4', 'k=6', 'k=8', 'k=10'] * 3 + ['\nRandom', '\nSequential', '\nNOAA Temp']
    # xtick_ind = ind + [2.5, 8.5, 14.5]
    xtick_ind = ind
    xtick_strings = ['\nRandom', '\nSequential', '\nNOAA Temp']
    plt.xticks(xtick_ind, xtick_strings)


    #label_rects(pmope, mOPE, [0 for i in range(len(mOPE))])
    #label_tops(pdope, dOPE, mOPE)
    label_tops(pmope, percentGain, [0]*len(pmope))

    # Add limits
    maxbarh = mOPE_seq[0] + dOPE_seq[0]
    plt.ylim([0, maxbarh + maxbarh/4.])

    plt.legend(loc='upper center', ncol=3, frameon=False, fontsize=12, 
               columnspacing=4, handleheight=3)
    plt.title('Simulated Performace of 3-tiered mOPE and dOPE \n 1 million inserts |Scache|=500, |Gcache|=1000')
    plt.savefig('dm_btree_sim.pdf', bbox_inches='tight', format='pdf')
    plt.show()

if __name__ == '__main__':
    # mOPE_rand = [5585, 3887, 3307, 2999]
    # mOPE_seq = [10451, 6926, 5723, 4981]
    # mOPE_NOAA = [6135, 3846, 3587, 2956]
    # dOPE_rand = [5745, 3619, 2847, 2429]
    # dOPE_seq = [5468, 3082, 2326, 1936]
    # dOPE_NOAA = [888, 511, 390, 327]
    mOPE_rand = [2823899 ]
    mOPE_seq = [8323402]
    mOPE_NOAA = [2796171]
    dOPE_rand = [1529403 ]
    dOPE_seq = [2804657]
    dOPE_NOAA = [1001543 ]




    main(mOPE_rand, mOPE_seq, mOPE_NOAA, dOPE_rand, dOPE_seq, dOPE_NOAA)
