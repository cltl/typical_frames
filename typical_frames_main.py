from .xml_utils import srl_id_frames, term_id_lemmas, determiner_id_info, compound_id_info, get_text_title, frame_info_dict, sentence_info
from .path_utils import get_naf_paths
from .corpus_utils import delete_smallest_texts, corpus_to_json, select_event_types, sample_corpus
from .fficf_utils import frames_collections, frame_stats, ff_icf, scores_to_format, scores_to_json

from lxml import etree
import json
import os
import pandas as pd

def frame_info(naf_root,
                verbose=0):
    '''
    extracts dictionary from naf with relevant info about frames and their lexical units.
    :param naf_iterable: path to naf iterable
    :type naf_iterable: string
    '''
    doc_tree = etree.parse(naf_root)
    root = doc_tree.getroot()

    title = get_text_title(root)
    framedict = srl_id_frames(root)
    lemmadict = term_id_lemmas(root)
    sentencedict = sentence_info(root)
    detdict = determiner_id_info(root)
    compounddict = compound_id_info(root)

    frame_info = frame_info_dict(title=title,
                                    framedict=framedict,
                                    lemmadict=lemmadict,
                                    sentencedict=sentencedict,
                                    detdict=detdict,
                                    compounddict=compounddict)
    if verbose >= 2:
        print(frame_info)
    return frame_info

def event_type_info(collections,
                verbose=0):
    """
    Returns a dictionary with event type as key and list of dictionaries with linguistic information as value.
    :param collections: a collection of collections of NAF paths per event type
    :type collections: dictionary
    """
    event_type_frame_info_dict = {}

    for event_type, collection in collections.items():
        collection_of_dicts = []
        for file in collection:
            frame_info_dict = frame_info(file)
            collection_of_dicts.append(frame_info_dict)
        event_type_frame_info_dict[event_type] = collection_of_dicts
    return event_type_frame_info_dict

def load_corpus(project,
                language,
                output_folder=None,
                minimal_frames_per_doc=10,
                start_from_scratch=True,
                verbose=0):
    """
    load the corpus from DFNDataReleases and distribute the linguistic information from the naf files
    over event types in dictionary.
    :param project: the name of the project under which the corpus in DFNDataReleases is stored
    :param language: the language of the corpus
    :param output_folder: output folder
    :param minimal_frames_per_doc: the minimal number of annotated frames a document must contain
    :param start_from_scratch: start from scratch
    :type project: string
    :type language: string
    :type output_folder: string
    :type minimal_frames_per_doc: integer
    :type start_from_scratch: boolean
    """
    event_type_paths_dict = get_naf_paths(project=project,
                                        language=language,
                                        verbose=verbose)
    event_type_info_dict = event_type_info(collections=event_type_paths_dict)
    sliced_corpus = delete_smallest_texts(collections=event_type_info_dict,
                                            minimal_n_frames=minimal_frames_per_doc,
                                            verbose=verbose)

    if verbose >= 2:
        for event_type, collection in sliced_corpus.items():
            print(f'{event_type}: {len(collection)} reference texts')

    corpus_to_json(corpus_dict=sliced_corpus,
                    output_folder=output_folder,
                    start_from_scratch=start_from_scratch,
                    verbose=verbose)
    return

def contrastive_analysis(event_types=None,
                            output_folder=None,
                            start_from_scratch=False,
                            verbose=2):
    """
    Extract frames from corpus per event type, perform ff*icf and return a dataframe in excel and json.
    :param event_types: specified wikidata event type identifiers
    :param output_folder: output folder
    :param start_from_scratch: start from scratch
    :type event_types: list
    :type output_folder: string
    :type start_from_scratch: boolean
    """
    assert type(event_types) == list, "event type identifiers are not in list"
    assert len(event_types) >= 2, "provide at least two identifiers in the event types list"

    corpus_path = f"{output_folder}/corpus_info.json"
    assert os.path.isfile(corpus_path) == True, "corpus not found"

    with open(corpus_path, "r") as infile:
        corpus_dict = json.load(infile)

    if event_types!= None:
        event_type_info_dict = select_event_types(event_types=event_types,
                                                    corpus_dict=corpus_dict,
                                                    verbose=verbose)
    else:
        event_type_info_dict = corpus_dict

    sampled_corpus = sample_corpus(collections=event_type_info_dict,
                                    verbose=verbose)
    event_type_frames_dict = frames_collections(event_type_frame_collections=sampled_corpus,
                                                verbose=verbose)
    frame_freq_dict = frame_stats(event_type_frames_dict=event_type_frames_dict,
                                    verbose=verbose)
    fficf_dict = ff_icf(collections=sampled_corpus,
                        event_type_frames_dict=event_type_frames_dict,
                        frame_freq_dict=frame_freq_dict,
                        verbose=verbose)
    scores_to_format(fficf_dict=fficf_dict,
                        frame_freq_dict=frame_freq_dict,
                        output_folder=output_folder,
                        start_from_scratch=start_from_scratch,
                        event_types=event_types,
                        verbose=verbose)
    scores_to_json(fficf_dict=fficf_dict,
                    output_folder=output_folder,
                    start_from_scratch=start_from_scratch,
                    verbose=verbose)
    return
