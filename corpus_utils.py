import json
import os
import shutil
import random

def delete_smallest_texts(collections, minimal_n_frames, verbose):
    """
    load the event_type_info_dict and delete the smallest texts.
    :param collections: collection of collections of dictionaries per event type
    :param minimal_n_frames: filter of minimum number of annotated frames in a text
    :type collections: dictionary
    :type minimal_n_frames: integer
    """
    sliced_corpus = {}
    count = 0
    for event_type, events in collections.items():
        new_list = []
        for event in events:
            for title, stats in event.items():
                if stats['frame frequency'] >= minimal_n_frames:
                    new_list.append(event)
                else:
                    count += 1
                    continue
        assert len(new_list) != 0, "no documents containing more frames than provided threshold"
        sliced_corpus[event_type] = new_list
    if verbose >= 1:
        print(f"{count} texts with less than {minimal_n_frames} frames removed")
    return sliced_corpus

def create_output_folder(output_folder, start_from_scratch, verbose):
    '''creates output folder for export dataframe'''
    if os.path.isdir(output_folder):
        if start_from_scratch == True:
            shutil.rmtree(output_folder)
            if verbose >= 1:
                print(f"removed existing folder {output_folder}")

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
        if verbose >= 1:
            print(f"created folder at {output_folder}")

def corpus_to_json(corpus_dict, output_folder, start_from_scratch, verbose):
    """export loaded and sliced corpus to json"""
    if output_folder != None:
        create_output_folder(output_folder=output_folder,
                            start_from_scratch=start_from_scratch,
                            verbose=verbose)
        json_path = f'{output_folder}/corpus_info.json'
        with open(json_path, 'w') as outfile:
            json.dump(corpus_dict, outfile, indent=4, sort_keys=True)

        if verbose >= 1:
            print(f"loaded and sliced corpus exported to {json_path}")

def select_event_types(event_types, corpus_dict, verbose):
    """create new dictionary with selected event types of corpus_dict"""
    event_type_info_dict = {}

    for identifier in event_types:
        assert identifier in corpus_dict, f"{identifier} not in corpus"

    for event_type, info in corpus_dict.items():
        if event_type in event_types:
            event_type_info_dict[event_type] = info

    assert len(event_type_info_dict) == len(event_types), "list of event types not represented in selected corpus"
    return event_type_info_dict

def sample_corpus(collections, verbose):
    """
    create proportional sizes of subcorpora across event types. randomize when selecting the texts for this sample.
    :param collections: collection of collections of dictionaries per event type
    :type collections: dictionary
    """
    lengths_dict = {}

    for event_type, info_dicts in collections.items():
        lengths_dict[event_type] = len(info_dicts)

    len_smallest_corpus = min(lengths_dict.values())
    sampled_collections = {}

    for event_type, info_dicts in collections.items():
        sampled_list = random.sample(info_dicts, len_smallest_corpus)
        sampled_collections[event_type] = sampled_list

    if verbose >= 3:
        for event_type, info in sampled_collections.items():
            print(f"{event_type}: {len(info)} sampled reference texts")

    return sampled_collections
