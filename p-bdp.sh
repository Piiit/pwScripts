#!/bin/bash
set -euo pipefail
SCRIPTNAME=${0##*/}

p-pgprod -c "copy (select stationtype,id,active,available,description,municipality,name,origin,pointprojection,shortname,stationcode from station) to stdout delimiter as ',' csv header"  > station.csv
p-pgprod -c "copy (select id,cname,created_on,cunit,description,rtype from type) to stdout delimiter as ',' csv header"  > type.csv
p-pgprod -c "copy (select id,created_on,period,timestamp,value,station_id,type_id from measurement) to stdout delimiter as ',' csv header"  > measurement.csv
p-pgprod -c "copy (select id,created_on,period,timestamp,value,station_id,type_id from measurementhistory limit 1000000) to stdout delimiter as ',' csv header"  > measurementhistory.csv


p-pgtest -c "\copy station from station.csv delimiter as ',' csv header"
p-pgtest -c "\copy type from type.csv delimiter as ',' csv header"
p-pgtest -c "\copy measurement from measurement.csv delimiter as ',' csv header"
p-pgtest -c "\copy measurementhistory from measurementhistory.csv delimiter as ',' csv header"

p-pgtest -c "select setval('station_seq', (select max(id) from station)); select setval('type_seq', (select max(id) from type)); select setval('measurement_id_seq', (select max(id) from measurement));"


exit 0
