pro test_map

common omn_data_blk
common dst_data_blk

;; inputs for tsyg model
internal_model = 'igrf'
external_model='t01'
rlim = 40.*!re

dateArr = [20121230]
timeArr = [1000]
sfjul, dateArr[0], timeArr[0], julVal
altArr = [  17073.0 + 6371. ]
latArr = [ -9.0 ]
lonArr = [ -137.7 ]
julsArr = [julVal]



; now loop through the array and calculate AACGM coordinates from the inputs

for rr=0.d , n_elements(dateArr)-1 do begin

	_alt = altArr[rr]
	_lat = latArr[rr]
	_lon = lonArr[rr]
	
	;; convert the coords into X, Y and Z (cartesian)
	_x = (_alt)*cos(_lon*!dtor)*cos(_lat*!dtor)
	_y = (_alt)*sin(_lon*!dtor)*cos(_lat*!dtor)
	_z = (_alt)*sin(_lat*!dtor)

	in_arr_geo = [ [_x], [_y], [_z] ]
	
	;; project to ionosphere (north)
	currJulRead = julsArr[rr]
	tarr = [(currJulRead - julday(1,1,1970,0))*86400.d]


	; need to get the params for tsyg models
	; [pdyn,dst,imf-by,imf-bz,g1,g2]
	;; for gmagpar the parameters vary with time
	;; we need to populate the params!!
	;;read for the entire day and get the closest value which is not nan
	chkDstLoaded=dst_check_loaded(dateArr[rr])
	chkOmnLoaded=omn_check_loaded(dateArr[rr])

	if chkDstLoaded eq 0 then begin
		dst_read, dateArr[rr]
		dstJulsArr = dst_data.juls
		dstDataArr = dst_data.dst_index
		jindsFiniteDst = where(finite(dstJulsArr))
		dstJulsArr = dstJulsArr[jindsFiniteDst]
		dstDataArr = dstDataArr[jindsFiniteDst]
	endif
	dd = min( abs( dstJulsArr-currJulRead ), index)
	;; Select the appropriate dst index
	currDstIndex = dstDataArr[index]
	; check if time is not too off
	flagDstVal = 0
	if dd*1440.d gt 60. then begin
		print, '------->Data found, but '+string(dd*1440.d,format='(I4)')+' minutes off chosen time.'
		flagDstVal = 1
	endif
	;print, "indexxx DST-------->", dd*1440.d, currDstIndex, dateArr[rr], timeArr[rr]

	if chkOmnLoaded eq 0 then begin
		omn_read, dateArr[rr]
		omnJulsArr = omn_data.juls
		omnPdArr = omn_data.pd
		omnBzArr = omn_data.bz_gsm
		omnByArr = omn_data.by_gsm
		jindsFinitePd = where(finite(omnPdArr))
		jindsFiniteBz = where(finite(omnBzArr))
		jindsFiniteBy = where(finite(omnByArr))

		pdFiniteJulsArr = omnJulsArr[jindsFinitePd]
		pdFiniteDataArr = omnPdArr[jindsFinitePd]

		bzFiniteJulsArr = omnJulsArr[jindsFiniteBz]
		bzFiniteDataArr = omnBzArr[jindsFiniteBz]

		byFiniteJulsArr = omnJulsArr[jindsFiniteBy]
		byFiniteDataArr = omnByArr[jindsFiniteBy]

	endif

	ddPd = min( abs( pdFiniteJulsArr-currJulRead ), indexPd)
	flagPdVal = 0
	flagBzVal = 0
	flagByVal = 0
	if ddPd*1440.d gt 60. then begin
		print, '------->Data found, but '+string(ddPd*1440.d,format='(I4)')+' minutes off chosen time.'
		flagPdVal = 1
	endif
	ddBz = min( abs( bzFiniteJulsArr-currJulRead ), indexBz)
	if ddBz*1440.d gt 60. then begin
		print, '------->Data found, but '+string(ddBz*1440.d,format='(I4)')+' minutes off chosen time.'
		flagBzVal = 1
	endif
	ddBy = min( abs( byFiniteJulsArr-currJulRead ), indexBy)
	if ddBy*1440.d gt 60. then begin
		print, '------->Data found, but '+string(ddBy*1440.d,format='(I4)')+' minutes off chosen time.'
		flagByVal = 1
	endif

	currPd = pdFiniteDataArr[indexPd]
	currBz = bzFiniteDataArr[indexBz]
	currBy = byFiniteDataArr[indexBy]
	;; setup the gmagpar array
	;; [pdyn,dst,imf-by,imf-bz,g1,g2]
	gmagpar = [ currPd, currDstIndex, currBy, currBz, 0.5, 1.1 ]
	print, "gmagpar---------->", gmagpar
	
	if external_model eq 't89' then begin
		par = [2.]
	endif else begin
		par = fltarr(10)
		par[0:5]=gmagpar
	endelse


	;; trace to northern hemisphere!!!
	;; trace to northern hemisphere!!!
	trace2iono, tarr, in_arr_geo, out_arr, $
	in_coord='geo', out_coord='geo', $
	external=external_model, internal=internal_model, $
	par=par, rlim=rlim, /km
	
	out_arr_geo = out_arr

	;; Get the latitude and longitude in the ionosphere
	if sqrt(total((out_arr_geo/!re)^2)) gt 2. then begin
		latFpRbspNth = !values.f_nan
		lonFpRbspNth = !values.f_nan
		mltFpRbspNth = !values.f_nan
	endif else begin
		xyz_to_polar, out_arr_geo/!re, mag=alt, theta=glat, phi=glon
		;; convert to AACGM coords
		tmpp = cnvcoord(glat, glon, [200.])
		latFpRbspNth = tmpp[0]
		lonFpRbspNth = tmpp[1]
		; convert to mlt
		parse_date, dateArr[rr], year, month, day
		utsec = (currJulRead - julday(1, 1, year, 0, 0))*86400.d
		mltFpRbspNth =  mlt(year, utsec, lonFpRbspNth)
	endelse

	;; trace to southern hemisphere!!!
	;; trace to southern hemisphere!!!
	trace2iono, tarr, in_arr_geo, out_arr_sth, $
		in_coord='geo', out_coord='geo', $
		external=external_model, internal=internal_model, $
		par=par, rlim=rlim, /km, /south
	
	out_arr_geo_sth = out_arr_sth

	;; Get the latitude and longitude in the ionosphere
	;; Get the latitude and longitude in the ionosphere
	if sqrt(total((out_arr_geo_sth/!re)^2)) gt 2. then begin
		latFpRbspSth = !values.f_nan
		lonFpRbspSth = !values.f_nan
		mltFpRbspSth = !values.f_nan
	endif else begin
		xyz_to_polar, out_arr_geo_sth/!re, mag=alt, theta=glat, phi=glon
		;; convert to AACGM coords
		tmpp = cnvcoord(glat, glon, [200.])
		latFpRbspSth = tmpp[0]
		lonFpRbspSth = tmpp[1]
		; convert to mlt
		parse_date, dateArr[rr], year, month, day
		utsec = (currJulRead - julday(1, 1, year, 0, 0))*86400.d
		mltFpRbspSth =  mlt(year, utsec, lonFpRbspSth)
	endelse

	print, "o/p--->", latFpRbspNth, lonFpRbspNth, mltFpRbspNth
	

endfor

end