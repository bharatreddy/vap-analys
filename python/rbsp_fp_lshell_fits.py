if __name__ == "__main__":
    import rbsp_fp_lshell_fits
    import datetime
    inpLosVelFile = \
        "../data/frmtd-saps-vels-20130316.txt"
    inpSAPSDataFile = \
        "../data/processedSaps-rbsp.txt"
    rbspSatAFile = "../data/rbsp_iono_satA.txt"
    rbspSatBFile = "../data/rbsp_iono_satB.txt"
    rblsObj = rbsp_fp_lshell_fits.LshellRbsp(inpLosVelFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=inpSAPSDataFile, applyPOESBnd=False)
    inpDt = datetime.datetime( 2013, 3, 16, 9, 40 )
    resDF = rblsObj.get_fp_fit_vel(inpDt)


class LshellRbsp(object):
    """
    A class to obtain SAPS velocities using 
    an optimized Lshell fitting method
    """
    def __init__(self, losdataFile, inpSAPSDataFile=None, applyPOESBnd=False):
        import pandas
        # get raw Los data from the input file and store it in a DF
        inpColNames = [ "dateStr", "timeStr", "beam", "range", \
          "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
          "radCode"]
        self.losSDVelDF = pandas.read_csv(losdataFile, sep=' ',\
                                     header=None, names=inpColNames)
        self.losSDVelDF["date"] = self.losSDVelDF.apply( \
                                    self.convert_to_datetime, axis=1 )
        # for some reason MLAT is a str type, convert it to float
        self.losSDVelDF["MLAT"] = self.losSDVelDF["MLAT"].astype(float)
        # Also get a normMLT for plotting & analysis
        self.losSDVelDF['normMLT'] = [x-24 if x >= 12\
             else x for x in self.losSDVelDF['MLT']]
        # We'll also need SAPS data file to determine
        # which velocities are below the auroral oval
        # This file location could be set to None if
        # all the velocities present in the velocity 
        # file are below the auroral oval!
        if inpSAPSDataFile is None:
            print "saps data file is set to None!"
            print "Assuming all vels are below auroral oval!!"
        self.inpSAPSDataFile = inpSAPSDataFile
        if applyPOESBnd:
            print "Not applying POES boundary." 
            print "Assuming all vels are below auroral oval!!"
        self.applyPOESBnd = applyPOESBnd
        # READ RBSP SAT A DATA
        rbspDataColList = [ "dateStr", "timeStr", "MLatNth", "MLonNth",\
                              "MLTNth", "MLatSth", "MLonSth", "MLTSth", "sat" ]
        self.rbspSatADF = pandas.read_csv("../data/rbsp_iono_satA.txt", \
                             delim_whitespace=True, header=None)
        self.rbspSatADF.columns = rbspDataColList
        self.rbspSatADF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth",\
         "MLonSth", "MLTSth"] ] = self.rbspSatADF[ ["MLatNth", "MLonNth",\
                 "MLTNth", "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
        self.rbspSatADF["date"] = self.rbspSatADF.apply( \
            rbsp_to_datetime, axis=1 )
        self.rbspSatADF["hour"] = [ x.strftime("%H") for x\
                     in self.rbspSatADF["date"] ]
        # READ RBSP SAT B DATA
        self.rbspSatBDF = pandas.read_csv("../data/rbsp_iono_satB.txt", \
                             delim_whitespace=True, header=None)
        self.rbspSatBDF.columns = rbspDataColList
        self.rbspSatBDF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth",\
         "MLonSth", "MLTSth"] ] = self.rbspSatBDF[ ["MLatNth", "MLonNth",\
                 "MLTNth", "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
        self.rbspSatBDF["date"] = self.rbspSatBDF.apply(\
             rbsp_to_datetime, axis=1 )
        self.rbspSatBDF["hour"] = [ x.strftime("%H") for x\
                     in self.rbspSatBDF["date"] ]



    def convert_to_datetime(self,row):
        """ 
        Given a datestr and a time string for 
        losVel DF convert to a python datetime obj.
        """
        import datetime
        datecolName="dateStr"
        timeColName="timeStr"
        currDateStr = str( int( row[datecolName] ) )
    #     return currDateStr
        if row[timeColName] < 10:
            currTimeStr = "000" + str( int( row[timeColName] ) )
        elif row[timeColName] < 100:
            currTimeStr = "00" + str( int( row[timeColName] ) )
        elif row[timeColName] < 1000:
            currTimeStr = "0" + str( int( row[timeColName] ) )
        else:
            currTimeStr = str( int( row[timeColName] ) )
        return datetime.datetime.strptime( currDateStr\
                        + ":" + currTimeStr, "%Y%m%d:%H%M" )


    def rbsp_to_datetime(row, datecolName="dateStr", timeColName="timeStr"):
        """ 
        Given a datestr and a time string for 
        rbsp DF convert to a python datetime obj.
        """
        currDateStr = str( int( row[datecolName] ) )
    #     return currDateStr
        if row[timeColName] < 10:
            currTimeStr = "000" + str( int( row[timeColName] ) )
        elif row[timeColName] < 100:
            currTimeStr = "00" + str( int( row[timeColName] ) )
        elif row[timeColName] < 1000:
            currTimeStr = "0" + str( int( row[timeColName] ) )
        else:
            currTimeStr = str( int( row[timeColName] ) )
        return datetime.datetime.strptime( currDateStr\
                        + ":" + currTimeStr, "%Y%m%d:%H%M" )
