cp ~/cache/osmosis*.tgz osmosis-latest.tgz
if [ ! -f "osmosis-latest.tgz" ];
then
  #wget http://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz
  wget https://github.com/openstreetmap/osmosis/releases/download/0.48.3/osmosis-0.48.3.tgz
  mv osmosis-0.48.3.tgz osmosis-latest.tgz
fi
tar xvfz osmosis-latest.tgz
chmod a+x bin/osmosis
chmod a+x bin/osmosis.bat
bin/osmosis
