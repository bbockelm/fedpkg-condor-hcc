#!/bin/bash

input="condor_src-$1-all-all.tar.gz"

if [ ! -f $input ] ; then
   echo "$0: $input is not a regular file";
   exit 1;
fi

echo "Processing $input"

echo "...extracting $input"
tar xzf $input

cd condor-$1

if [ ! -f BUILD-ID ] ; then
   build="UNKNOWN"
else
   build=`cat BUILD-ID`
fi

echo "...recording BUILD-ID: $build"

echo "...removing NTconfig directory"
rm -rf NTconfig

echo "...removing all externals except 'man'"
mv externals/bundles/man externals/
rm -rf externals/bundles/*
mv externals/man externals/bundles/

echo "...creating condor-$1-$build-RH.tar.gz"
cd ..
tar czfsp condor-$1-$build-RH.tar.gz condor-$1

echo "...cleaning up"
rm -rf condor-$1

