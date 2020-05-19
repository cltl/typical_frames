"""
Typical frame detection

python typical_frames.py --path_config_json=<path_config_json> --verbose=<verbose>

Usage:
  typicalframes.py --path_config_json=<path_config_json> --verbose=<verbose>

Options:
    --path_config_json=<path_config_json> e.g., ../config/v0.json
    --verbose=<verbose> 0 nothing, 1 descriptive stats, 2 debugging information

Example:
    python typical_frames.py --path_config_json="../config/v0.json" --verbose="2"
"""
import sys
import pickle
import json
import os
from docopt import docopt

# load arguments
arguments = docopt(__doc__)
print()
print('PROVIDED ARGUMENTS')
print(arguments)
print()

from typical_utils import frames_naf_predicate, frames_collection, frames_collections, contrastive_analysis, output_tfidf_to_format, get_entity_name, get_entity_list, validation_to_json

sys.path.append('../../')

settings_path = arguments['--path_config_json']
settings = json.load(open(settings_path))

ev_type_coll_path = settings['paths']['wd_representation_with_mwep']
ev_type_coll = pickle.load(open(ev_type_coll_path,
                                'rb'))

event_types = settings['event_types']
wiki_output_dir = settings['paths']['data_release_naf_folder']
json_out = settings['paths']['typical_frames_path']

frame_to_info_path = os.path.join(settings['paths']['lexicon_data'], 'frame_to_info.json')
frame_to_info = json.load(open(frame_to_info_path))

set_of_paths_per_event_type = []

for event_type in event_types:
    naf_paths = ev_type_coll.get_paths_of_reftexts_of_one_event_subgraph(f'http://www.wikidata.org/entity/{event_type}',
                                                                        wiki_output_dir,
                                                                         verbose=1)
    set_of_paths_per_event_type.append(naf_paths) #create a list of sets with each set containing the naf_paths for an event_type

#entity_list = get_entity_list(event_types)

event_type_frames_dict = frames_collections(event_types, set_of_paths_per_event_type, frame_to_info)
tf_idf_dict = contrastive_analysis(event_type_frames_dict)
validation_to_json(tf_idf_dict, json_out)
