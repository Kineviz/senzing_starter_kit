#!/usr/bin/env bash

echo "y" | G2ConfigTool.py -f /var/senzing/config/demo-config.g2c
/app/file-loader.py -f /data/open-ownership.json
/app/file-loader.py -f /data/open-sanctions.json
/app/sz_graph_export.py -S -o /output/demo_