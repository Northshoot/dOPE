import matplotlib.pyplot as plt 
import csv

def main():
  
  # Make a square figure and axes
  plt.rc('font', family='serif')
  plt.rc('legend', fontsize=6)


  # Inserts per round trip bar graph
  plt.figure(0, figsize=(7,6))
  ind = [1,2,3, 5,6,7, 9,10,11]
  mid_ind = [x + 0.4 for x in ind]
  #            1000               10000                    100000
  # NOAA   Random   Increase   NOAA  Random Increase    NOAA Random Increase
  rts_m = [ 5.2, 6.1, 6.9, 6.9, 6.8, 9.7, 7.8, 6.8, 12.6]
  rts_m = [ 5.2, 6.9, 7.8, 6.1, 6.8, 6.8, 6.9, 9.7, 12.6]
  rts_d = [ 2.6, 2.5, 4.4, 1.5, 1.9, 9.7, 1.3, 1.9, 9.52]
  rts_d = [ 2.6, 1.5, 1.3, 2.5, 1.9, 1.9, 4.4, 9.7, 9.5]
  p1 = plt.bar(ind, rts_m, width=0.4, color="#bfbfbf")
  p2 = plt.bar(mid_ind, rts_d, width=0.4, color="#333333")
  plt.ylim([0,16])
  plt.text(1.5, 13.5, "NOAA")
  plt.text(5.5, 13.5, "Random")
  plt.text(9.5, 13.5, "Sequential")
  for x,y,z in zip(mid_ind, rts_m, rts_d):
      d = dict(fontsize=8)
      plt.text(x-0.22,y+0.2,str(round(y/z,1))+"X", **d)
  plt.xticks(mid_ind, 3*("1,000", "10,000", "100,000"), 
                         rotation="vertical")
  plt.xlabel("Simulated Round Trips")
  plt.title("Inserts Per Round Trip mOPE vs dOPE\n100 Entry Cache Size")
  plt.ylabel("Average Round Trips per Insert")
  plt.legend((p1[0], p2[0]), ('mOPE', 'dOPE'))
  plt.savefig('InsertsRTs.png', bbox_inches='tight', dpi = 1200)

  # Round trips
  with open('Round_trips_mope.csv') as f:
    reader = csv.reader(f)
    rts = list(reader)

  with open('Round_trips_dope.csv') as df:
    readerd = csv.reader(df)
    rtds = list(readerd)

  plt.figure(1, figsize=(7,6))
  xs = [x for x in range(len(rts))]
  xds = [x for x in range(len(rtds))]
  ys = [y for y in rts]
  yds = [y for y in rtds]
  plt.plot(xs, ys, marker = 'o', color = "#007fff")
  plt.plot(xds, yds, marker = 'o', color = "#ff1a1a")
  plt.ylim([-1,20])
  plt.title("Round Trip Cost of Inserts Over Time", y = 1.05)
  plt.xlabel("Insert Number")
  plt.ylabel("Round Trips For Insert")
  plt.xticks(fontsize = 10)
  plt.yticks(fontsize = 10)
  plt.savefig('RoundTrips.png', bbox_inches='tight', dpi = 1200)

  # Queue Size
  with open('Min_Queue_Avoiding_Drops.csv') as f:
    MQreader = csv.reader(f)
    rate_and_minQs = list(MQreader)

  plt.figure(2, figsize=(7,6))
  # Unmarshal csv tuple list into three lists
  InToOutRatio = []
  RandomData = []
  NOAA_Temp = []
  Increasing = []
  for (a,b,c,d) in rate_and_minQs:
    InToOutRatio.append(a)
    RandomData.append(b)
    NOAA_Temp.append(c)
    Increasing.append(d)

  map(float, InToOutRatio)
  map(float, RandomData)
  map(float, NOAA_Temp)
  map(float, Increasing)
  ax = plt.subplot(111)
  ax.scatter(InToOutRatio, Increasing, marker = '*', c = 'g', label = 'Increasing Integers', s = 15.0)
  ax.scatter(InToOutRatio, NOAA_Temp, marker = 'd', c= 'r', label = "NOAA Hourly Temperatures", s = 15.0)
  ax.scatter(InToOutRatio, RandomData, marker = '+', c= 'b', label = 'Random Integers', s = 15.0)
  plt.ylim([0, 1100])
  plt.xlim([0, 10])
  plt.title("Queue Size Preventing Drops Sending 1000 Packets", y = 1.05)
  plt.xlabel("Arrival Rate / Sending Rate")
  plt.ylabel("Minimum Queue Length to Prevent Drops")
  plt.xticks(fontsize = 10)
  plt.yticks(fontsize = 10)
  plt.legend(loc = 'lower right')
  plt.savefig("Min_Queue.png", bbox_inches='tight', dpi = 1200)


  # Queue min comparison
  plt.figure(3, figsize=(7,6))

  with open('dOPE_min_Q_lens.csv') as dQ:
    dQreader = csv.reader(dQ)
    min_Qsd = list(dQreader)
  NOAAd = []
  Increasingd = []
  for (a,b,c) in min_Qsd:
    NOAAd.append(a)
    Increasingd.append(b)

  map(float, NOAAd)
  map(float, Increasingd)
  ax = plt.subplot(111)
  InToOutRatiod = [0.143, 0.167, 0.2, 0.25, 0.33, 0.5, 1, 2, 3, 4, 5, 6, 7]
  ax.scatter(InToOutRatio, NOAA_Temp, marker = 'd', c= 'r', label = "NOAA Hourly Temp mOPE", s = 15.0)
  ax.scatter(InToOutRatiod, NOAAd, marker = 'd', c= 'b', label = "NOAA Hourly Temp dOPE", s = 15.0 )
  plt.ylim([0, 1100])
  plt.xlim([0, 10])
  plt.title("Queue Size Preventing Drops Sending 1000 Packets. dOPE vs mOPE", y = 1.05)
  plt.xlabel("Arrival Rate / Sending Rate")
  plt.ylabel("Minimum Queue Length to Prevent Drops")
  plt.yticks(fontsize = 10)
  plt.legend(loc = 'lower right')
  plt.savefig("Min_Queue_mOPE_dOPE.png", bbox_inches='tight', dpi = 1200)

  # Queue Drops
  with open("Drops_For_Q_size.csv") as f:
    MQAreader = csv.reader(f)
    qsize_and_drops = list(MQAreader)

    plt.figure(4, figsize=(7,6))
    qsize = []
    unity = []
    double = []
    half = []
    for (a,b,c,d) in qsize_and_drops:
      qsize.append(a)
      unity.append(b)
      double.append(c)
      half.append(d)

    map(float, qsize)
    map(float, unity)
    map(float, double)
    map(float, half)
    ax = plt.subplot(111)
    ax.scatter(qsize, unity, c = 'g', s = 15.0, marker = '+', label = "Arrival Rate / Departure Rate = 1")
    ax.scatter(qsize, double, c = 'b', s = 15.0, marker = '+', label = "Arrival Rate / Departure Rate = 2")
    ax.scatter(qsize, half, c = 'y', s = 15.0, marker = '+', label = "Arrival Rate / Departure Rate = 0.5")
    plt.title("Drops by Queue Size NOAA Hourly Temperature Dataset", y = 1.05)
    plt.xlabel("Queue Size (Packets)")
    plt.ylabel("Drops per 1000 Arrivals")
    plt.xticks(fontsize = 10)
    plt.yticks(fontsize = 10)
    plt.xlim([0,1100]) 
    plt.ylim([0,950])
    plt.legend()
    plt.savefig("Avoiding_Drops.png", bbox_inches='tight', dpi = 1200)




if __name__ == '__main__':
  main()