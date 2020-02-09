import csv
from pathlib import Path
from typing import List

from cnorm.chain import Chain

from utils.mesh import MeshDictionary


class WordPair(object):
    def __init__(self, word_en, word_ja):
        self.word_en = word_en
        self.word_ja = word_ja


class Dictionary(object):
    def __init__(self, dict_name: str):
        self.dict_name = dict_name
        self.word_pairs = []
        self.ja = {}
        self.en = {}

    def __iter__(self):
        return iter(self.word_pairs)

    def __len__(self):
        return len(self.word_pairs)

    def __getitem__(self, item):
        return self.word_pairs[item]

    def __repr__(self):
        lines = [
            'dictionary name: {}'.format(self.dict_name),
            '-- {:,} word pairs'.format(len(self)),
            '---- {:,} unique English words\t'.format(len(self.en)),
            '---- {:,} unique Japanese words\t'.format(len(self.ja)),
        ]
        return '\n'.join(lines)

    def read(self, fp: Path):
        pass

    def make_dictionary(self):
        """
        日英, 英日辞書を作成
        :return:
        """
        # for word_pair in self.word_pairs:
        #     word_ja = word_pair.word_ja
        #     word_en = word_pair.word_en
        #     self.ja.setdefault(word_ja, {
        #         'names_en': set(),
        #         'mesh_ids': set(),
        #     })
        #     self.ja[word_ja]['names_en'].add(word_en)
        #     self.en.setdefault(word_en, {
        #         'names_ja': set(),
        #         'mesh_ids': set(),
        #     })
        #     self.en[word_en]['names_ja'].add(word_ja)

        ja, en = {}, {}
        for word_pair in self.word_pairs:
            word_ja = word_pair.word_ja
            word_en = word_pair.word_en
            ja.setdefault(word_ja, {
                'names_en': set(),
                'mesh_ids': set(),
            })
            ja[word_ja]['names_en'].add(word_en)
            en.setdefault(word_en, {
                'names_ja': set(),
                'mesh_ids': set(),
            })
            en[word_en]['names_ja'].add(word_ja)
        sorted_ja = {}
        for k, v in sorted(ja.items(), key=lambda x: x[0]):
            sorted_ja[k] = v
        sorted_en = {}
        for k, v in sorted(en.items(), key=lambda x: x[0]):
            sorted_en[k] = v
        self.ja = sorted_ja
        self.en = sorted_en


    def initiate(self):
        """
        MeSH IDとの紐付きを初期化
        :return:
        """
        for val in self.en.values():
            val['mesh_ids'] = set()
        for val in self.ja.values():
            val['mesh_ids'] = set()

    def map_mesh(self, mesh_dict: MeshDictionary, chain: Chain=None):
        """日英, 英日辞書の英語と一致するMeSH termを探し、MeSH IDを紐づける
        chainを渡した場合、順にcnormのRuleを適用した状態での文字列比較になる
        :param mesh_dict:
        :return:
        """
        # en, jaに対するmesh_idsの紐付きを初期化
        self.initiate()

        if chain is None:
            chain = Chain()

        en_conv2org = {}
        for word_en in self.en.keys():
            word_en_conv = chain.apply(word_en)
            en_conv2org.setdefault(word_en_conv, set())
            en_conv2org[word_en_conv].add(word_en)

        for term, ids in mesh_dict.term2ids.items():
            term_conv = chain.apply(term)
            if term_conv not in en_conv2org:
                continue
            for en_org in en_conv2org[term_conv]:
                self.en[en_org]['mesh_ids'] |= ids
                for name_ja in self.en[en_org]['names_ja']:
                    self.ja[name_ja]['mesh_ids'] |= ids

        en_has_mesh = sum([1 for v in self.en.values() if v['mesh_ids']])
        ja_has_mesh = sum([1 for v in self.ja.values() if v['mesh_ids']])
        lines = [
            '{:,}/{:,} English words are mapped to MeSH IDs'.format(en_has_mesh, len(self.en)),
            '{:,}/{:,} Japanese words are mapped to MeSH IDs'.format(ja_has_mesh, len(self.ja)),
        ]
        print('\n'.join(lines))


class MEDUTX(Dictionary):
    dict_name = 'medutx'

    def __init__(self):
        super(MEDUTX, self).__init__(self.dict_name)

    def read(self, fp: Path):
        with fp.open() as f:
            reader = csv.reader(f, delimiter='\t')
            for word_en, word_ja in reader:
                self.word_pairs.append(
                    WordPair(word_en, word_ja)
                )
        self.make_dictionary()


class TEMU(Dictionary):
    dict_name = 'temu'

    def __init__(self):
        super(TEMU, self).__init__(self.dict_name)

    def read(self, fp: Path):
        with fp.open() as f:
            reader = csv.reader(f, delimiter='\t')
            for word_en, word_ja in reader:
                self.word_pairs.append(
                    WordPair(word_en, word_ja)
                )
        self.make_dictionary()


def combine_dict(dict_list: List[Dictionary], dict_name: str=None):
    """
    複数の辞書を結合
    :param dict_list:
    :param dict_name:
    :return:
    """
    if dict_name is None:
        dict_name = ' + '.join([d.dict_name for d in dict_list])
    _dict = Dictionary(dict_name)
    _dict.word_pairs = [w for d in dict_list for w in d.word_pairs]
    _dict.make_dictionary()
    return _dict
