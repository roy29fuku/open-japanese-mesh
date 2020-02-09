from copy import deepcopy
from pathlib import Path
from typing import List


class MeshDictionary(object):
    def __init__(self, dict_name: str):
        self.dict_name = dict_name
        self.records = {}
        self.term2ids = {}
        self.id2terms = {}

    def __iter__(self):
        return iter(self.records)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, item):
        return self.records[item]

    def __repr__(self):
        lines = [
            'dictionary name: {}'.format(self.dict_name),
            '-- {:,} unique MeSH terms\t'.format(len(self.term2ids)),
            '-- {:,} unique MeSH IDs\t'.format(len(self.id2terms)),
        ]
        return '\n'.join(lines)

    def read(self, fp: Path):
        pass

    def make_dictionary(self):
        self.get_id2terms()
        self.get_term2ids()

    def get_id2terms(self):
        id2terms = {}
        for _id, v in self.records.items():
            terms = v['synonyms']
            terms.add(v['heading'])
            for term in terms:
                id2terms[_id] = id2terms.get(_id, set())
                id2terms[_id].add(term)
        self.id2terms = id2terms

    def get_term2ids(self):
        term2ids = {}
        for _id, v in self.records.items():
            terms = v['synonyms']
            terms.add(v['heading'])
            for term in terms:
                term2ids[term] = term2ids.get(term, set())
                term2ids[term].add(_id)
        self.term2ids = term2ids


class MeshDescriptor(MeshDictionary):
    dict_name = 'MeSH Descriptor'

    def __init__(self):
        super(MeshDescriptor, self).__init__(self.dict_name)
        self.records = {}
        self.id2term = {}
        self.term2id = {}

    def read(self, fp: Path):
        onerecord = {"tree": [], "synonyms": set(), "heading": "", "ui": ""}
        UI = ""
        lineno = 0
        with fp.open(encoding="utf-8") as f:
            for line in f:
                lineno += 1
                line = line.strip()
                if line == "":
                    continue
                elif line == "*NEWRECORD":
                    if UI:
                        self.records[UI] = deepcopy(onerecord)
                    onerecord = {"tree": [], "synonyms": set(), "heading": "", "ui": ""}
                    UI = ""
                elif " = " in line:
                    attr, value = line.split(" = ", 1)
                    if attr == "UI":
                        UI = value
                        onerecord["ui"] = value
                    elif attr == "MH":
                        onerecord["heading"] = value
                    elif attr in ["PRINT ENTRY", "ENTRY"]:
                        onerecord["synonyms"].add(value.split("|")[0])
                    elif attr == "MN":
                        onerecord["tree"].append(value)

                elif " =" in line:
                    continue
                else:
                    print("?", lineno, line)
        self.records[UI] = deepcopy(onerecord)
        self.make_dictionary()


class MeshSupplementary(MeshDictionary):
    dict_name = 'MeSH Supplementary'

    def __init__(self):
        super(MeshSupplementary, self).__init__(self.dict_name)
        self.records = {}
        self.id2term = {}
        self.term2id = {}

    def read(self, fp: Path):
        onerecord = {"map": [], "synonyms": set(), "heading": "", "ui": ""}
        UI = ""
        lineno = 0
        with fp.open(encoding="utf-8") as f:
            for line in f:
                lineno += 1
                line = line.strip()
                if line == "":
                    continue
                elif line == "*NEWRECORD":
                    if UI:
                        self.records[UI] = deepcopy(onerecord)
                    onerecord = {"map": [], "synonyms": set(), "heading": "", "ui": ""}
                    UI = ""
                elif " = " in line:
                    attr, value = line.split(" = ", 1)
                    if attr == "UI":
                        UI = value
                        onerecord["ui"] = value
                    elif attr == "NM":
                        onerecord["heading"] = value
                    elif attr in ["SY", "N1"]:
                        onerecord["synonyms"].add(value.split("|")[0])
                    elif attr == "HM":
                        onerecord["map"].append(value)

                elif " =" in line:
                    continue
                else:
                    print("?", lineno, line)
        self.records[UI] = deepcopy(onerecord)
        self.make_dictionary()


def combine_mesh(dict_list: List[MeshDictionary], dict_name: str=None):
    """
    複数の辞書を結合
    :param dict_list:
    :param dict_name:
    :return:
    """
    if dict_name is None:
        dict_name = ' + '.join([d.dict_name for d in dict_list])
    _dict = MeshDictionary(dict_name)
    _dict.records = {k: v for d in dict_list for k, v in d.records.items()}
    _dict.make_dictionary()
    return _dict
