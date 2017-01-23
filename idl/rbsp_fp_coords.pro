pro rbsp_fp_coords


fNameRbsp = "/home/bharatr/Docs/data/rbspOp.txt"

nel_arr_all = 1000000d


dateVal = lonarr(1)
timeVal = intarr(1)
satVal = ""

dateArr = lonarr(nel_arr_all)
timeArr = intarr(nel_arr_all)
xGeoArr = fltarr(nel_arr_all)
yGeoArr = fltarr(nel_arr_all)
zGeoArr = lonarr(nel_arr_all)
satArr = strarr(nel_arr_all)

rcnt=0.d
OPENR, 1, fNameRbsp
WHILE not eof(1) do begin
	;; read the data line by line

	READF,1, dateVal, timeVal, yearVal, monVal, dayVal, xGeoVal, yGeoVal, zGeoVal, geodLatVal, geodLonVal, altVal, satVal

	dateArr[rcnt] = ulong(dateVal)
	timeArr[rcnt] = uint(timeVal)
	xGeoArr[rcnt] = xGeoVal
	yGeoArr[rcnt] = yGeoVal
	zGeoArr[rcnt] = zGeoVal
	satArr[rcnt] = satVal

	rcnt += 1

ENDWHILE         
close,1	


dateArr = dateArr[0:rcnt-1]
timeArr = timeArr[0:rcnt-1]
xGeoArr = xGeoArr[0:rcnt-1]
yGeoArr = yGeoArr[0:rcnt-1]
zGeoArr = zGeoArr[0:rcnt-1]
satArr = satArr[0:rcnt-1]



; now loop through the array and calculate AACGM coordinates from the inputs

for rr=0.d , n_elements(dateArr)-1 do begin

	; x, y and z geo coords
	arr_geo_coords = [ [xGeoArr[rr]], [yGeoArr[rr]], [zGeoArr[rr]] ]

	xyz_to_polar, arr_geo_coords/!re, mag=alt, theta=glat, phi=glon
	;; convert to AACGM coords
	tmpp = cnvcoord(glat, glon, [200.])
	latFpRbspNth = tmpp[0]
	lonFpRbspNth = tmpp[1]


	print, "aacgm lat, lon---->", latFpRbspNth, lonFpRbspNth

endfor



end