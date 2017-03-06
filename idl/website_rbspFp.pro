pro website_rbspFp


outFormat = '(i4,1x,i2,1x,i2,1x,i2,1x,i2,1x,a1,4(1x,f7.2))'
fNameInputRbsp = "/home/bharatr/Docs/data/rbspFpMagn.dat"

fNameOutRbsp = "/home/bharatr/Docs/data/rbspFp.dat"

nel_arr_all = 2500000d


year = intarr(1)
month = intarr(1)
day = intarr(1)
hour = intarr(1)
min = intarr(1)
satType = strarr(1)
mlatNth = fltarr(1) 
mlonNth = fltarr(1) 
mlatSth = fltarr(1) 
mlonSth = fltarr(1) 


l6 = ""

yearArr = intarr(nel_arr_all)
monArr = intarr(nel_arr_all)
dayArr = intarr(nel_arr_all)
hourArr = intarr(nel_arr_all)
minArr = intarr(nel_arr_all)
satArr = strarr(nel_arr_all)
mlatNthArr = fltarr(nel_arr_all)
mlonNthArr = fltarr(nel_arr_all)
mlatSthArr = fltarr(nel_arr_all)
mlonSthArr = fltarr(nel_arr_all)

rcnt=0.d
missedCnt = 0.d
OPENR, 1, fNameInputRbsp
WHILE not eof(1) do begin
	;; read the data line by line

	READF,1, year, month, day, hour, min, l6 ,l7

	newLine = STRSPLIT(l6, /EXTRACT)

	if (n_elements(newLine) ne 5) then begin
		missedCnt += 1
		continue
	endif

	yearArr[rcnt] = year
	monArr[rcnt] = month
	dayArr[rcnt] = day
	hourArr[rcnt] = hour
	minArr[rcnt] = min
	satArr[rcnt] = newLine[0]
	mlatNthArr[rcnt] = float( newLine[1] );float( newLine[1] )
	mlonNthArr[rcnt] = float( newLine[2] );float( newLine[2] )
	mlatSthArr[rcnt] = float( newLine[3] );float( newLine[3] )
	mlonSthArr[rcnt] = float( newLine[4] );float( newLine[4] )

	


	;print, "line1--->", newLine[0], "-->", newLine[1], "-->", newLine[2], "-->", newLine[3], "-->", newLine[4], "--->" ,n_elements(newLine)
	;print, "-------------------------------------------"
	;print, "l7--->", l7

	rcnt += 1

ENDWHILE         
close,1	
print, "missed count--->", missedCnt


yearArr = yearArr[0:rcnt-1]
monArr = monArr[0:rcnt-1]
dayArr = dayArr[0:rcnt-1]
hourArr = hourArr[0:rcnt-1]
minArr = minArr[0:rcnt-1]
satArr = satArr[0:rcnt-1]
mlatNthArr = mlatNthArr[0:rcnt-1]
mlonNthArr = mlonNthArr[0:rcnt-1]
mlatSthArr = mlatSthArr[0:rcnt-1]
mlonSthArr = mlonSthArr[0:rcnt-1]


openw, 1, fNameOutRbsp

for rr=0.d , n_elements(yearArr)-1 do begin

	currMlatNth = mlatNthArr[rr]
	currMlonNth = mlonNthArr[rr]
	currMlatSth = mlatSthArr[rr]
	currMlonSth = mlonSthArr[rr]

	;

	gCrdNth = cnvcoord( currMlatNth, currMlonNth, 200., /geo )
	gCrdSth = cnvcoord( currMlatSth, currMlonSth, 200., /geo )


	print, "currMlatSth, currMlonSth------->", currMlatSth, currMlonSth, gCrdSth


	print, yearArr[rr], monArr[rr], dayArr[rr], hourArr[rr], minArr[rr], satArr[rr], gCrdNth[0], gCrdNth[1], gCrdSth[0], gCrdSth[1], $
	                                                                format = outFormat

	printf,1, yearArr[rr], monArr[rr], dayArr[rr], hourArr[rr], minArr[rr], satArr[rr], gCrdNth[0], gCrdNth[1], gCrdSth[0], gCrdSth[1], $
	                                                                format = outFormat


endfor

close,1




end