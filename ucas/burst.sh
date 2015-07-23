#!/bin/bash
# usage:  ./burst.sh <pdf>

echo Burst $1
pdftk $1 burst

echo There are `ls pg_*.pdf | wc -l` pages.

echo Collate $1
./burst-check.sh | python burst-collate.py > collate.sh

echo There are `wc -l collate.sh` lines in collate.sh.
echo There are `awk 'NF%4!=0{print}' collate.sh` lines in collate.sh with odd lengths.
echo Now check collate.sh before running it.

exit
