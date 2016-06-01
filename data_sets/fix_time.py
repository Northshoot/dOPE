# -*- coding: utf-8 -*-
# 
# ██╗  ██╗ █████╗ ██████╗ ███╗   ███╗ ██████╗ ███╗   ██╗██╗   ██╗ █████╗ ██╗
# ██║  ██║██╔══██╗██╔══██╗████╗ ████║██╔═══██╗████╗  ██║╚██╗ ██╔╝██╔══██╗██#║
# ███████║███████║██████╔╝██╔████╔██║██║   ██║██╔██╗ ██║ ╚████╔╝ ███████║██║
# ██╔══██║██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██║╚██╗██║  ╚██╔╝  ██╔══██║██║
# ██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║ ╚████║   ██║██╗██║  ██║██║
# ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝╚═╝╚═╝  ╚═╝╚═╝
#                                                                         
# Copyright (C) 2016 Laurynas Riliskis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created on 5/6/16.
def fix_time():
    # Return list
    filename = 'CRNS0101-05-2015-CA_Santa_Barbara_11_W.csv'
    cnt = ''
    # Read from file
    with open(filename, 'r') as f:
        for line in f:
            #merge 1+2 add 8
            w = line.split()
            new_line = w[1] + ' ' + w[2][:2]+':' + w[2][2:]
            cnt += new_line + '\t' + w[8] + '\t' + w[12] + '\t' + w[15] + '\n'
    f = open('2015_Santa_Barbara_clean.txt','w')
    f.write(cnt)
    f.close()

def get_vals(data):
    from datetime import datetime
    outofrange = 0
    dates = []
    temp = []
    for row in data:
        w = row.split()
        if len(w) > 1:
            if -100 < float(w[8]) < 100:
                t = w[1] + ' ' + w[2][:2] + ':' + w[2][2:]
                dates.append(datetime.strptime(t, "%Y%m%d %H:%M"))
                temp.append(w[8])
            else:
                outofrange += 1
                print("Out of range: " + str(outofrange) + " row: " + row)
    return dates, temp
def plot():
    import numpy as np
    import matplotlib.pyplot as plt


    with open('CRNS0101-05-2015-CA_Santa_Barbara_11_W.txt') as f:
        data = f.read()
    with open('CRNS0101-05-2015-MO_Chillicothe_22_ENE.txt') as f2:
        data2 = f2.read().split('\n')
    data = data.split('\n')
    dates, temp = get_vals(data)
    dates_2, temp_2 = get_vals(data2)

    x = np.array(dates)
    y = np.array(temp)
    y_2 = np.array(temp_2)
    x_2 = np.array(dates_2)
    fig = plt.figure()

    ax1 = fig.add_subplot(111)

    ax1.set_title("Temperature")
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Temperatures')

    ax1.plot(x, y, c='r', label='Santa Barbara')
    ax1.plot(x_2, y_2, c='b', label='Chillicothe')

    leg = ax1.legend()
    plt.show()
if __name__ == "__main__":
    plot()
