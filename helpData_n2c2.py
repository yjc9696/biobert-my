import json

import numpy as np

import metrics
import tokenization
import utils
from config import opt


def write2file(data, path):
    with open(path, 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False))
def get_BIO(self, tag):
    return self.id2tag[tag]
    # if tag == 0:
    #     return 'O'
    # if tag % 2 == 1:
    #     return 'B-' + str(tag)
    # else:
    #     return 'I-' + str(tag)


def detokenize(self,in_tok,in_lab):
    """
    convert suub-word level BioBERT-NER results to full words and labels.

    Args:
        pred_token_test_path: path to token_test.txt from output folder. ex) output/token_test.txt
        pred_label_test_path: path to label_test.txt from output folder. ex) output/label_test.txt
    Outs:
        A dictionary that contains full words and predicted labels.
    """

    # read predicted
    pred = {'toks':[], 'labels':[]} # dictionary for predicted tokens and labels.
    for lineIdx, (lineTok, lineLab) in enumerate(zip(in_tok, in_lab)):
        pred['toks'].append(lineTok)
        if lineLab in ['[CLS]','[SEP]', 'X']: # replace non-text tokens with O. These will not be evaluated.
            pred['labels'].append('O')
            continue
        pred['labels'].append(get_BIO(self,lineLab))

    assert (len(pred['toks']) == len(pred['labels'])), "Error! : len(pred['toks'])(%s) != len(pred['labels'])(%s) : Please report us "%(len(pred['toks']), len(pred['labels']))

    bert_pred = {'toks':[], 'labels':[], 'sentence':[]}
    buf = []
    for t, l in zip(pred['toks'], pred['labels']):
        if t in ['[CLS]','[SEP]']: # non-text tokens will not be evaluated.
            bert_pred['toks'].append(t)
            bert_pred['labels'].append(t) # Tokens and labels should be identical if they are [CLS] or [SEP]
            if t == '[SEP]':
                bert_pred['sentence'].append(buf)
                buf = []
            continue
        elif t[:2] == '##': # if it is a piece of a word (broken by Word Piece tokenizer)
            bert_pred['toks'][-1] += t[2:] # append pieces to make a full-word
            buf[-1]+=t[2:]
        else:
            bert_pred['toks'].append(t)
            bert_pred['labels'].append(l)
            buf.append(t)

    assert (len(bert_pred['toks']) == len(bert_pred['labels'])), ("Error! : len(bert_pred['toks']) != len(bert_pred['labels']) : Please report us")

    return bert_pred


class DataHelper(object):
    def __init__(self, opt):
        self.opt = opt
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=opt.bert_vocab_unk, do_lower_case=True)
        self.id2r, self.r2id = None, None
        self.id2tag, self.tag2id = None, None
        self.id2type, self.type2id = None, None
        self.type2types = None
        self.get_relations()

        self.origin_train_data = utils.load_data(self.opt.train_data_dir)
        self.origin_dev_data = utils.load_data(self.opt.dev_data_dir)
        self.origin_test1_data = utils.load_data(self.opt.test1_data_dir)

    def get_relations(self):
        """
        得到所有的xx2xx文件
        """
        # origin_50_schema = load_data(self.opt.schema_dir_old, case=1)
        relation_all = utils.load_data(self.opt.schema_dir_new, case=1)
        # self.down2top = {}  # 记录类别的上下为关系
        # for old, new in zip(origin_50_schema, new_50_schema):
        #     old_sample_obj_type = old['object_type']
        #     old_sample_sbj_type = old['subject_type']
        #     new_sample_obj_type = new['object_type']
        #     new_sample_sbj_type = new['subject_type']
        #     top_obj, top_sbj = self.down2top.get(old_sample_obj_type, None), self.down2top.get(old_sample_sbj_type, None)
        #     assert (top_obj == None or top_obj == new_sample_obj_type) \
        #            and (top_sbj == None or top_sbj == new_sample_sbj_type)
        #     self.down2top[old_sample_obj_type] = new_sample_obj_type
        #     self.down2top[old_sample_sbj_type] = new_sample_sbj_type
        # print("上下位关系为:{}".format(self.down2top))

        self.r2id = {}
        self.id2r = {}
        self.id2tag = {}
        self.tag2id = {}
        self.id2type = {}
        self.type2id = {}
        exist_ent_type, exist_rel_type = set(), set()
        for sample in relation_all:
            obj, r, sbj = sample['object_type'], sample['predicate'], sample['subject_type']
            if obj not in exist_ent_type:
                self.id2type[len(exist_ent_type) + 1] = obj
                self.id2tag[2 * len(exist_ent_type) + 1] = 'B-' + obj
                self.id2tag[2 * len(exist_ent_type) + 2] = 'I-' + obj
                exist_ent_type.add(obj)
            if sbj not in exist_ent_type:
                self.id2type[len(exist_ent_type) + 1] = sbj
                self.id2tag[2 * len(exist_ent_type) + 1] = 'B-' + sbj
                self.id2tag[2 * len(exist_ent_type) + 2] = 'I-' + sbj
                exist_ent_type.add(sbj)
            if r not in exist_rel_type:
                # 多余给NA
                self.id2r[len(exist_rel_type)] = r
                exist_rel_type.add(r)

        self.id2r[len(exist_rel_type)] = 'NA'
        exist_rel_type.add('NA')
        self.id2tag[0] = 'O'
        exist_ent_type.add('O')
        self.id2type[0] = 'O'

        print("实体类型数目为:{};关系数目为:{}".format(len(exist_ent_type), len(exist_rel_type)))
        self.r2id = {self.id2r[idx]: idx for idx in self.id2r.keys()}
        self.tag2id = {self.id2tag[idx]: idx for idx in self.id2tag.keys()}
        self.type2id = {self.id2type[idx]: idx for idx in self.id2type.keys()}

        self.type2types = {ent: set() for ent in exist_ent_type}
        for sample in relation_all:
            obj, r, sbj = sample['object_type'], sample['predicate'], sample['subject_type']
            self.type2types[obj].add(sbj)

        self.type2types = {ent: list(self.type2types[ent]) for ent in self.type2types.keys()}

        # 写入文件
        print("写入xx2xx数据到目录{}..".format(self.opt.json_data_root))
        write2file(self.id2r, self.opt.id2r_dir)
        write2file(self.r2id, self.opt.r2id_dir)
        write2file(self.id2tag, self.opt.id2tag_dir)
        write2file(self.tag2id, self.opt.tag2id_dir)
        write2file(self.id2type, self.opt.id2type_dir)
        write2file(self.type2id, self.opt.type2id_dir)
        write2file(self.type2types, self.opt.type2types_dir)

    def down2topForDatas(self, datas):
        topDatas = []
        for data in datas:
            text = data['text']
            downSpoList = data['spo_list']
            topSpoList = []
            for spo in downSpoList:
                spo['object_type'] = self.down2top[spo['object_type']]
                spo['subject_type'] = self.down2top[spo['subject_type']]
                topSpoList.append(spo)
            dataUnit = {}
            dataUnit['text'] = text
            dataUnit['spo_list'] = topSpoList
            topDatas.append(dataUnit)
        return topDatas

    def get_positions(self, data_list, map_str):
        """
        返回实体在单词列表中的所有位置
        sample:
        >> input: ['球','星','球'，'星', ...., ], '球星'
        >> return: 【(2, 3)，（4，5）】
        """
        result = []
        if (opt.use_all_positions == False):
            str, end = self.get_position(data_list, map_str)
            result.append((str, end))
            return result
        map_str = map_str.strip().replace(' ', '$')
        map_str = self.tokenizer.tokenize(map_str)
        map_str = [i.replace('#', '') for i in map_str]
        map_str = ''.join(map_str)
        data_list = [i.replace('#', '') for i in data_list]
        # 如果只由一个词组成
        for word in data_list:
            if map_str.lower() in word.lower():
                start_id = end_id = data_list.index(word)
                result.append((start_id, end_id))
        start_id = -1
        end_id = -1
        for idx, word in enumerate(data_list):
            if map_str.startswith(word):
                start_id = end_id = idx
                while end_id + 1 < len(data_list) and data_list[end_id + 1] in map_str:
                    if "".join(data_list[start_id:end_id + 2]) == map_str:
                        # print("".join(data_list[start_id:end_id+3]))
                        result.append((start_id, end_id + 1))
                        break
                    end_id += 1
                find_str = ""
                for idx in range(start_id, end_id + 1):
                    find_str = find_str + data_list[idx]
                if find_str != map_str:
                    pre_extend = (data_list[start_id - 1] if start_id > 0 else "") + find_str
                    last_extend = find_str + (data_list[end_id + 1] if end_id < len(data_list) - 1 else "")
                    pre_last_extend = (data_list[start_id - 1] if start_id > 0 else "") + find_str + (data_list[end_id + 1] if end_id < len(data_list) - 1 else "")
                    if map_str in pre_extend:
                        start_id -= 1
                    elif map_str in last_extend:
                        end_id += 1
                    elif map_str in pre_last_extend:
                        start_id -= 1
                        end_id += 1
                    else:
                        start_id = -1
                        end_id = -1
        if len(result) > 0:
            return result
        for idx, word in enumerate(data_list[:-1]):
            if map_str in (word + data_list[idx + 1]):
                result.append((idx, idx + 1))

        if len(result) == 0:
            result.append((-1, -1))
        # print("word_list{}  map_str {} loss".format(data_list, map_str))
        return result

    def get_position(self, data_list, map_str):
        """
        返回实体在单词列表中的位置,只返回第一次出现的位置
        sample:
        >> input: ['球','星','姚'，'明', ...., ], '姚明'
        >> return: (2, 3)
        """
        map_str = map_str.strip().replace(' ', '$')
        map_str = self.tokenizer.tokenize(map_str)
        map_str = [i.replace('#', '') for i in map_str]
        map_str = ''.join(map_str)
        data_list = [i.replace('#', '') for i in data_list]
        # 如果只由一个词组成
        for word in data_list:
            if map_str.lower() in word.lower():
                start_id = end_id = data_list.index(word)
                return start_id, end_id

        start_id = -1
        end_id = -1
        for idx, word in enumerate(data_list):
            if start_id != - 1 and end_id != -1:
                return start_id, end_id
            if map_str.startswith(word):
                start_id = end_id = idx
                while end_id + 1 < len(data_list) and data_list[end_id + 1] in map_str:
                    if "".join(data_list[start_id:end_id + 2]) == map_str:
                        # print("".join(data_list[start_id:end_id+3]))
                        return start_id, end_id + 1
                    end_id += 1
                find_str = ""
                for idx in range(start_id, end_id + 1):
                    find_str = find_str + data_list[idx]
                if find_str != map_str:
                    pre_extend = (data_list[start_id - 1] if start_id > 0 else "") + find_str
                    last_extend = find_str + (data_list[end_id + 1] if end_id < len(data_list) - 1 else "")
                    pre_last_extend = (data_list[start_id - 1] if start_id > 0 else "") + find_str + (data_list[end_id + 1] if end_id < len(data_list) - 1 else "")
                    if map_str in pre_extend:
                        start_id -= 1
                    elif map_str in last_extend:
                        end_id += 1
                    elif map_str in pre_last_extend:
                        start_id -= 1
                        end_id += 1
                    else:
                        start_id = -1
                        end_id = -1
        if start_id != -1 and end_id != -1:
            return start_id, end_id
        for idx, word in enumerate(data_list[:-1]):
            if map_str in (word + data_list[idx + 1]):
                return idx, idx + 1
        # print("word_list{}  map_str {} loss".format(data_list, map_str))
        return start_id, end_id

    def get_tag(self, word_list, entity_list, type_list):
        '''
        得到一个句子的tag标签
        sampple:
        >> input: ['球'，'星', '姚'， '明', ...], ['姚明']， ['人物']
        >> return: ['O', 'O', 'id(B-人物), id(I-人物)']
        '''
        word_list = [word.replace('#', '') for word in word_list]
        tag_list = [0] * len(word_list)
        for entity, type_ in zip(entity_list, type_list):
            positions = self.get_positions(word_list, entity)
            for start_id, end_id in positions:
                if start_id == -1 or end_id == -1:
                    continue
                # 补充书名号
                #  if start_id > 0 and end_id < len(word_list)-1:
                #      if word_list[start_id-1] == '《' and word_list[end_id+1] == '》':
                #          start_id -= 1
                #          end_id += 1
                Bid = 2 * (self.type2id[type_] - 1) + 1
                Iid = 2 * (self.type2id[type_] - 1) + 2
                tag_list[start_id] = Bid
                if start_id < end_id:
                    for idx in range(start_id + 1, end_id + 1):
                        tag_list[idx] = Iid
        return tag_list

    def get_entity_list_and_type_list(self, data_list):
        """
        得到实体和对应的类型列表，一一对应
        sample:
        >> input: [姚明，NBA]
        >> return:[人，组织]
        """
        entity_list, type_list = [], []
        for unit in data_list:
            entity_list.append(unit['object'])
            type_list.append(unit['object_type'])
            entity_list.append(unit['subject'])
            type_list.append(unit['subject_type'])
        return entity_list, type_list

    def get_sample_exist_entity2rlation(self, word_list, spo_list):
        """
        给定句子的 bert切词列表, 一句话的spo_list
        返回该句话存在的头实体尾实体位置及对应的关系字典
        {(obj_s, obj_e, sbj_s, sbj_e): r}
        """
        golden_map = {}
        word_list = [word.replace('#', '') for word in word_list]
        for spo in spo_list:
            obj = spo['object']
            sbj = spo['subject']

            o_po = self.get_positions(word_list, obj)
            s_po = self.get_positions(word_list, sbj)
            for o_s, o_e in o_po:
                for s_s, s_e in s_po:
                    r = self.r2id[spo['predicate']]
                    golden_map[(o_s, o_e, s_s, s_e)] = r
        return golden_map

    def get_sample_all_entity2relation(self, tags_list, golden_map):
        """
        返回一个句子所有可能实体组合极其关系
        [[s1, e1, s2, e2, r],
         [s1, e1, s2, e2, 0]
         ...]]
        """
        all_entity = []
        NA_entity = []
        NA_num = 0
        rel_num = 0
        tags_list = [self.id2tag[i] for i in tags_list]
        ent_and_position = metrics.get_entities(tags_list)
        for ent1 in ent_and_position:
            for ent2 in ent_and_position:
                if ent2 == ent1:
                    continue
                ent2_for_ent1 = self.type2types.get(ent1[0], [])
                if ent2[0] not in ent2_for_ent1:
                    continue
                entity_tuple = (ent1[1], ent1[2], ent2[1], ent2[2])
                # 0代表关系为NA
                re = golden_map.get(entity_tuple, self.r2id['NA'])
                ent_list = [entity_tuple[i] for i in range(4)]
                ent_list.append(re)
                if re == self.r2id['NA']:
                    NA_entity.append(ent_list)
                else:
                    all_entity.append(ent_list)
        rel_num = len(all_entity)
        if len(NA_entity) > 0:
            all_entity.extend(NA_entity[:min(2, len(NA_entity))])
            NA_num = min(opt.naNum, len(NA_entity))
        return all_entity, rel_num, NA_num

    def get_sens_and_tags_and_entsRel(self, datas, case=0):
        rel_max_sen = -1
        exceed_length_num = 0
        NA_num = 0
        max_r_num = 0
        all_rel_num = 0
        sens, tags, ent_rel = [], [], []
        PAD = self.tokenizer.convert_tokens_to_ids(['[PAD]'])
        O_tag = [self.type2id['O']]
        BIO_data = ""
        BIO_base =""
        for data in datas:
            text = data['text']
            # 一共修改3处， util中一处 此文件两处去掉首位空格，然后将空格替换为@
            text = text.strip().replace(' ', '$')
            word_list = self.tokenizer.tokenize(text)
            sen = self.tokenizer.convert_tokens_to_ids(word_list)
            rel_max_sen = max(rel_max_sen, len(word_list))
            if len(word_list) > self.opt.seq_length:
                exceed_length_num += 1

            if len(word_list) < self.opt.seq_length:
                sen = sen + PAD * (self.opt.seq_length - len(sen))
            else:
                sen = sen[:self.opt.seq_length]
            sens.append(sen)

            # if case >= 2:
            #     continue
            entity_list, type_list = self.get_entity_list_and_type_list(data['spo_list'])
            # __import__('ipdb').set_trace()
            # '▌1999年：「喜剧之王」前两年的贺岁档其实都有星爷，只不过作品票房一直跟不上'
            tag = self.get_tag(word_list, entity_list, type_list)
            assert len(word_list) == len(tag)
            if len(word_list) < self.opt.seq_length:
                tag = tag + O_tag * (self.opt.seq_length - len(tag))
            else:
                tag = tag[:self.opt.seq_length]
            tags.append(tag)
            de_t=detokenize(self,word_list,tag)
            for i,word in enumerate(word_list):
                if word == '$':
                    continue
                BIO_data = BIO_data + word + "	" + get_BIO(self, tag[i]) + "\n"
            for i in  range(len(de_t['toks'])):
                word=de_t['toks'][i]
                label=de_t['labels'][i]
                if word == '$':
                    continue
                BIO_base = BIO_base + word + "	" + label + "\n"
            BIO_data = BIO_data + '\n'
            BIO_base = BIO_base + '\n'
            # __import__('ipdb').set_trace()
            exist_map = self.get_sample_exist_entity2rlation(word_list, data['spo_list'])
            if case == 0:
                all_e2r, rel_num, NAs = self.get_sample_all_entity2relation(tag, exist_map)
                NA_num += NAs
            else:
                all_e2r = []
                for key in exist_map.keys():
                    e2r = [key[0], key[1], key[2], key[3], exist_map[key]]
                    all_e2r.append(e2r)
            all_rel_num += len(exist_map)
            max_r_num = max(max_r_num, len(all_e2r))
            ent_rel.append(all_e2r)
        sens = np.array(sens)
        tags = np.array(tags)
        ent_rel = np.array(ent_rel)

        root_path = self.opt.data_root
        base=""
        if case == 0:
            branch = 'train.tsv'
            base ='train_base.tsv'
        if case == 1:
            branch = 'dev.tsv'
            base ='dev_base.tsv'
        if case == 2:
            branch = 'test.tsv'
            base ='test_base.tsv'
        if case == 3:
            branch = 'test2.tsv'
        data_root = root_path
        print("存在关系数:{};NA关系数{}; 每句话中最大关系数(含NA):{}".format(all_rel_num, NA_num, max_r_num))
        print("真实最大长度{}; 设置最大长度{}; 超过长度数{}".format(rel_max_sen, self.opt.seq_length, exceed_length_num))
        print("saving data in {}".format(data_root))

        with open(data_root+branch, 'w') as f:
            f.write(BIO_data)
        with open(data_root+base, 'w') as f:
            f.write(BIO_base)
        # np.save(data_root + 'sens', sens)
        # np.save(data_root + 'tags', tags)
        # np.save(data_root + 'relations', ent_rel)

    def process_data(self):
        if self.origin_train_data is not None:
            print("process train data")
            self.get_sens_and_tags_and_entsRel(self.origin_train_data, case=0)
        if self.origin_dev_data is not None:
            print("process dev data")
            self.get_sens_and_tags_and_entsRel(self.origin_dev_data, case=1)
        if self.origin_test1_data is not None:
            print("process test1 data")
            self.get_sens_and_tags_and_entsRel(self.origin_test1_data, case=2)
        print("确定数据质量...")
        # metrics.judge_data_quality(self.opt)


if __name__ == '__main__':
    dataHelper = DataHelper(opt)
    # metrics.judge_data_quality(opt)
    dataHelper.process_data()
