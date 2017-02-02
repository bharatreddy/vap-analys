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
    def __init__(self, losdataFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=None, applyPOESBnd=False):
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
        self.rbspSatADF = pandas.read_csv(rbspSatAFile, \
                             delim_whitespace=True, header=None)
        self.rbspSatADF.columns = rbspDataColList
        self.rbspSatADF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth",\
         "MLonSth", "MLTSth"] ] = self.rbspSatADF[ ["MLatNth", "MLonNth",\
                 "MLTNth", "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
        self.rbspSatADF["date"] = self.rbspSatADF.apply( \
            self.convert_to_datetime, axis=1 )
        self.rbspSatADF["hour"] = [ x.strftime("%H") for x\
                     in self.rbspSatADF["date"] ]
        # READ RBSP SAT B DATA
        self.rbspSatBDF = pandas.read_csv(rbspSatBFile, \
                             delim_whitespace=True, header=None)
        self.rbspSatBDF.columns = rbspDataColList
        self.rbspSatBDF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth",\
         "MLonSth", "MLTSth"] ] = self.rbspSatBDF[ ["MLatNth", "MLonNth",\
                 "MLTNth", "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
        self.rbspSatBDF["date"] = self.rbspSatBDF.apply(\
             self.convert_to_datetime, axis=1 )
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


    def rbsp_to_datetime(self, row, datecolName="dateStr",\
             timeColName="timeStr"):
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


    def get_fp_fit_vel(self, inpDateTime, southFps=False,\
         filterLat=0.5, filterMLT=0.5):
        """
        Given an input datetime get lshell fit results
        at the footprints of satellites! 
        We can either work with Northern Hemi FPs 
        or Southern hemi FPs (not both at once!).
        The filterLat and filterMLT measurements are supposed 
        to identify the latitude and mlt close to the spacecraft.
        These will be used in L-shell fit
        """
        import pandas
        # Filter rbsp velocities by time and hemisphere
        currSatADF = self.rbspSatADF[ self.rbspSatADF["date"]\
                            == inpDateTime ].reset_index(drop=True)
        currSatBDF = self.rbspSatBDF[ self.rbspSatBDF["date"]\
                            == inpDateTime ].reset_index(drop=True)
        if not southFps:
            currSatADF = currSatADF[ ["dateStr", "timeStr",\
                     "date", "MLatNth", "MLonNth", "MLTNth", "sat", "hour"] ]
            currSatBDF = currSatBDF[ ["dateStr", "timeStr",\
                     "date", "MLatNth", "MLonNth", "MLTNth", "sat", "hour"] ]
        else:
            currSatADF = currSatADF[ ["dateStr", "timeStr",\
                     "date", "MLatSth", "MLonSth", "MLTSth", "sat", "hour"] ]
            currSatBDF = currSatBDF[ ["dateStr", "timeStr",\
                     "date", "MLatSth", "MLonSth", "MLTSth", "sat", "hour"] ]
        # Now filter losvelDF for the given time
        currLosDF = self.losSDVelDF[ self.losSDVelDF["date"]\
                            == inpDateTime ].reset_index(drop=True)
        # Now merge the DFs
        currSatADF = pandas.merge( currSatADF, currLosDF, on=["date"] )
        currSatBDF = pandas.merge( currSatBDF, currLosDF, on=["date"] )

        if not southFps:
            hemiChosen = "Nth"
        else:
            hemiChosen = "Sth"
        # SAT A
        currSatADF["del_mlat"] = abs(currSatADF["MLat" + hemiChosen]\
             - currSatADF["vlosMLAT"])
        currSatADF["del_mlt"] = abs(currSatADF["MLT" + hemiChosen]\
             - currSatADF["vlosMLT"])
        # Drop values which are far away from RBSP FPs
        currSatADF = currSatADF[ ( currSatADF["del_mlat"] < latDiff ) &\
                        ( currSatADF["del_mlt"] < mltDiff ) ].\
                        reset_index(drop=True)
        # SAT B
        currSatBDF["del_mlat"] = abs(currSatBDF["MLat" + hemiChosen]\
             - currSatBDF["vlosMLAT"])
        currSatBDF["del_mlt"] = abs(currSatBDF["MLT" + hemiChosen]\
             - currSatBDF["vlosMLT"])
        # Drop values which are far away from RBSP FPs
        currSatBDF = currSatBDF[ ( currSatBDF["del_mlat"] < latDiff ) &\
                        ( currSatBDF["del_mlt"] < mltDiff ) ].\
                        reset_index(drop=True)

        print currSatADF[ abs(currSatADF["Vlos"]) > 100. ]
        print "-----------------------------------------------------------"
        print currSatBDF[ abs(currSatBDF["Vlos"]) > 100. ]