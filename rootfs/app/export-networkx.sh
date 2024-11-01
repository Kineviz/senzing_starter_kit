#!/usr/bin/env bash

set -x


# sleep infinity


echo "y" | G2ConfigTool.py -f /config/demo-config.g2c
/app/file-loader.py -f /data/open-ownership.json
/app/file-loader.py -f /data/open-sanctions.json
/app/sz_graph_export.py -S -o /output/demo_