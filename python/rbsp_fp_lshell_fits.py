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


    def get_fp_fit_vel(self, inpDateTime, southFps=False, filterLat=0.5, \
         filterMLT=0.5, plotFitVelSatA=None, plotFitVelSatB=None):
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
        # Setup a DF to store the results
        # SAT-A
        rbspLocMlat = currSatADF["MLat"+hemiChosen].unique()[0]
        rbspLocMlt = currSatADF["MLT"+hemiChosen].unique()[0]
        eventTime = currSatADF["date"].unique()[0]
        fitDFSatA = pandas.DataFrame(
            {'rbspLocMlat': [rbspLocMlat],
             'rbspLocMlt': [rbspLocMlt],
             'eventTime': [eventTime],
             'sat': ["satA"],
             'estVelMagn': [None],
             'estVelAzim': [None],
             'errVelMagn': [None],
             'errVelAzim': [None],
             'nUniqAzims': [None],
             'losazimRange': [None]
            })
        # SAT-B
        rbspLocMlat = currSatBDF["MLat"+hemiChosen].unique()[0]
        rbspLocMlt = currSatBDF["MLT"+hemiChosen].unique()[0]
        eventTime = currSatBDF["date"].unique()[0]
        fitDFSatB = pandas.DataFrame(
            {'rbspLocMlat': [rbspLocMlat],
             'rbspLocMlt': [rbspLocMlt],
             'eventTime': [eventTime],
             'sat': ["satB"],
             'estVelMagn': [None],
             'estVelAzim': [None],
             'errVelMagn': [None],
             'errVelAzim': [None],
             'nUniqAzims': [None],
             'losazimRange': [None]
            })
        # We'll filter out velocities whose magnitudes are less than 100 m/s.
        currSatADF = currSatADF[ abs(currSatADF["Vlos"])\
             > 100. ].reset_index(drop=True)
        currSatBDF = currSatBDF[ abs(currSatBDF["Vlos"])\
             > 100. ].reset_index(drop=True)
        # If there is good data get an lshell fit
        fitDFList = []
        rbspFitResDF = None
        if currSatADF.shape[0] > 0:
            # get fit velocities
            ( nUniqAzims, losazimRange, estVelMagn, estVelAzim,\
             errVelMagn, errVelAzim ) = self.fit_los(currSatADF,\
                plotName=plotFitVelSatA)
            fitDFSatA["nUniqAzims"] = nUniqAzims
            fitDFSatA["losazimRange"] = losazimRange
            fitDFSatA["estVelMagn"] = estVelMagn
            fitDFSatA["estVelAzim"] = estVelAzim
            fitDFSatA["errVelMagn"] = errVelMagn
            fitDFSatA["errVelAzim"] = errVelAzim
        fitDFList.append( fitDFSatA )
        if currSatBDF.shape[0] > 0:
            # get fit velocities
            ( nUniqAzims, losazimRange, estVelMagn, estVelAzim,\
             errVelMagn, errVelAzim ) = self.fit_los(currSatBDF,\
                plotName=plotFitVelSatB)
            fitDFSatB["nUniqAzims"] = nUniqAzims
            fitDFSatB["losazimRange"] = losazimRange
            fitDFSatB["estVelMagn"] = estVelMagn
            fitDFSatB["estVelAzim"] = estVelAzim
            fitDFSatB["errVelMagn"] = errVelMagn
            fitDFSatB["errVelAzim"] = errVelAzim
        fitDFList.append( fitDFSatB )
        # return the combined results
        return pandas.concat(fitDFList)


    def fit_los(self, inpLosVelDF, plotName=None):
        """
        In this function we'll identify if a good fit
        can be derived out of the l-o-s velocities.
        """
        import pandas
        import scipy.optimize
        import matplotlib.pyplot as plt
        # get a few basic parameters - azimuth range
        # number of unique azimuths
        azimRange = inpLosVelDF["azim"].max()\
        - inpLosVelDF["azim"].min()
        print "azimRange--->", azimRange
        # If azim range is less than 25, skip!
        if abs(azimRange) < 25:
            print "azim range not good for fitting!"
        uniqAzims = set( list( inpLosVelDF["azim"].unique() ) )
        print "uniqAzims--->", uniqAzims
        # If number of unique azims are less than 3 skip!
        if len( uniqAzims ) < 3:
            print "num of unique azims not good for fitting!"
        # Now do the fitting if everything works
        popt, pcov = scipy.optimize.curve_fit(self.vel_sine_func, \
                                            inpLosVelDF['azim'].T,\
                                            inpLosVelDF['Vlos'].T,
                                           p0=( 1000., 10. ))
        # print "popt--->", popt
        # print "err vel magn-->", pcov[0,0]**0.5
        # print "err azim-->", pcov[1,1]**0.5
        # If chosen make a plot
        if plotName is not None:
            plt.style.use('ggplot')
            thetaArr = range(-110, 120, 10)
            vLosArr = [ round( \
                self.vel_sine_func(t, Vmax=popt[0], delTheta=popt[1]) )\
                 for t in thetaArr ]
            fig1 = plt.figure()
            ax = fig1.add_subplot(111)
            inpLosVelDF.plot( x="azim", y="Vlos", kind="scatter", ax=ax )
            ax.plot( thetaArr, vLosArr )
            ax.get_figure().savefig( plotName, bbox_inches='tight' )
        return ( len( uniqAzims ), azimRange, popt[0], \
            popt[1], pcov[0,0]**0.5, pcov[1,1]**0.5 )



    def vel_sine_func(self, theta, Vmax, delTheta):
        import numpy
        # Fit a sine curve for a given cell
        # we are working in degrees but numpy deals with radians
        # convert to radians
        return Vmax * numpy.sin( numpy.deg2rad(theta) +\
                                numpy.deg2rad(delTheta) )