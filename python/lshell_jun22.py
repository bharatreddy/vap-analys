def str_to_datetime(row):
        # Given a datestr and a time string convert to a python datetime obj.
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

if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import os
    import lshell_events
    # Base directory where all the files are stored
    baseDir = "/home/bharat/Documents/code/frmtd-vels/"
    # Output file to store the results
    currInpLosFile = "../data/event-saps-vels-20130622.txt"
    fitResFile = "../data/fitted_vels_jun22.txt"
    timeInterval = 2 # min
    # Before appending to the file! delete it if it 
    # exists already. We dont want to append to old data!
    if os.path.isfile( fitResFile ):
        os.remove( fitResFile )
    # Before appending to the file! delete it if it 
    # exists already. We dont want to append to old data!
    if os.path.isfile( fitResFile ):
        os.remove( fitResFile )
    # SAPS data file
    inpSAPSDataFile = None
    print "working with--->", currInpLosFile
    # Now get the fitted results for the current date
    lsObj = lshell_events.LshellFit(currInpLosFile,\
     inpSAPSDataFile=inpSAPSDataFile)
    # Need to figure out the minmum and max time
    # to loop through for each file!
    inpColNames = [ "dateStr", "timeStr", "beam", "range", \
      "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
      "radCode"]
    tempDF = pandas.read_csv(currInpLosFile, sep=' ',\
                                 header=None, names=inpColNames)
    # add a datetime col
    # tempDF["date"] = pandas.to_datetime( \
    #                         tempDF['dateStr'].astype(str) + "-" +\
    #                         tempDF['timeStr'].astype(str), \
    #                         format='%Y%m%d-%H%M')
    tempDF["date"] = tempDF.apply( str_to_datetime, axis=1 )
    currStartDate = tempDF["date"].min()
    currEndDate = tempDF["date"].max()
    # loop through the datetimes
    delDates = currEndDate - currStartDate
    # loop through the dates and create a list
    fitDFList = []
    fitDF = None
    for dd in range((delDates.seconds)/(60*timeInterval) + 1):
        currDate = currStartDate + \
            datetime.timedelta( minutes=dd*timeInterval )
        print "working with time-->", currDate
        currfitDF = lsObj.get_timewise_lshell_fits(currDate)
        if currfitDF.shape[0] == 0:
            print "no good fits found! Moving on!!"
            continue
        # To this DF add a datetime column, to distinguish between fits
        currfitDF["date"] = currDate
        fitDFList.append( currfitDF )
        fitDF = pandas.concat( fitDFList )
    # Now only update the file if fitDF is populated
    if fitDF is not None:
        # Now append fitDF to a file and delete the DF!
        # Also we need date and time seperately for idl
        fitDF["dtStr"] = [ x.strftime("%Y%m%d") for x in fitDF["date"]]
        fitDF["tmStr"] = [ x.strftime("%H%M") for x in fitDF["date"]]
        # select the columns to save
        fitDF = fitDF[ ["normMLT", "MLAT", "vSaps", "azim",\
             "vMagnErr", "azimErr", "dtStr", "tmStr"] ]
        with open(fitResFile, 'a') as fra:
            fitDF.to_csv(fra, header=False,\
                              index=False, sep=' ' )
    print fitDF
    print "--------------------SAVED DATA------------------"