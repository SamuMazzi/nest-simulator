NEST_SIMULATOR_DIR=/home/samuele/Documenti/GitHub/nest-simulator

cd ../build/
cmake -DCMAKE_INSTALL_PREFIX:PATH=${NEST_SIMULATOR_DIR}/../build/ ${NEST_SIMULATOR_DIR}
cd ../nest-simulator/
make -j16
make install -j16
source ../build/install/bin/nest_vars.sh

# python3 minimal_test.py

# if it doesn't work, delete nest-install folder, uninstall any kind of nest in the system and retry.
