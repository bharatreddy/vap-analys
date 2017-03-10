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

def get_vel_sd_rbFP(inputDT, inpLosVelFile, inpSAPSDataFile):
    """
    In the current function we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import numpy
    import lshell_events
    # satA footprint file
    satAFpFile = "../data/rbsp_iono_satA.txt"
    # satB footprint file
    satBFpFile = "../data/rbsp_iono_satB.txt"
    # Read in RBSP sat A data
    rbspSatADF = pandas.read_csv(satAFpFile, \
                                 delim_whitespace=True, header=None)
    rbspSatADF.columns = [ "dateStr", "timeStr", "MLatNth", "MLonNth",\
                          "MLTNth", "MLatSth", "MLonSth", "MLTSth", "sat" ]
    rbspSatADF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth", "MLonSth",\
                 "MLTSth"] ] = rbspSatADF[ ["MLatNth", "MLonNth", "MLTNth",\
                 "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
    rbspSatADF["date"] = rbspSatADF.apply( str_to_datetime, axis=1 )
    ####### DO THE SAME FOR SAT B #######
    rbspSatBDF = pandas.read_csv(satBFpFile, \
                                 delim_whitespace=True, header=None)
    rbspSatBDF.columns = [ "dateStr", "timeStr", "MLatNth", "MLonNth",\
                          "MLTNth", "MLatSth", "MLonSth", "MLTSth", "sat" ]
    rbspSatBDF[ ["MLatNth", "MLonNth", "MLTNth", "MLatSth", "MLonSth",\
                 "MLTSth"] ] = rbspSatBDF[ ["MLatNth", "MLonNth", "MLTNth",\
                 "MLatSth", "MLonSth", "MLTSth"] ].astype(float)
    rbspSatBDF["date"] = rbspSatBDF.apply( str_to_datetime, axis=1 )
    # Now select only the datetime we are interested in
    rbspSatADF = rbspSatADF[ rbspSatADF["date"] == inputDT].reset_index()
    rbspSatBDF = rbspSatBDF[ rbspSatBDF["date"] == inputDT].reset_index()
    # get fit data after inputs from Los file and SAPS file
    # inpSAPSDataFile = None
    lsObj = lshell_events.LshellFit(inpLosVelFile, \
        inpSAPSDataFile=inpSAPSDataFile)
    inpDt = datetime.datetime( 2013, 6, 22, 6, 30 )
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
        if nrstLocSatADF is not None:
            nrstLocDF = pandas.concat( [ nrstLocDF, nrstLocSatBDF ] )
        else:
            nrstLocDF = nrstLocSatBDF
    return nrstLocDF


if __name__ == "__main__":
    import datetime
    import pandas
    currDt = datetime.datetime( 2013, 6, 22, 6, 30 )
    inpLosVelFile = \
        "../data/formatted-vels-20130622.txt"
    inpSAPSDataFile = \
        "../../vel-analys/data/processedSaps.txt"
    currDF = get_vel_sd_rbFP(currDt, inpLosVelFile, inpSAPSDataFile)
    print currDF