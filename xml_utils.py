import os
from lxml import etree
from collections import defaultdict

def get_text_title(root):
    """extract text title from NAF"""
    target = root.find('nafHeader/fileDesc')
    title = target.get('title')
    return title

def srl_id_frames(root):
    """Load a NAF file, extract the frames and their corresponding identifiers and add them to a dictionary."""
    framedict = {}

    if root.find('srl') in root:
        for predicate in root.find('srl'):
            ext_ref_el = predicate.find('externalReferences/externalRef')
            uri = ext_ref_el.get('reference')
            frame = uri[35:]
            label = frame[0].upper() + frame[1:]
            target = predicate.find('span/target')
            id = target.get('id')
            framedict[id] = label
    return framedict

def term_id_lemmas(root):
    """load a NAF file, extract the term id and corresponding lemma, POS and wf and add them to a dictionary."""
    lemmadict = {}

    if root.find('terms') in root:
        for term in root.find('terms'):
            term_id = term.get('id')
            lemma = term.get('lemma')
            pos = term.get('pos')
            target = term.find('span/target')
            target_id = target.get('id')
            lemmapos = {"lemma": lemma, "POS": pos, "wf": target_id}
            lemmadict[term_id] = lemmapos
    return lemmadict

def sentence_info(root):
    """Load a NAF file, extract the sentence ids with corresponding wfs and add them to a dictionary."""
    sentencedict = defaultdict(set)

    if root.find('text') in root:
        for term in root.find('text'):
            sentence = term.get('sent')
            wf = term.get('id')
            sentencedict[sentence].add(wf)
    return sentencedict

def compound_id_info(root):
    """load a NAF file, extract info about compounding."""
    compounddict = {}

    if root.find('deps') in root:
        for dep in root.find('deps'):
            if dep.get('rfunc') == "compound":
                head_id = dep.get('from')
                modifier_id = dep.get('to')
                compounddict[head_id] = {"component": 'head', "modifier id": modifier_id}
                compounddict[modifier_id] = {"component": 'modifier', "head id": head_id}
    return compounddict

def determiner_id_info(root):
    """load a NAF file, extract info about determiners"""
    detdict = {}

    if root.find('deps') in root:
        for dep in root.find('deps'):
            if dep.get('rfunc') == "det":
                det_id = dep.get("to")
                predicate_id = dep.get("from")
                detdict[predicate_id] = {"det id": det_id}
    return detdict

def frame_info_dict(title,
                    framedict,
                    lemmadict,
                    sentencedict,
                    detdict,
                    compounddict):
    """integrate different dictionaries extracted from naf in order to create a frame_info_dict"""
    frame_info_dict = {}
    id_info_dict = {}
    term_id_dict = {}
    frame_freq_dict = {}
    counter = 0

    for term_id in framedict:
        counter += 1
        if term_id in lemmadict:
            frame = framedict[term_id]
            lemma = lemmadict[term_id]['lemma']
            pos = lemmadict[term_id]['POS']
            wf = lemmadict[term_id]['wf']
            info_dict = {"frame": frame, "lemma": lemma, "POS": pos}
            for sentence, words in sentencedict.items():
                if wf in words:
                    info_dict['sentence'] = sentence
        if term_id in detdict:
            det_id = detdict[term_id]['det id']
            if det_id in lemmadict and (lemmadict[det_id]['lemma'] == 'an' or lemmadict[det_id]['lemma'] == 'a' or lemmadict[det_id]['lemma'] == 'the'):
                article = lemmadict[det_id]['lemma']
                if article == 'a' or article == 'an':
                    definite_dict = {"definite": False, "lemma": article}
                    info_dict['article'] = definite_dict
                else:
                    definite_dict = {"definite": True, "lemma": article}
                    info_dict['article'] = definite_dict
            else:
                info_dict['article'] = {"definite": None, "lemma": None}
        else:
            info_dict['article'] = {"definite": None, "lemma": None}

        if term_id in compounddict:
            if compounddict[term_id]['component'] == 'head':
                modifier_id = compounddict[term_id]['modifier id']
                if modifier_id in lemmadict:
                    modifier = lemmadict[modifier_id]['lemma']
                if term_id in lemmadict:
                    head = lemmadict[term_id]['lemma']
                    compound = f"{modifier} {head}"
                    info_dict["compound"] = {"function": "head", "lemma": compound}
            if compounddict[term_id]['component'] == 'modifier':
                head_id = compounddict[term_id]['head id']
                if head_id in lemmadict:
                    head = lemmadict[head_id]['lemma']
                if term_id in lemmadict:
                    modifier = lemmadict[term_id]['lemma']
                    compound = f"{modifier} {head}"
                    info_dict["compound"] = {"function": "modifier", "lemma": compound}
        else:
            info_dict["compound"] = {"function": None, "lemma": None}
        id_info_dict[term_id] = info_dict

    frame_info_dict[title] = {'frame frequency': counter, 'frame info': id_info_dict}
    return frame_info_dict
