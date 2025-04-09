#!/bin/sh

INTERFERENCES=("cpu" "l1d" "l1i" "l2" "llc" "membw")
PARSEC_JOBS=("blackscholes" "canneal" "dedup" "ferret" "freqmine" "radix" "vips")

#none_real=()
#for job in ${PARSEC_JOBS[@]}
#do
#    real=$(sed -n '/^real/p' results-part2a/${job}_none.log)
#    time_only=$(echo "$real" | grep -o "[0-9]\+m[0-9.]\+s")
#    min=${time_only%%m*}
#    sec=${time_only#*m}
#    sec=${sec%s}
#    total=$(echo "$min * 60 + $sec" | bc)
#    none_real+=("$total")
#done
#
#echo "${none_real[@]}"
     

for job in ${PARSEC_JOBS[@]}
do
    real=$(sed -n '/^real/p' results-part2a/${job}_none.log)
    time_only=$(echo "$real" | grep -o "[0-9]\+m[0-9.]\+s")
    min=${time_only%%m*}
    sec=${time_only#*m}
    sec=${sec%s}
    total=$(echo "$min * 60 + $sec" | bc -l)
#    none_real+=("$total")

    for interference in ${INTERFERENCES[@]}
    do
        real=$(sed -n '/^real/p' results-part2a/${job}_${interference}.log)
        time_only=$(echo "$real" | grep -o "[0-9]\+m[0-9.]\+s")
        min=${time_only%%m*}
        sec=${time_only#*m}
        sec=${sec%s}
        total2=$(echo "$min * 60 + $sec" | bc -l)
        normalized=$(echo "$total2 / $total" | bc -l)
        rounded=$(printf "%.2f" "$normalized")
        
        if (( $(echo "$rounded <= 1.3" | bc -l) )); then
            color="green"
        elif (( $(echo "$rounded <= 2.0" | bc -l) )); then
            color="YellowOrange"
        else
            color="red"
        fi
            
        
        echo "$job, $interference, $normalized, $color"
    done
done
