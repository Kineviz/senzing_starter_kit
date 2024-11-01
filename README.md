# Starter Kit

This project illustrates using open data with both Kineviz and Senzing.

*question: Michael, if you want to add step 0 or prior setup about copying the G2C.db sqlite database ...
Also I am not married to any of this, so feel free to show it differently.
Below is really the script and what each output should look like.*

  1. configure Sz for the demo

    Its just a matter of registering the data sources like so ...

    ```console
    G2ConfigTool.py -f ../config/demo-config.g2c
    ```

    The result should look like this ...

    ```console
    ----- addDataSource -----
    addDataSource OPEN-OWNERSHIP

    Data source successfully added!

    ----- addDataSource -----
    addDataSource OPEN-SANCTIONS

    Data source successfully added!

    ----- save -----
    save

    Configuration changes saved!

    ----- quit -----
    quit

    There are unsaved changes, would you like to save first? (y/n) y

    Configuration changes saved!

    ```

  1. load OpenSanctions + OpenOwnership into Sz

    There is an open source file loader program thats json files into Sz.
    It is located [here](https://github.com/senzing-garage/file-loader):

    ```console
    wget https://raw.githubusercontent.com/senzing-garage/file-loader/refs/heads/main/file-loader.py
    python3 file-loader.py -f ../data/open-ownership.json
    python3 file-loader.py -f ../data/open-sanctions.json

    ```

    after each run, you should see a success message like so ...

    ```console
    2024-10-31 00:03:31,194 - file-loader - INFO:  Results
    2024-10-31 00:03:31,194 - file-loader - INFO:  -------
    2024-10-31 00:03:31,194 - file-loader - INFO:
    2024-10-31 00:03:31,195 - file-loader - INFO:  Source file:                /project/data/open-sanctions.json
    2024-10-31 00:03:31,195 - file-loader - INFO:  With info file:             With info responses not requested
    2024-10-31 00:03:31,195 - file-loader - INFO:
    2024-10-31 00:03:31,195 - file-loader - INFO:  Successful loaded records:    24    <<------ correct count
    2024-10-31 00:03:31,195 - file-loader - INFO:  Error loaded records:         0     <<------ with no errors
    2024-10-31 00:03:31,195 - file-loader - INFO:  Loading elapsed time (mins):  0.1
    2024-10-31 00:03:31,195 - file-loader - INFO:
    2024-10-31 00:03:31,195 - file-loader - INFO:  Successful redo records:      1
    2024-10-31 00:03:31,195 - file-loader - INFO:  Error redo records:           0
    2024-10-31 00:03:31,195 - file-loader - INFO:  Redo elapsed time (mins):     0.0
    2024-10-31 00:03:31,195 - file-loader - INFO:
    2024-10-31 00:03:31,195 - file-loader - INFO:  Total elapsed time (mins):    0.1

    ```

  1. export ER results as a NetworkX graph, serialized to JSON
    There is an open source export program that reads an Sz database and writes networkx json for the purpose of loading the graph database.
    It is located [here](https://github.com/senzing-garage/sz-graph-export)

    ```console
    wget https://raw.githubusercontent.com/senzing-garage/sz-graph-export/refs/heads/main/sz_graph_export.py
    python3 sz_graph_export.py -S -o ../export/demo_
    ```

    And the result should look like this ...

    ```console
    10/31 12:09 INFO: getting max entity_id ...
    10/31 12:09 INFO: getting entities from 1 to 1000000 ...
    10/31 12:09 INFO: 193 entities processed after 0.0 minutes, done!
    10/31 12:09 INFO: 156 relationships processed after 0.0 minutes, done!
    10/31 12:09 INFO: processed completed in 0.0 minutes   <-------------------
    ```

    Two files will have been written to the export diretory

    * demo_source_graph.json  These are the nodes and edges that were loaded from open_ownership.json and open_sanctions.json files.
    * demo_senzing_graph.json  These are the resolved nodes and edges that Sz resolved them into.

    ... over to Kineviz!

  1. load the source data records and ER results into Kv
  1. video to illustrate graph (3D spin)
  1. drill-down into a specific case to explore
  1. illustrate the "before and after" contrast of this case with or without ER
