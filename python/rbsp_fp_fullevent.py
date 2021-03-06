if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import os
    import rbsp_fp_lshell_fits
    # File info
    inpLosVelFile = \
        "../data/frmtd-saps-vels-20130316.txt"
    inpSAPSDataFile = \
        "../data/processedSaps-rbsp.txt"
    rbspSatAFile = "../data/rbsp_iono_satA.txt"
    rbspSatBFile = "../data/rbsp_iono_satB.txt"
    rblsObj = rbsp_fp_lshell_fits.LshellRbsp(inpLosVelFile, rbspSatAFile, \
             rbspSatBFile, inpSAPSDataFile=inpSAPSDataFile, applyPOESBnd=False)
    # Out data file
    outDataFile = "../data/final_results-mar16.txt"
    # Loop through the entire event
    startTime = datetime.datetime( 2013, 3, 16, 9, 0 )
    endTime = datetime.datetime( 2013, 3, 16, 10, 0 )
    delDates = endTime - startTime
    timeInterval = 2 # min
    finResDFList = []
    for dd in range((delDates.seconds)/(60*timeInterval) + 1):
        currDt = startTime + \
                            datetime.timedelta( minutes=dd*timeInterval )
        dtStr = currDt.strftime( "%H%M" )
        # Now here check if there is a good fit for the min chosen
        # value of filter lat and mlt. If not we'll try to find a 
        # better fit by choosing a broader range!
        filterLatArr = [ 0.5, 1. ]
        filterMLTArr = [ 0.5, 1. ]
        for flLat in filterLatArr:
            for flMlt in filterMLTArr:
                # We'll try and get fitting for all
                # lat/mlt combinations..then choose the best fit
                plotFitVelSatA = None#"../figs/satA-" + dtStr + "-" + str(flLat) + "-" + str(flMlt) + ".pdf"
                plotFitVelSatB = None#"../figs/satB-" + dtStr + "-" + str(flLat) + "-" + str(flMlt) + ".pdf"
                resDF = rblsObj.get_fp_fit_vel(currDt, filterLat=flLat, \
                     filterMLT=flMlt, plotFitVelSatA=plotFitVelSatA,\
                      plotFitVelSatB=plotFitVelSatB)
                resDF["filter_lat_range"] = flLat
                resDF["filter_mlt_range"] = flMlt
                finResDFList.append( resDF )
                del resDF
                # Append the DF to a file
                # with open(outDataFile, 'a') as rFA:
                #     resDF.to_csv(rFA, header=False,\
                #                       index=False, sep=' ' )
    finDF = pandas.concat( finResDFList )
    # Filter out null values!!
    finDF = finDF[ finDF["eventTime"].notnull() ].reset_index(drop=True)
    finDF = finDF[ finDF["estVelAzim"].notnull() ].reset_index(drop=True)
    # Filter out estimated azimuths which are 
    # off by more than 20 degrees from westwards
    finDF = finDF[ abs(finDF["estVelAzim"]) <= 20. ].reset_index()
    finDF.to_csv(outDataFile, sep=' ',\
                   index=False)
    print finDF.head(200)