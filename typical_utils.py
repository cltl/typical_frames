from lxml import etree
import numpy
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import operator
import pandas as pd
import requests
import json
from collections import defaultdict, Counter
import re

###GET FF-ICF PER EVENT TYPE###

def frames_naf_predicate(path_to_doc):
    """Load a NAF file, extract the frames from their predicate layers and add them to a list."""
    doc_tree = etree.parse(path_to_doc) #parse the NAF file
    root = doc_tree.getroot()
    frames = []

    if root.find('srl') in root:
        for predicate in root.find('srl'):
            ext_ref_el = predicate.find(‘externalReferences/externalRef’)
            uri = ext_ref_el.get(‘reference’)
            frames.append(uri) #append the frames to a list
    return frames

def frames_collection(collection):
    """returns a list of frames extracted from a collection of NAF files."""
    collection_frames = []

    for file in collection: #iterate over the filepaths in a list
        for frame in frames_naf_predicate(file): #iterate over the frames extracted from each NAF file
            collection_frames.append(frame) #append the frames to a list
    return collection_frames

def frames_collections(event_types,collection_of_collections):
    """returns a dictionary with the event type as key and list of frames as value"""
    event_type_frames_dict = {}

    for event_type, collection in zip(event_types, collection_of_collections): #iterate over each event type and the corresponding list of sets of filepaths
        event_type_frames_dict[event_type] = frames_collection(collection) #add each event type and the corresponding list of frames as key-value pairs to a dictionary
    return event_type_frames_dict

def contrastive_analysis(event_type_frames_dict):
    """returns a dictionary with event type as key and a sorted list of frames and their tf-idf values"""
    lists_frames = []

    for key in event_type_frames_dict: #iterate over the key:value (event type:list of frames) pairs
        values = event_type_frames_dict[key] #create a variable for each list of frames
        space = ' '
        space = space.join(values) #join the frames
        lists_frames.append(space) #append the string to a list

    vectorizer = CountVectorizer() #frame vocabulary
    lists_vector_data = vectorizer.fit_transform(lists_frames) #data structure that represents the instances through their vectors
    column_headers = vectorizer.get_feature_names() #frame vocabulary mapped to data columns
    tfidf_transformer = TfidfTransformer()
    lists_frames_tfidf = tfidf_transformer.fit_transform(lists_vector_data)
    tf_idf_array = lists_frames_tfidf.toarray() #apply tf-idf
    tf_idf_array_round = numpy.round(tf_idf_array, decimals=3)

    tf_idf_dict = {}

    for key, array in zip(event_type_frames_dict, tf_idf_array): #iterate over the event types and the list of corresponding arrays of tf-idf values
        frame_valuedict = {}
        for frame, value in zip(column_headers, array): #iterate over each frame and its corresponding value
            frame_valuedict[frame] = value #add the frame and value as key-value pair to a dictionary
        sorted_tuples = sorted(frame_valuedict.items(), key=operator.itemgetter(1), reverse=True) #convert the dictionary to a list of tuples sorted in descending order of the values
        tf_idf_dict[key] = sorted_tuples #add the event type and its list of tuples as a key-value pair to the tf_idfdict
    return tf_idf_dict

def output_tfidf_to_format(tf_idf_dict):
    """exports the output of the tf-idf analysis to an excel format"""
    headers = ['event type', 'rank', 'frame', 'tf-idf value', 'judgement']
    list_of_lists = []

    for key in tf_idf_dict: #iterate over the tf-idf dictionary
        for tupl, number in zip(tf_idf_dict[key][:40], range(1,41)): #iterate over n tuples and corresponding range of numbers
                one_row = [key, number] #create a list with the event type and the number of each tuple
                for element in tupl: #iterate over the frame and its tf-idf value of each tuple
                    one_row.append(element) #append both elements to the list
                one_row.append('') #append placeholder for validation
                list_of_lists.append(one_row) #append the list to a list of lists

    df = pd.DataFrame(list_of_lists, columns=headers) #turn the list into a table

    df.to_excel('tf_idf.xlsx', index=False) #export the table to an excel file

def validation_to_json(tf_idf_dict, output_path):
    """exports the tf-idf dictionary to json with validation of typical frames"""
    typical_frame_dict = {}

    for key, value in tf_idf_dict.items(): #iterate over the key/value pairs of the tf_idf dictionary
        typical = []
        other = []
        for frame in value[:10]: #iterate over the first n tuples in the list
            typical.append(frame[0]) #append the frame of each tuple to a list
        for frame in value[10:]: #iterate over the rest of the tuples in the list
            other.append(frame[0]) #append the frame of each tuple to another list
        validation_dict = {'typical': typical, 'other': other} #create dictionary with both lists as values
        typical_frame_dict[key] = validation_dict #add the dictionary to typical_frame_dict with event types as keys

    with open(output_path, 'w') as outfile:
        json.dump(typical_frame_dict, outfile, indent=4, sort_keys=True)

### CONVERT WIKIDATA IDENTIFIER TO ENTITY NAME ###

def get_entity_name(identifier):
    """returns name of the event type for a given identifier in wikidata"""
    r = requests.get(f"https://www.wikidata.org/entity/{identifier}.json")
    data = json.loads(r.text)
    return data["entities"][identifier]["labels"]["en"]["value"]

def get_entity_list(event_types):
    """returns a list with the wikidata identifiers converted to their entity name"""
    entity_list = []

    for identifier in event_types:
        entity = get_entity_name(identifier)
        entity_list.append(entity)
    return entity_list
