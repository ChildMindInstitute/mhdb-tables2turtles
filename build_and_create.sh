# build_and_create.sh
#
# This is a simple BASH script to build and execute mhdb/create_mhdb.
#
# Authors:
#     - Jon Clucas, 2017 (jon.clucas@childmind.org)
#     - Arno Klein, 2019 (arno@childmind.org)  http://binarybottle.com
#
# Copyright 2017, Child Mind Institute (http://childmind.org),
# Apache v2.0 License

python3 setup.py build
python3 setup.py install
cd mhdb
./create_mhdb
cd ..
