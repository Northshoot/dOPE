# Parse NOAA weather data file.  The Different column numbers are referenced
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
#    9    T_CALC                         Celsius
#    10   T_HR_AVG                       Celsius
#    11   T_MAX                          Celsius
#    12   T_MIN                          Celsius
#    13   P_CALC                         mm
#    14   SOLARAD                        W/m^2
#    15   SOLARAD_FLAG                   X
#    16   SOLARAD_MAX                    W/m^2
#    17   SOLARAD_MAX_FLAG               X
#    18   SOLARAD_MIN                    W/m^2
#    19   SOLARAD_MIN_FLAG               X
#    20   SUR_TEMP_TYPE                  X
#    21   SUR_TEMP                       Celsius
#    22   SUR_TEMP_FLAG                  X
#    23   SUR_TEMP_MAX                   Celsius
#    24   SUR_TEMP_MAX_FLAG              X
#    25   SUR_TEMP_MIN                   Celsius
#    26   SUR_TEMP_MIN_FLAG              X
#    27   RH_HR_AVG                      %
#    28   RH_HR_AVG_FLAG                 X
#    29   SOIL_MOISTURE_5                m^3/m^3
#    30   SOIL_MOISTURE_10               m^3/m^3
#    31   SOIL_MOISTURE_20               m^3/m^3
#    32   SOIL_MOISTURE_50               m^3/m^3
#    33   SOIL_MOISTURE_100              m^3/m^3
#    34   SOIL_TEMP_5                    Celsius
#    35   SOIL_TEMP_10                   Celsius
#    36   SOIL_TEMP_20                   Celsius
#    37   SOIL_TEMP_50                   Celsius
#    38   SOIL_TEMP_100                  Celsius
#
# parseNOAAFile takes in a filename to a NOAA file and a column
# number to be read and returns a list of all data in that column
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








