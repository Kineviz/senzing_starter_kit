#!/usr/bin/env bash

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

echo "First 10 lines of /input/demo_senzing_graph.json"
head -10 /input/demo_senzing_graph.json

echo "First 10 lines of /input/demo_source_graph.json"
head -10 /input/demo_source_graph.json
