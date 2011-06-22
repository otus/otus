dir=${PWD}
../src/tsdb tsd --port=4242 --staticroot=$dir/../build/staticroot --cachedir="/tmp/tsdb"
