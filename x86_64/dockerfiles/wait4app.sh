#!/bin/bash
# Wait for application  to create flag file
#until pids=$(pidof $1)
#do   
#   echo '.' 
#done
until [[ -e ./appflag ]]
do
   echo '.'
   sleep 1
done
#echo "Waiting for 1M seconds"
#sleep 1000000

## There could be multiple notepad processes, so loop over the pids
#for pid in $pids
#do        
#    taskset -p 03 $pid
#    renice -n 5 -p $pid
#    sleep 5
#    renice -n 0 -p $pid
#done
