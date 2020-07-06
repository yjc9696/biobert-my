import json
import logging
import os

from config import opt


class RunningAverage():
    """A simple class that maintains the running average of a quantity

    Example:
    ```
    loss_avg = RunningAverage()
    loss_avg.update(2)
    loss_avg.update(4)
    loss_avg() = 3
    ```
    """

    def __init__(self):
        self.steps = 0
        self.total = 0

    def update(self, val):
        self.total += val
        self.steps += 1

    def __call__(self):
        return self.total / float(self.steps)


def set_logger(log_path):
    """Set the logger to log info in terminal and file `log_path`.

    In general, it is useful to have a logger so that every output to the terminal is saved
    in a permanent file. Here we save it to `model_dir/train.log`.

    Example:
    ```
    logging.info("Starting training...")
    ```

    Args:
        log_path: (string) where to log
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Logging to a file
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
        logger.addHandler(file_handler)

        # Logging to console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(stream_handler)




def norm_length(origin_list):
    """
    规范化标签格式长度
    input: ['球', '星'， '姚', '明']
    """

    return origin_list
    norm_list = []
    for i in origin_list:
        if len(i) < 5:
            i = i + (5 - len(i)) * ' '
        else:
            i = i[:5]
        norm_list.append(i)
    return norm_list

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


def clear_data(text):
    # text = text.replace("*", "")
    # text = text.replace(".", "")
    # text = text.replace(":", "")
    # text = text.replace("#", "")
    # text = text.replace("[", "")
    # text = text.replace("]", "")
    return text

def load_data_base(path):
    '''
    加载数据，返回json数组.
    '''
    data = []
    data_lines = open(path, encoding='utf-8').readlines()
    for line in data_lines:
        line_json = json.loads(line)
        if len(line_json['postag']) == 0:
            continue
        if 'spo_list' in line_json.keys() and len(line_json['spo_list']) == 0:
            continue
        data.append(line_json)
    return data
def load_data(path, case=0):
    '''
    加载数据，字典数据列表.
    0:加载原始json数据
    1:加载schema数据
    '''
    data = []
    if case == 1:
        data_lines = open(path, encoding='utf-8').readlines()
        for line in data_lines:
            line_json = json.loads(line)
            data.append(line_json)
        return data
    filelist = os.listdir(path)
    text_files = []
    tag_files = []
    txt_files = []
    for filename in filelist:
        de_path = os.path.join(path, filename)
        if os.path.isfile(de_path):
            if de_path.endswith(".ssp"):  # Specify to find the  file.
                text_files.append(de_path)
            if de_path.endswith(".ann"):
                tag_files.append(de_path)
            if de_path.endswith(".txt"):
                txt_files.append(de_path)
    if len(text_files)==0:
        text_files=txt_files
    for index in range(len(text_files)):
        text_file = text_files[index]
        tag_file = tag_files[index]
        text = open(text_file, encoding='utf-8').read()
        pos_tag = []
        T_map = {}
        spo_list = []
        with open(tag_file, encoding='utf-8') as file_to_read:
            while True:
                tag_line = file_to_read.readline()
                if not tag_line:
                    break
                tag_line = tag_line.split()
                if tag_line[0].find('T') != -1:
                    tag = {}
                    tag["type"] = tag_line[1]
                    tag["word"] = ' '.join(tag_line[4:])
                    if tag_line[2].isdigit() == False or tag_line[3].isdigit() == False:
                        continue
                    tag["start_id"] = int(tag_line[2])
                    tag["end_id"] = int(tag_line[3])
                    T_map[tag_line[0]] = tag
                    pos_tag.append(tag)
            file_to_read.seek(0)
            while True:
                tag_line = file_to_read.readline()
                if not tag_line:
                    break
                tag_line = tag_line.split()
                if tag_line[0].find('R') != -1:
                    O = tag_line[2][5:]
                    S = tag_line[3][5:]
                    if (O not in T_map.keys()) or (S not in T_map.keys()):
                        continue
                    O = T_map[O]
                    S = T_map[S]
                    spo = {}
                    spo["predicate"] = tag_line[1]
                    spo["object"] = O["word"]
                    spo["O"]=O
                    spo["object_type"] = O["type"]
                    spo["subject"] = S["word"]
                    spo["S"]=S
                    spo["subject_type"] = S["type"]
                    spo_list.append(spo)
        text = clear_data(text)
        start_id = 0
        end_id = 0
        if (opt.is_cut):
            while True:
                if end_id==len(text):
                    break
                start_id = end_id
                end_id = min(end_id + opt.seq_length, len(text))
                text_now = text[start_id:end_id]
                if len(text_now) < opt.seq_length:
                    text_now += ' ' * (opt.seq_length - len(text_now))
                spo_l = []
                for spo in spo_list:
                    O = spo["O"]
                    S = spo["S"]
                    if int(O["start_id"]) >= start_id and int(O["end_id"]) < end_id and int(S["start_id"]) >= start_id and int(S["end_id"]) < end_id:
                        spo_l.append(spo)
                if len(spo_l) == 0:
                    continue
                line = {}
                spo_l
                line["text"] = text_now
                line["postag"] = []
                line["spo_list"] = spo_l
                data.append(line)

        else:
            line = {}
            line["text"] = text
            line["postag"] = []
            line["spo_list"] = spo_list
            data.append(line)
    return data
