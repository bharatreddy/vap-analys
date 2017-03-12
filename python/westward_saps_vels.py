if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import os
    import rbsp_fp_lshell_fit
    # File info
    # inpLosVelFile = \
    #     "../data/frmtd-saps-vels-20130316.txt"
    inpLosVelFile = "../data/formatted-vels-20130622.txt"
    inpSAPSDataFile = \
        "../data/processedSaps-rbsp.txt"
    rbspSatAFile = "../data/rbsp_iono_satA.txt"
    rbspSatBFile = "../data/rbsp_iono_satB.txt"
    rblsObj = rbsp_fp_lshell_fit.FittedVels(inpLosVelFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=inpSAPSDataFile, applyPOESBnd=False)
    # Out data file
    outDataFile = "../data/westWards-mar16.txt"
    # Loop through the entire event
    startTime = datetime.datetime( 2013, 6, 22, 6, 0 )
    endTime = datetime.datetime( 2013, 6, 22, 6, 20 )
    delDates = endTime - startTime
    timeInterval = 2 # min
    finResDFList = []
    for dd in range((delDates.seconds)/(60*timeInterval) + 1):
        currDt = startTime + \
                            datetime.timedelta( minutes=dd*timeInterval )
        print "current time--->", currDt
        dtStr = currDt.strftime( "%H%M" )
        resDF = rblsObj.get_fp_fitted_vel(currDt)
        print resDF
        finResDFList.append( resDF )
        del resDF
    finDF = pandas.concat( finResDFList )
    # Filter out null values!!
    # finDF = finDF[ finDF["eventTime"].notnull() ].reset_index(drop=True)
    finDF = finDF[ finDF["estVelAzim"].notnull() ].reset_index(drop=True)
    finDF.to_csv(outDataFile, sep=' ',\
                   index=False)
    print finDF.head(200)
    # Write the data to a outfile
    outFileName = "fitVelDataFpRbsp-" + startTime.strftime("%Y%m%d") + ".txt"
    finDF.to_csv("../data/" + outFileName, sep=' ', index=False)