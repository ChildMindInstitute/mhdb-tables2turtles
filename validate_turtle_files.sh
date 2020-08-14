# validate_turtle_files.sh
#
# This is a simple BASH script to validate output turtle files.
#
# Authors:
#     - Arno Klein, 2020 (arno@childmind.org)  http://binarybottle.com
#
# Copyright 2020, Child Mind Institute (http://childmind.org),
# Apache v2.0 License

#echo "Building mhdb-states.ttl..."
#ttl output/mhdb-states.ttl

echo "Building mhdb-disorders.ttl..."
ttl output/mhdb-disorders.ttl

echo "Building mhdb-resources.ttl..."
ttl output/mhdb-resources.ttl

echo "Building mhdb-assessments.ttl..."
ttl output/mhdb-assessments.ttl

echo "Building mhdb-measures.ttl..."
ttl output/mhdb-measures.ttl
