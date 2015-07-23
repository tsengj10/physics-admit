#!/bin/bash
# usage:  ./burst.sh <pdf>

nhi=`ls pg_*.pdf | wc -l`

for (( n=1; n<=$nhi; n++ ))
do
  if [ $n -lt 10 ]; then f=pg_000$n.pdf
  elif [ $n -lt 100 ]; then f=pg_00$n.pdf
  elif [ $n -lt 1000 ]; then f=pg_0$n.pdf
  else f=pg_$n.pdf;
  fi
  pdftotext $f - | head -2
  echo $f
done

exit
