#!/bin/bash
if [ $# -eq 0 ]; then
  echo -e '\n Usage: "profile1 [sleep:]profile2 profile3"\n'
  exit
fi
profiles=$1
for profile in ${profiles[@]}; do 
  slpbfr=0
  if echo $profile | grep -q "\:"; then
    slpbfr=$( echo $profile | cut -d: -f1 )
    profile=$( echo $profile | cut -d: -f2 )
  fi
  sleep $slpbfr
  ./template-ops.py --profile $profile
done
