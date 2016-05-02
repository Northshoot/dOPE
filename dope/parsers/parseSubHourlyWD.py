# Parse NOAA subhourly data file.  The Different column numbers are referenced
# below:
# Field#  Name                           Units
# ---------------------------------------------
#    1    WBANNO                         XXXXX
#    2    UTC_DATE                       YYYYMMDD
#    3    UTC_TIME                       HHmm
#    4    LST_DATE                       YYYYMMDD
#    5    LST_TIME                       HHmm
#    6    CRX_VN                         XXXXXX
#    7    LONGITUDE                      Decimal_degrees
#    8    LATITUDE                       Decimal_degrees
#    9    AIR_TEMPERATURE                Celsius
#    10   PRECIPITATION                  mm
#    11   SOLAR_RADIATION                W/m^2
#    12   SR_FLAG                        X
#    13   SURFACE_TEMPERATURE            Celsius
#    14   ST_TYPE                        X
#    15   ST_FLAG                        X
#    16   RELATIVE_HUMIDITY              %
#    17   RH_FLAG                        X
#    18   SOIL_MOISTURE_5                m^3/m^3
#    19   SOIL_TEMPERATURE_5             Celsius
#    20   WETNESS                        Ohms
#    21   WET_FLAG                       X
#    22   WIND_1_5                       m/s
#    23   WIND_FLAG                      X
#  ftp://ftp.ncdc.noaa.gov/pub/data/uscrn/products/subhourly01/

def parseNOAAFile(filename, columnNumber):
   # Return list
   data_values = []
   # Read from file
   with open(filename, 'r') as f:
      for line in f:
         words = line.split()
         data_val =  round(float(words[columnNumber -1]) , 1)
         data_values.append(data_val)

   return data_values

def parseNOAAFile2File(filein, fileout, columnNumber):
    data_values = parseNOAAFile(filein, columnNumber)
    min_val = min(data_values) * 10
    with open(fileout, 'w') as f:
        for dataval in data_values:
            newdv = (10 * dataval) + min_val
            f.write("%s,\n" % dataval)


