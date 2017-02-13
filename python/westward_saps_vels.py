if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import os
    import rbsp_fp_westwards_fit
    # File info
    inpLosVelFile = \
        "../data/frmtd-saps-vels-20130316.txt"
    inpSAPSDataFile = \
        "../data/processedSaps-rbsp.txt"
    rbspSatAFile = "../data/rbsp_iono_satA.txt"
    rbspSatBFile = "../data/rbsp_iono_satB.txt"
    rblsObj = rbsp_fp_westwards_fit.WestwardVels(inpLosVelFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=inpSAPSDataFile, applyPOESBnd=False)
    # Out data file
    outDataFile = "../data/westWards-mar16.txt"
    # Loop through the entire event
    startTime = datetime.datetime( 2013, 3, 16, 8, 0 )
    endTime = datetime.datetime( 2013, 3, 16, 10, 0 )
    delDates = endTime - startTime
    timeInterval = 2 # min
    finResDFList = []
    for dd in range((delDates.seconds)/(60*timeInterval) + 1):
        currDt = startTime + \
                            datetime.timedelta( minutes=dd*timeInterval )
        dtStr = currDt.strftime( "%H%M" )
        resDF = rblsObj.get_fp_westwards_vel(currDt)
        finResDFList.append( resDF )
        del resDF
    finDF = pandas.concat( finResDFList )
    # Filter out null values!!
    finDF = finDF[ finDF["eventTime"].notnull() ].reset_index(drop=True)
    finDF = finDF[ finDF["estVelAzim"].notnull() ].reset_index(drop=True)
    finDF.to_csv(outDataFile, sep=' ',\
                   index=False)
    print finDF.head(200)