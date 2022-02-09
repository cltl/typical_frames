import numpy as np
import operator
import os
import random
import statistics
import math
import json
import shutil
import pandas as pd
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

def frames_from_dict(frame_info_dict):
    """
    Load a naf dictionary, extract the frames and add them to a list.
    :param frame_info_dict: dictionary with linguistic information extracted from NAF file
    :type frame_info_dict: dictionary
    """
    frames = []

    for title, info in frame_info_dict.items():
        for term_id, term_info in info['frame info'].items():
            frame = term_info["frame"]
            frames.append(frame)
    return frames

def frames_collection(collection):
    """
    returns a list of frames extracted from a collection of NAF files.
    :param collection: collection of dictionaries with relevant info extracted from NAF files
    :param collection: list
    """
    collection_frames = []

    for info_dict in collection:
        for frame in frames_from_dict(info_dict):
            collection_frames.append(frame)
    return collection_frames

def frames_collections(event_type_frame_collections, verbose):
    """
    returns a dictionary with the event type as key and list of frames as value
    :param event_type_frame_collections: collection of collections of event types with corresponding dictionaries for NAF files
    :type event_type_frame_collections: dictionary
    """
    event_type_frames_dict = {}

    for event_type, collection in event_type_frame_collections.items():
        event_type_frames_dict[event_type] = frames_collection(collection)

    if verbose >= 2:
            for event_type, frames in event_type_frames_dict.items():
                print(f'{event_type}: {len(frames)} frames')
    return event_type_frames_dict

def frame_stats(event_type_frames_dict,verbose):
    """
    returns a dictionary with event type as key and a dictionary with (relative) frequency for each frame as value
    :param event_type_frames_dict: dictionary with for each event type a list of corresponding frames
    :type event_type_frame_dict: dictionary
    """
    event_type_frame_freq_dict = {}

    for key in event_type_frames_dict:
        assert type(event_type_frames_dict[key]) == list, "no list of frames"
        frame_stats_dict = {}
        frames = event_type_frames_dict[key]
        assert len(frames) != 0, "no frames in list"
        count_dict = Counter(frames)
        for frame, freq in count_dict.items():
            relative_freq = (freq/len(frames))*100
            info_dict = {'absolute frequency': freq, 'relative frequency': relative_freq}
            frame_stats_dict[frame] = info_dict
        event_type_frame_freq_dict[key] = frame_stats_dict
    return event_type_frame_freq_dict

def split_on_space(text):
    """
    split text on spaces.
    :param text: the text that needs to be tokenized
    :type text: string
    """
    return text.split(' ')

def c_tf_idf(frame_freq_event_type, total_freq_frames_event_type, total_n_docs, frame_freq_event_types):
    """
    calculates c_tf_idf for a frame in a given matrix.
    :param frame_freq_event_type: the number of occurences of the frame in the event type
    :param total_freq_frames_event_type: the total number of all frame occurrences in the event type
    :param total_n_docs: the total number of documents across event types
    :param frame_freq_event_types: the number of occurences of the frame across event types
    :type frame_freq_event_type: integer
    :type total_freq_frames_event_type: integer
    :type total_n_docs: integer
    :type frame_freq_event_types: integer
    """
    tf = frame_freq_event_type/total_freq_frames_event_type
    idf_array = np.log(np.divide(total_n_docs, frame_freq_event_types)).reshape(-1,1)
    idf = idf_array[0][0]
    c_tf_idf = tf*idf
    return c_tf_idf

def normalize_data(data):
    the_array = (data - np.min(data)) / (np.max(data) - np.min(data))
    return list(the_array)

def ff_icf(collections, event_type_frames_dict, frame_freq_dict, verbose):
    """
    calculates ff_icf scores.
    :param collections: collection of collections of event types with corresponding dictionaries with linguistc NAF info
    :param event_type_frames_dict: dictionary with event types: list of frames
    :param frame_freq_dict: absolute and relative frequency per frame per event type
    :type collections: dictionary
    :type event_type_frames_dict: dictionary
    :type frame_freq_dict: dictionary
    """
    total_n_docs = 0 #total number of documents

    for event_type, info in collections.items(): #iterate over event type: list of info-dictionaries
        total_n_docs += len(info) #add the length of the list (equal to the number of texts) to counter

    lists_frames = []

    for key in event_type_frames_dict: #iterate over the key:value (event type:list of frames) pairs
        values = event_type_frames_dict[key] #create a variable for each list of frames
        assert type(values) == list, "no list of frames"
        assert len(values) != 0, "no frames in list"
        space = ' '
        space = space.join(values) #join the frames
        lists_frames.append(space) #append the string to a list. this results in a list with a joined string of frames per event type

    vectorizer = CountVectorizer(lowercase=False, analyzer=split_on_space)
    frames_vector_data = vectorizer.fit_transform(lists_frames) #vectorize the frames per event type
    vector_shape = frames_vector_data.shape
    column_headers = vectorizer.get_feature_names() #get the matrix's columnh headers
    assert vector_shape[0] == len(collections), "not all event types are represented in matrix"
    assert vector_shape[1] == len(column_headers), "not all frames are represented in matrix"
    frames_vector_array = frames_vector_data.toarray()
    list_of_lists = []

    for row in frames_vector_array: #iterate over the vectors
        assert len(row) == len(column_headers), "certain frames in column headers not represented in vector"
        total_freq_frames_event_type = sum(row) #create variable for the sum of all frames of the event type
        scores = []
        for frame_freq_event_type, frame in zip(row, column_headers): #iterate over both the absolute frequencies in the vector and the corresponding column headers
            frame_freq_event_types = 0
            for event_type, freq_dict in frame_freq_dict.items(): #iterate over event_type:dictionary with frequencies
                if frame in freq_dict: #if the frame is in the dictionary of the event type
                    frame_freq_event_types += freq_dict[frame]['absolute frequency'] #add the absolute frequency to counter
            assert frame_freq_event_types != 0, f"{frame} not in corpus"
            c_tf_idf_score = c_tf_idf(frame_freq_event_type, total_freq_frames_event_type, total_n_docs, frame_freq_event_types)
            #if c_tf_idf_score < 0:
            #    c_tf_idf_score = 0
            scores.append(c_tf_idf_score) #append the score to a list
        normalized_scores = normalize_data(scores)
        list_of_lists.append(normalized_scores) #append the list to another list. The result is a list of scores per each event type

    c_tf_idf_round = np.round(list_of_lists, decimals=6)
    assert len(c_tf_idf_round) == len(collections), "not all event types are represented as list with c-tf-idf scores"
    c_tf_idfdict = {}

    for event_type, array in zip(event_type_frames_dict, c_tf_idf_round): #iterate over the event types and the list of corresponding arrays of tf-idf values
        frame_valuedict = {}
        for frame, value in zip(column_headers, array): #iterate over each frame and its corresponding value
            frame_valuedict[frame] = value #add the frame and value as key-value pair to a dictionary
        sorted_tuples = sorted(frame_valuedict.items(), key=operator.itemgetter(1), reverse=True) #convert the dictionary to a list of tuples sorted in descending order of the values
        assert len(sorted_tuples) == len(column_headers), "not all frames across event types have a c-tf-idf score in event type"
        c_tf_idfdict[event_type] = sorted_tuples #add the event type and its list of tuples as a key-value pair to the tf_idfdict

    if verbose >= 3:
        for event_type, scores in c_tf_idfdict.items():
            print(f'{event_type}: top ranking: {scores[:3]}')
            print(f'{event_type}: bottom ranking: {scores[-3:]}')
    return c_tf_idfdict

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

def scores_to_format(fficf_dict, frame_freq_dict, output_folder, start_from_scratch, event_types, verbose):
    """exports the output of the ff*icf analysis to an excel format"""
    headers = ['event type', 'rank', 'frame', 'ff*icf value', 'absolute freq', 'relative freq', 'judgement']
    list_of_lists = []

    for key in fficf_dict:
        cutoff_point = len(fficf_dict[key])
        break

    for key in fficf_dict:
        for tupl, number in zip(fficf_dict[key][:cutoff_point], range(1,(cutoff_point+1))):
            one_row = [key, number]
            frame = tupl[0]
            score = tupl[1]
            one_row.append(frame)
            one_row.append(score)
            if frame in frame_freq_dict[key]:
                abs_freq = frame_freq_dict[key][frame]['absolute frequency']
                rel_freq = frame_freq_dict[key][frame]['relative frequency']
            else:
                abs_freq = 0
                rel_freq = 0
            one_row.append(abs_freq)
            one_row.append(rel_freq)
            one_row.append('')
            list_of_lists.append(one_row)

    df = pd.DataFrame(list_of_lists, columns=headers)

    if output_folder != None:
        create_output_folder(output_folder=output_folder,
                            start_from_scratch=start_from_scratch,
                            verbose=verbose)
        if event_types != None:
            identifiers = "_".join(event_types)
            xlsx_path = f"{output_folder}/typicality_scores_{identifiers}.xlsx"
        df.to_excel(xlsx_path, index=False)
        if verbose:
            print(f"exported typicality scores to {xlsx_path}")
    return

def scores_to_json(fficf_dict, output_folder, start_from_scratch, verbose):
    """exports the output of the ff-icf analysis to a json format per event type"""
    json_dict = {}

    for key in fficf_dict:
        scores_dict = {}
        for tupl in fficf_dict[key]:
            frame = tupl[0].lower()
            premon_frame = "http://premon.fbk.eu/resource/fn17-"+frame
            score = tupl[1]
            scores_dict[premon_frame] = score
        if output_folder != None:
            create_output_folder(output_folder=output_folder,
                                start_from_scratch=start_from_scratch,
                                verbose=verbose)
            json_path = f"{output_folder}/typicality_scores_{key}.json"
            with open(json_path, 'w') as outfile:
                json.dump(scores_dict, outfile, indent=4, sort_keys=True)
            if verbose:
                print(f"exported typicality scores to {json_path}")
    return


###other possibly useful functions###

def top_n_frames(typicality_scores, top_n_typical_frames, verbose=0):
    if top_n_typical_frames == 'all':
        the_target_frames = list(typicality_scores)
    else:
        the_target_frames = []

        n = 0
        for frame_label, typ_score in sorted(typicality_scores.items(),
                                             key=operator.itemgetter(1),
                                             reverse=True):
            the_target_frames.append(frame_label)

            n += 1
            if n == top_n_typical_frames:
                break

        assert len(the_target_frames) == top_n_typical_frames

    if verbose >= 5:
        print()
        print(f'selected {len(the_target_frames)} from total of {len(typicality_scores)} frames')
        print(f'first three are: {the_target_frames[:3]}')

    return the_target_frames

def get_time_bucket_to_frame_to_freq(big_df,
                                     target_frames=None):

    the_time_buckets = set(big_df['time bucket'])
    time_bucket_to_frame_to_freq = {}
    frame_to_freq = defaultdict(int)
    time_bucket_to_total_frame_occurrences = defaultdict(int)

    for time_bucket in the_time_buckets:
        time_bucket_df = big_df[big_df['time bucket'] == time_bucket]
        time_bucket_to_frame_to_freq[time_bucket] = {}

        for frame_label in time_bucket_df.columns:
            if frame_label != 'time bucket':

                if target_frames:
                    if frame_label not in target_frames:
                        continue

                total = sum(time_bucket_df[frame_label])
                time_bucket_to_frame_to_freq[time_bucket][frame_label] = total
                frame_to_freq[frame_label] += total
                time_bucket_to_total_frame_occurrences[time_bucket] += total

    return time_bucket_to_frame_to_freq, frame_to_freq, time_bucket_to_total_frame_occurrences

def compute_c_tf_idf_between_time_buckets(typicality_scores,
                                          train_df,
                                          dev_df,
                                          test_df,
                                          top_n_typical_frames,
                                          verbose=0):
    the_target_frames = top_n_frames(typicality_scores=typicality_scores,
                                     top_n_typical_frames=top_n_typical_frames,
                                     verbose=verbose)

    the_big_df = pd.concat([train_df,
                                dev_df,
                                test_df], axis=0)


    # time_bucket -> frame -> frequency
    # total frequency of a frame across time buckets
    # total number of frame occurrences per time bucket
    time_bucket_to_frame_to_freq,\
    frame_to_freq, \
    time_bucket_to_total_frame_occurrences = get_time_bucket_to_frame_to_freq(big_df=the_big_df,
                                                                              target_frames=the_target_frames)


    # total number of docs
    number_of_docs = len(the_big_df)

    list_of_lists = []
    headers = ['time bucket', 'frame', 'c_tf_idf']

    for time_bucket, tb_frame_to_freq in time_bucket_to_frame_to_freq.items():

        for frame, tb_freq in tb_frame_to_freq.items():

            c_tf_idf_score = c_tf_idf(frame_freq_event_type=tb_freq,
                                      total_freq_frames_event_type=time_bucket_to_total_frame_occurrences[time_bucket],
                                      total_n_docs=number_of_docs,
                                      frame_freq_event_types=frame_to_freq[frame])
            one_row = [time_bucket, frame, c_tf_idf_score]
            list_of_lists.append(one_row)


    c_tf_idf_df = pd.DataFrame(list_of_lists, columns=headers)
    return c_tf_idf_df
