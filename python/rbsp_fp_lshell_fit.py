if __name__ == "__main__":
    import rbsp_fp_lshell_fit
    import datetime
    inpLosVelFile = \
        "../data/formatted-vels-20130622.txt"
    inpSAPSDataFile = \
        "../data/processedSaps-rbsp.txt"
    rbspSatAFile = "../data/rbsp_iono_satA.txt"
    rbspSatBFile = "../data/rbsp_iono_satB.txt"
    rblsObj = rbsp_fp_lshell_fit.FittedVels(inpLosVelFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=inpSAPSDataFile, applyPOESBnd=False)
    inpDt = datetime.datetime( 2013, 6, 22, 6, 0 )
    resDF = rblsObj.get_fp_fitted_vel(inpDt)
    # print "FIN---RESULT"
    # print resDF


class FittedVels(object):
    """
    A class to obtain SAPS velocities 
    assuming SAPS are perfectly westwards.
    """
    def __init__(self, losdataFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=None, applyPOESBnd=False):
        import pandas
        # get raw Los data from the input file and store it in a DF
        inpColNames = [ "dateStr", "timeStr", "beam", "range", \
          "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
          "radCode"]
        self.losdataFile = losdataFile
        self.inpSAPSDataFile = inpSAPSDataFile
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


    def get_fitvel_sd_nearest(self, inputDT, inpLosVelFile, inpSAPSDataFile):
        """
        In the current function we'll loop through each and every
        file (representing l-o-s velocities for a given day)
        and get the best lshell fits out of them!!!
        """
        import pandas
        import numpy
        import lshell_events
        # Select only the datetime we are interested in
        rbspSatADF = self.rbspSatADF[ self.rbspSatADF["date"] == inputDT].reset_index()
        rbspSatBDF = self.rbspSatBDF[ self.rbspSatBDF["date"] == inputDT].reset_index()
        # get fit data after inputs from Los file and SAPS file
        # inpSAPSDataFile = None
        lsObj = lshell_events.LshellFit(inpLosVelFile, \
            inpSAPSDataFile=inpSAPSDataFile)
        sdFitresDF = lsObj.get_timewise_lshell_fits(inputDT)
        # Get only the good-fits and identify the location 
        # closest to the rbsp footprint.
        sdFitresDF = sdFitresDF[ sdFitresDF["goodFitCheck"] ].reset_index()
        # set up some variables for later use
        nrstLocSatADF = None
        nrstLocSatBDF = None
        nrstLocDF = None
        # Find the closest MLTs
        if rbspSatADF.shape[0] > 0:
            if ( rbspSatADF["MLTNth"].tolist()[0] >= 12. ):
                satANormMLT = rbspSatADF["MLTNth"].tolist()[0] - 24.
            else:
                satANormMLT = rbspSatADF["MLTNth"].tolist()[0]
            sdFitresDF["delMLATSatA"] = sdFitresDF["MLAT"] -\
                         rbspSatADF["MLatNth"].tolist()[0]
            sdFitresDF["delMLTSatA"] = sdFitresDF["normMLT"] - satANormMLT
            nrstLocSatADF = sdFitresDF[ numpy.abs( sdFitresDF["delMLTSatA"] ) \
                == numpy.min( numpy.abs( sdFitresDF["delMLTSatA"] ) ) ]
            # Get the nearest rows in MLT first and then MLAT
            # We do this because we assume direction remains constant
            # over MLT
            nrstLocSatADF = nrstLocSatADF[ numpy.abs( \
                nrstLocSatADF["delMLATSatA"] ) == numpy.min(\
                 numpy.abs( nrstLocSatADF["delMLATSatA"] ) ) ].reset_index()
            nrstLocSatADF["sat"] = "SatA"
            nrstLocDF = nrstLocSatADF
        # same thing for SAT-B
        if rbspSatBDF.shape[0] > 0:
            if ( rbspSatBDF["MLTNth"].tolist()[0] >= 12. ):
                satBNormMLT = rbspSatBDF["MLTNth"].tolist()[0] - 24.
            else:
                satBNormMLT = rbspSatBDF["MLTNth"].tolist()[0]
            sdFitresDF["delMLATSatB"] = sdFitresDF["MLAT"] -\
                         rbspSatBDF["MLatNth"].tolist()[0]
            sdFitresDF["delMLTSatB"] = sdFitresDF["normMLT"] - satBNormMLT
            nrstLocSatBDF = sdFitresDF[ numpy.abs( sdFitresDF["delMLTSatB"] ) \
                == numpy.min( numpy.abs( sdFitresDF["delMLTSatB"] ) ) ]
            nrstLocSatBDF = nrstLocSatBDF[ numpy.abs( \
                nrstLocSatBDF["delMLATSatB"] ) == numpy.min(\
                 numpy.abs( nrstLocSatBDF["delMLATSatB"] ) ) ].reset_index()
            nrstLocSatBDF["sat"] = "SatB"
            if nrstLocSatADF is not None:
                nrstLocDF = pandas.concat( [ nrstLocDF, nrstLocSatBDF ] )
            else:
                nrstLocDF = nrstLocSatBDF
        print "nrstLocDF"
        print nrstLocDF
        print "nrstLocDF"
        return nrstLocDF


    def get_fp_fitted_vel(self, inpDateTime, southFps=False,\
         filterLat=1., filterMLT=0.5):
        """
        Given an input datetime get lshell fit results
        at the footprints of satellites! 
        We can either work with Northern Hemi FPs 
        or Southern hemi FPs (not both at once!).
        """
        import pandas
        import numpy
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
             - currSatADF["MLAT"])
        currSatADF["del_mlt"] = abs(currSatADF["MLT" + hemiChosen]\
             - currSatADF["MLT"])
        # Drop values which are far away from RBSP FPs
        currSatADF = currSatADF[ ( currSatADF["del_mlat"] < filterLat ) &\
                        ( currSatADF["del_mlt"] < filterMLT
                         ) ].\
                        reset_index(drop=True)
        # SAT B
        currSatBDF["del_mlat"] = abs(currSatBDF["MLat" + hemiChosen]\
             - currSatBDF["MLAT"])
        currSatBDF["del_mlt"] = abs(currSatBDF["MLT" + hemiChosen]\
             - currSatBDF["MLT"])
        # Drop values which are far away from RBSP FPs
        currSatBDF = currSatBDF[ ( currSatBDF["del_mlat"] < filterLat ) &\
                        ( currSatBDF["del_mlt"] < filterMLT ) ].\
                        reset_index(drop=True)
        # Get the best azim from the nearest MLT
        azimDF = self.get_fitvel_sd_nearest( inpDateTime, \
            self.losdataFile, self.inpSAPSDataFile )
        # Setup a DF to store the results
        # SAT-A
        if currSatADF.shape[0] > 0:
            rbspLocMlat = currSatADF["MLat"+hemiChosen].unique()[0]
            rbspLocMlt = currSatADF["MLT"+hemiChosen].unique()[0]
            eventTime = currSatADF["date"].unique()[0]
        else:
            rbspLocMlat = None
            rbspLocMlt = None
            eventTime = None
        fitDFSatA = pandas.DataFrame(
            {'rbspLocMlat': [rbspLocMlat],
             'rbspLocMlt': [rbspLocMlt],
             'eventTime': [eventTime],
             'sat': ["satA"],
             'losVelMagn': [None],
             'losVelAzim': [None],
             'estVelMagn': [None],
             'estVelAzim': [None]
            })
        # SAT-B
        if currSatBDF.shape[0] > 0:
            rbspLocMlat = currSatBDF["MLat"+hemiChosen].unique()[0]
            rbspLocMlt = currSatBDF["MLT"+hemiChosen].unique()[0]
            eventTime = currSatBDF["date"].unique()[0]
        else:
            rbspLocMlat = None
            rbspLocMlt = None
            eventTime = None
        fitDFSatB = pandas.DataFrame(
            {'rbspLocMlat': [rbspLocMlat],
             'rbspLocMlt': [rbspLocMlt],
             'eventTime': [eventTime],
             'sat': ["satB"],
             'losVelMagn': [None],
             'losVelAzim': [None],
             'estVelMagn': [None],
             'estVelAzim': [None]
            })
        # We'll filter out velocities whose magnitudes are less than 50 m/s.
        currSatADF = currSatADF[ abs(currSatADF["Vlos"])\
             > 50. ].reset_index(drop=True)
        currSatBDF = currSatBDF[ abs(currSatBDF["Vlos"])\
             > 50. ].reset_index(drop=True)
        # If there is good data get an lshell fit
        fitDFList = []
        rbspFitResDF = None
        if currSatADF.shape[0] > 0:
            # get the closest velocity in Mlat and MLT
            minLocVelSatA = currSatADF[\
                 currSatADF["del_mlt"] == currSatADF["del_mlt"].min() ]
            if minLocVelSatA.shape[0] == 1  :
                lostFpVelMagnSatA = minLocVelSatA["Vlos"].tolist()[0]
                lostFpVelAazimSatA = minLocVelSatA["azim"].tolist()[0]
                fitDFSatA["losVelMagn"] = lostFpVelMagnSatA
                fitDFSatA["losVelAzim"] = lostFpVelAazimSatA
            else:
                minLocVelSatA = minLocVelSatA[ minLocVelSatA["del_mlat"]\
                 == minLocVelSatA["del_mlat"].min() ].reset_index(drop=True)
                lostFpVelMagnSatA = minLocVelSatA["Vlos"].tolist()[0]
                lostFpVelAazimSatA = minLocVelSatA["azim"].tolist()[0]
                fitDFSatA["losVelMagn"] = lostFpVelMagnSatA
                fitDFSatA["losVelAzim"] = lostFpVelAazimSatA
            # Now get the nearest azim from the fit results, if nothing found 
            # assume the velocities are perfectly westwards!
            if azimDF is None:
                azimOffsetSatA = 0.
            elif azimDF.shape[0] == 0:
                azimOffsetSatA = 0.
            else:
                if azimDF[ azimDF["sat"] == "SatA" ] is not None:
                    if azimDF[ azimDF["sat"] == "SatA" ].shape[0] > 0:
                        azimOffsetSatA = azimDF[ azimDF["sat"] == "SatA" ]["azim"]
                    else:
                        azimOffsetSatA = 0.
                else:
                    azimOffsetSatB = 0.
            estVelAzim = -90. - azimOffsetSatA
            estVelMagnSatA = lostFpVelMagnSatA/( numpy.cos( \
                            numpy.deg2rad( 90. - azimOffsetSatA - lostFpVelAazimSatA ) ) )
            fitDFSatA["estVelMagn"] = estVelMagnSatA
            fitDFSatA["estVelAzim"] = estVelAzim
        fitDFList.append( fitDFSatA )
        if currSatBDF.shape[0] > 0:
            # get the closest velocity in Mlat and MLT
            minLocVelsatB = currSatBDF[\
                 currSatBDF["del_mlt"] == currSatBDF["del_mlt"].min() ]
            if minLocVelsatB.shape[0] == 1  :
                lostFpVelMagnSatB = minLocVelsatB["Vlos"].tolist()[0]
                lostFpVelAazimSatB = minLocVelsatB["azim"].tolist()[0]
                fitDFSatB["losVelMagn"] = minLocVelsatB["Vlos"].tolist()[0]
                fitDFSatB["losVelAzim"] = minLocVelsatB["azim"].tolist()[0]
            else:
                minLocVelsatB = minLocVelsatB[ minLocVelsatB["del_mlat"]\
                 == minLocVelsatB["del_mlat"].min() ].reset_index(drop=True)
                lostFpVelMagnSatB = minLocVelsatB["Vlos"].tolist()[0]
                lostFpVelAazimSatB = minLocVelsatB["azim"].tolist()[0]
                fitDFSatB["losVelMagn"] = minLocVelsatB["Vlos"].tolist()[0]
                fitDFSatB["losVelAzim"] = minLocVelsatB["azim"].tolist()[0]
            # Now get the nearest azim from the fit results, if nothing found 
            # assume the velocities are perfectly westwards!
            if azimDF is None:
                azimOffsetSatB = 0.
            elif azimDF.shape[0] == 0:
                azimOffsetSatB = 0.
            else:
                if azimDF[ azimDF["sat"] == "SatB" ] is not None:
                    if azimDF[ azimDF["sat"] == "SatB" ].shape[0] > 0:
                        azimOffsetSatB = azimDF[ azimDF["sat"] == "SatB" ]["azim"]
                    else:
                        azimOffsetSatB = 0.
                else:
                    azimOffsetSatB = 0.
            estVelAzim = -90. - azimOffsetSatB
            estVelMagnSatB = lostFpVelMagnSatB/( numpy.cos( \
                            numpy.deg2rad( 90. - azimOffsetSatB - lostFpVelAazimSatB ) ) )
            fitDFSatB["estVelMagn"] = estVelMagnSatB
            fitDFSatB["estVelAzim"] = estVelAzim
        fitDFList.append( fitDFSatB )
        # return the combined results
        return pandas.concat(fitDFList)