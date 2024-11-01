#!/usr/bin/env bash

set -x

# Wait until files appear.

until [ -f /input/demo_senzing_graph.json ]
do
     echo "... waiting for /input/demo_senzing_graph.json"
     sleep 5
done

until [ -f /input/demo_source_graph.json ]
do
     echo "... waiting for /input/demo_source_graph.json"
     sleep 5
done

# Print files.

echo "Contents of /input/demo_senzing_graph.json"
cat /input/demo_senzing_graph.json

echo "Contents of /input/demo_source_graph.json"
cat /input/demo_source_graph.json
