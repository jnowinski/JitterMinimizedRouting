num_threads=1

#for i in 2 5 8 11 14 1 4 7 10 13 0 3 6 9 12 # original line

#for i in 8 # Test jitter minimalization algorithm

#for i in 16 # Test default algorithm

for i in 15 # Test LMSR algorithm
do
  bash generate_for_paper.sh ${i} ${num_threads} || exit 1
done
