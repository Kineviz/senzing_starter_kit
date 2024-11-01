#! /usr/bin/env python3

import os
import sys
import argparse
import json
import time
import logging
from datetime import datetime
from itertools import groupby
from operator import itemgetter
import re

try:
    # will eventually allow for API option if no database access
    # from senzing import G2ConfigMgr, G2Engine, G2EngineFlags, G2Exception
    from senzing import G2ConfigMgr
    from G2Database import G2Database
except:
    print('Could not import Senzing API, please make sure environment set')
    sys.exit(1)


class json2attribute():

    def __init__(self, iniParams):
        try:
            g2ConfigMgr = G2ConfigMgr()
            g2ConfigMgr.init('pyG2ConfigMgr', iniParams, False)
            defaultConfigID = bytearray()
            g2ConfigMgr.getDefaultConfigID(defaultConfigID)
            defaultConfigDoc = bytearray()
            g2ConfigMgr.getConfig(defaultConfigID, defaultConfigDoc)
            cfg_data = json.loads(defaultConfigDoc.decode())
            g2ConfigMgr.destroy()
            self.attr_lookup = {}
            for record in cfg_data['G2_CONFIG']['CFG_ATTR']:
                self.attr_lookup[record['ATTR_CODE']] = record
        except Exception as ex:
            raise Exception(ex)

    def parse(self, json_string):
        try:
            json_data = json.loads(json_string)
        except Exception as ex:
            raise Exception(ex)

        self.attr_groups = {}
        for attribute in (x for x in json_data if json_data[x]):
            if isinstance(json_data[attribute], list):
                i = 0
                for child_data in json_data[attribute]:
                    i += 1
                    for record_attribute in (x for x in child_data if child_data[x]):
                        attr_data = self.lookup_attribute(record_attribute.upper(), child_data[record_attribute])
                        segment_id = f'{attribute}-{i}'
                        self.update_grouping(segment_id, attr_data)
            else:
                attr_data = self.lookup_attribute(attribute.upper(), json_data[attribute])
                segment_id = 'ROOT'
                self.update_grouping(segment_id, attr_data)

        self.attr_list = []
        for segment_id in self.attr_groups:
            segment, attribute, usage_type = segment_id.split('|')
            min_attr_id = 9999
            attr_values = []
            used_from_date = used_thru_date = None
            for attr_data in sorted(self.attr_groups[segment_id], key=itemgetter('ATTR_ID')):
                if attr_data.get('ATTR_ID') < min_attr_id:
                    min_attr_id = attr_data.get('ATTR_ID')
                if attr_data.get('FELEM_CODE') == 'USAGE_TYPE':
                    usage_type = attr_data['ATTR_VALUE']
                elif attr_data.get('FELEM_CODE') == 'USED_FROM_DT':
                    used_from_date = attr_data['ATTR_VALUE']
                elif attr_data.get('FELEM_CODE') == 'USED_THRU_DT':
                    used_thru_date = attr_data['ATTR_VALUE']
                elif attr_data.get('FELEM_CODE') == 'KEY_TYPE' and attribute == 'REL_POINTER':
                    continue # simply ignoring optional domain for rel_pointers
                else:
                    attr_values.append(str(attr_data['ATTR_VALUE']))
            self.attr_list.append({'SEGMENT': segment,
                                   'ATTR_ID': min_attr_id,
                                   'ATTRIBUTE': attribute,
                                   'ATTR_VALUE': ' '.join(attr_values),
                                   'USAGE_TYPE': usage_type,
                                   'USED_FROM_DT': used_from_date,
                                   'USED_THRU_DT': used_thru_date})
        return self.attr_list

    def lookup_attribute(self, attr_name, attr_value):
        attr_data = {'ATTR_ID': 9999, 'ATTR_CODE': attr_name, 'ATTR_CLASS': 'PAYLOAD'}
        if attr_name in self.attr_lookup:
            attr_data = self.attr_lookup[attr_name].copy()
        elif '_' in attr_name:
            possible_label = attr_name[0:attr_name.find('_')]
            possible_attr_name = attr_name[attr_name.find('_') + 1:]
            if possible_attr_name in self.attr_lookup:
                attr_data = self.attr_lookup[possible_attr_name].copy()
                attr_data['USAGE_TYPE'] = possible_label
            else:
                possible_label = attr_name[attr_name.rfind('_') + 1:]
                possible_attr_name = attr_name[0:attr_name.rfind('_')]
                if possible_attr_name in self.attr_lookup:
                    attr_data = self.attr_lookup[possible_attr_name].copy()
                    attr_data['USAGE_TYPE'] = possible_label
        if not attr_data.get('FTYPE_CODE'):
            attr_data['FTYPE_CODE'] = attr_name
        attr_data['ATTR_VALUE'] = attr_value
        return attr_data

    def update_grouping(self, segment_id, attr_data):
        segment_id += f"|{attr_data.get('FTYPE_CODE','')}|{attr_data.get('USAGE_TYPE','')}"
        if segment_id not in self.attr_groups:
            self.attr_groups[segment_id] = [attr_data]
        else:
            self.attr_groups[segment_id].append(attr_data)

def fmt_source_node_id(src, id):
    if args.include_source_nodes:
        return f"{src}:{id}"
    return id

def export_nodes(senzing_graph, source_graph, entity_id, record_list):

    senzing_node_id = f"SENZING:{entity_id}"
    longest_primary_name = ''
    longest_other_name = ''
    entity_type_list = []
    count_by_data_source = {}
    for row in record_list:
        data_source = row['DATA_SOURCE']
        if data_source in count_by_data_source:
            count_by_data_source[data_source] += 1
        else:
            count_by_data_source[data_source] = 1
        record_id = row['RECORD_ID']
        record_node_id = fmt_source_node_id(data_source, record_id)
        match_key = row.get('MATCH_KEY', 'unknown')
        record_type = 'UNKNOWN'
        record_name = 'n/a'
        node_attrs = {}
        attr_list = json_parser.parse(row['JSON_DATA'])
        for attr_data in sorted(attr_list, key=itemgetter('ATTR_ID')):
            if attr_data['ATTRIBUTE'] in ('DATA_SOURCE', 'RECORD_ID', 'REL_ANCHOR', 'LOAD_ID'):
                continue

            if attr_data['ATTRIBUTE'] == 'REL_POINTER':
                if args.include_source_nodes:
                    # note: disclosed relations roles in Senzing should separate relationship type and details
                    # such as: "owned_by 50%". This makes graphs less messy and filtering easier!
                    # so everything before a space will be considered the type and the whole thing the details
                    related_record_id = attr_data['ATTR_VALUE']
                    role = attr_data['USAGE_TYPE'] if attr_data['USAGE_TYPE'] else 'RELATED_TO'
                    link = {'source': record_node_id,
                            'target': fmt_source_node_id(data_source, related_record_id),
                            'edge_class': 'Disclosed',
                            'edge_type': role.split()[0],
                            'edge_details': f"{data_source}: {role}",
                            'data_source': data_source}

                    # ensure related record exists (this could be optional to improve performance)
                    if sz_dbo.fetchNext(sz_dbo.sqlExec('select 1 from DSRC_RECORD where DSRC_ID = ? and RECORD_ID = ?', (row['DSRC_ID'], related_record_id))):
                        source_graph['links'].append(link)

            elif attr_data['ATTRIBUTE'] == 'RECORD_TYPE':
                record_type = attr_data['ATTR_VALUE']
                entity_type_list.append(record_type)

            else:
                if attr_data['ATTRIBUTE'] == 'NAME':
                    if attr_data.get('USAGE_TYPE') == 'PRIMARY':
                        record_name = attr_data['ATTR_VALUE']
                        longest_primary_name = attr_data['ATTR_VALUE'] if len(attr_data['ATTR_VALUE']) > len(longest_primary_name) else longest_primary_name
                    else:
                        longest_other_name = attr_data['ATTR_VALUE'] if len(attr_data['ATTR_VALUE']) > len(longest_other_name) else longest_other_name
                        if not record_name:
                            record_name = attr_data['ATTR_VALUE']

                attribute = (f"{attr_data['USAGE_TYPE']}_{attr_data['ATTRIBUTE']}" if attr_data.get('USAGE_TYPE') else attr_data['ATTRIBUTE']).lower()
                if node_attrs.get(attribute):
                    if not isinstance(node_attrs.get(attribute), list):
                        node_attrs[attribute] = [node_attrs[attribute]]
                    node_attrs[attribute].append(attr_data['ATTR_VALUE'])
                else:
                    node_attrs[attribute] = attr_data['ATTR_VALUE']

        if args.include_source_nodes:
            node = {'id': record_node_id,
                    'node_class': 'RECORD',
                    "node_type": record_type,
                    "node_name": record_name,
                    "data_source": data_source,
                    "record_id": record_id}
            node.update(node_attrs)
            source_graph['nodes'].append(node)

        link = {'source': record_node_id,
                'target': senzing_node_id,
                'edge_class': 'Resolved',
                'edge_type': 'Resolved to',
                'edge_details': "Use Senzing's whyRecordInEntity call to get current details"}
                # note could use match_key for edge_details but it gets out of date
        senzing_graph['links'].append(link)

    node = {'id': senzing_node_id,
            'node_class': 'ENTITY',
            "node_type": ', '.join(set(entity_type_list)),
            "node_name": longest_primary_name if longest_primary_name else longest_other_name,
            "entity_id": entity_id,
            "record_count": len(record_list),
            "data_sources": []}
    for data_source in count_by_data_source:
        node["data_sources"].append({data_source: count_by_data_source[data_source]})

    senzing_graph['nodes'].append(node)

def dbo_export(senzing_graph, source_graph):

    entity_start_time = time.time()
    get_records_sql = '''
        select
           reo.RES_ENT_ID,
           dr.DSRC_ID, 
           (select CODE from SYS_CODES_USED where CODE_ID = dr.DSRC_ID and CODE_TYPE='DATA_SOURCE') as DATA_SOURCE,
           dr.RECORD_ID,
           reo.MATCH_KEY,
           dr.JSON_DATA
        from RES_ENT_OKEY reo
        join OBS_ENT oe on oe.OBS_ENT_ID = reo.OBS_ENT_ID
        join DSRC_RECORD dr on dr.ENT_SRC_KEY = oe.ENT_SRC_KEY and dr.DSRC_ID = oe.DSRC_ID
        where reo.RES_ENT_ID between ? and ?
        order by reo.RES_ENT_ID;
        '''

    entity_count = 0
    chunk_size = 1000000
    beg_entity_id = 1
    end_entity_id = chunk_size

    logging.info('getting max entity_id ...')
    max_entity_id = sz_dbo.fetchNext(sz_dbo.sqlExec('select max(RES_ENT_ID) as MAX_ENTITY_ID from RES_ENT'))['MAX_ENTITY_ID']

    while True:
        logging.info(f"getting entities from {beg_entity_id} to {end_entity_id} ...")
        record_cursor = sz_dbo.fetchAllDicts(sz_dbo.sqlExec(get_records_sql, (beg_entity_id, end_entity_id)))

        for entity_records in groupby(record_cursor, key=itemgetter('RES_ENT_ID')):
            entity_count += 1
            if entity_count % 100000 == 0:
                elapsed = round((time.time() - entity_start_time) / 60, 1)
                logging.info(f"{entity_count:,} entities processed after {elapsed} minutes")

            export_nodes(senzing_graph, source_graph, entity_records[0], list(entity_records[1]))

        if end_entity_id >= max_entity_id:
            break

        beg_entity_id += chunk_size
        end_entity_id += chunk_size

    elapsed = round((time.time() - entity_start_time) / 60, 1)
    logging.info(f"{entity_count:,} entities processed after {elapsed} minutes, done!")

    relationship_start_time = time.time()
    relation_count = 0

    relation_query = '''
      select
        MIN_RES_ENT_ID as ENTITY_ID,
        MAX_RES_ENT_ID as RELATED_ENTITY_ID,
        MATCH_LEVELS as MATCH_LEVELS,
        MATCH_KEY
      from RES_RELATE where MATCH_LEVELS != '11'
      '''
    relation_cursor = sz_dbo.sqlExec(relation_query)
    record = sz_dbo.fetchNext(relation_cursor)
    while record:
        relation_count += 1
        if relation_count % 100000 == 0:
            elapsed = round((time.time() - relationship_start_time) / 60, 1)
            logging.info(f"{relation_count:,} relationships processed after {elapsed} minutes")

        if len(record['MATCH_LEVELS'].split(',')) > 1: # could 2 or 3 and 11 (we ignoring 11's disclosed relationships)
            record['MATCH_LEVELS'] = record['MATCH_LEVELS'].split(',')[0]
        link = {'source': f"SENZING:{record['ENTITY_ID']}",
                'target': f"SENZING:{record['RELATED_ENTITY_ID']}",
                'edge_class': 'Derived',
                'edge_type': {'2': 'Possible Match', '3': 'Possibly Related'}.get(record['MATCH_LEVELS'], 'Other'),
                'edge_details': remove_drs(record['MATCH_KEY'])}
        senzing_graph['links'].append(link)
        link['source'] = f"SENZING:{record['RELATED_ENTITY_ID']}"  # must point to each other to be bi-directional
        link['target'] = f"SENZING:{record['ENTITY_ID']}"
        senzing_graph['links'].append(link)

        record = sz_dbo.fetchNext(relation_cursor)

    elapsed = round((time.time() - relationship_start_time) / 60, 1)
    logging.info(f"{relation_count:,} relationships processed after {elapsed} minutes, done!")


def remove_drs(s):
    for ss in re.findall('\(.*?\)',s):
        s = s.replace(f"+REL_POINTER{ss}",'')
    return s


# ----------------------------------------
if __name__ == "__main__":

    argParser = argparse.ArgumentParser()
    argParser.add_argument('-o', '--output_path', help='Path to desired output files including base file name if desired as multiple files are created')
    #argParser.add_argument('-f', '--output_format', default='G', help='(G)raphml or (C)SV format, default is Graphml')
    argParser.add_argument('-S', '--include_source_nodes', action='store_true', default=False, help='Only resolved entity nodes and relationships are exported by default')
    argParser.add_argument('-D', '--debug', action='store_true', default=False, help='turn debug mode on')
    args = argParser.parse_args()

    loggingLevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d %I:%M', level=loggingLevel)

    if not args.output_path:
        logging.error('an output path is required')
        sys.exit(1)
    elif os.path.isdir(args.output_path) and args.output_path[-1] != os.path.sep:
        args.output_path += os.path.sep

    if os.getenv('SENZING_ENGINE_CONFIGURATION_JSON'):
        sz_config = os.getenv("SENZING_ENGINE_CONFIGURATION_JSON")
    elif os.getenv('SENZING_CONFIG_FILE'):
        try:
            from G2IniParams import G2IniParams
            iniParamCreator = G2IniParams()
            sz_config = iniParamCreator.getJsonINIParams(os.getenv('SENZING_CONFIG_FILE'))
        except Exception as ex:
            logging.error(ex)
            sys.exit(1)
    else:
        logging.error('Senzing environment not set')
        sys.exit(1)

    json_parser = json2attribute(sz_config)

    sz_dbo = sz_engine = None
    try:
        sz_dbo = G2Database(json.loads(sz_config)['SQL']['CONNECTION'])
    except Exception as ex:
        logging.error(f"Direct database access required: {ex}")
        sys.exit(1)

    # if not sz_dbo:
    #     try:
    #         from senzing import G2Engine, G2EngineFlags, G2Exception
    #         sz_engine = G2Engine()
    #         sz_engine.init('szGraphExport', sz_config, False)
    #     except G2Exception as ex:
    #         logging.error(f"Cannot initialize API: {ex}")
    #         sys.exit(1)

    proc_start_time = time.time()

    senzing_graph = {'directed': False,
                     'multigraph': False,
                     'graph': {},
                     'nodes': [],
                     'links': []}
    source_graph = None
    if args.include_source_nodes:  # source relationships are directed and there can be maultiple
        source_graph = {'directed': True,
                        'multigraph': True,
                        'graph': {},
                        'nodes': [],
                        'links': []}

    if sz_dbo:
        dbo_export(senzing_graph, source_graph)

    with open(args.output_path + 'senzing_graph.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(senzing_graph, indent=4))
    if args.include_source_nodes:
        with open(args.output_path + 'source_graph.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(source_graph, indent=4))

    logging.info(f"processed completed in {round((time.time() - proc_start_time) / 60, 1)} minutes")
    sys.exit(0)
