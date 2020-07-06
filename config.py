# coding=utf-8
# -*- coding: utf-8 -*-

class Config(object):
    # -----------数据集选择--------------------#
    dataset = 'N2C2-BIG'  # large(没有合并type关系)/small(合并type关系)
    naNum = 2  # 每个例子中补充的最大NA关系数目
    tag_nums = 19 * 2 + 1  # tag类型数量
    rel_nums = 50  # 关系数量

    # -------------dir ----------------#
    bert_model_dir = './biobert_v1.1_pubmed/bert-base-uncased.tar.gz'
    bert_vocab_dir = './biobert_v1.1_pubmed/vocab.txt'
    bert_vocab_unk = './biobert_v1.1_pubmed/vocab.txt'
    data_root = './datasets/NER/' + dataset + '/'
    npy_data_root = './datasets/NER/' + dataset + '/npy_data/'
    origin_data_root = './datasets/NER/' + dataset + '/origin_data/'
    json_data_root = './datasets/NER/' + dataset + '/json_data/'

    id2type_dir = json_data_root + 'id2type.json'
    type2id_dir = json_data_root + 'type2id.json'
    tag2id_dir = json_data_root + 'tag2id.json'
    r2id_dir = json_data_root + 'r2id.json'
    id2r_dir = json_data_root + 'id2r.json'
    id2tag_dir = json_data_root + 'id2tag.json'
    type2types_dir = json_data_root + 'type2types.json'

    schema_dir_old = origin_data_root + 'all_50_schemas_old'
    schema_dir_new = origin_data_root + 'relation.data'
    train_data_dir = origin_data_root + 'train_data'
    dev_data_dir = origin_data_root + 'dev_data'
    test1_data_dir = origin_data_root + 'test_data'
    test2_data_dir = origin_data_root + 'test2_data_postag'

    log_dir = './log'
    #  -------------- 模型超参数 -----------#
    k = 9
    filters = [5, 9, 13]  # CNN卷积核宽度
    filter_num = 230  # CNN卷积核个数
    seq_length = 128
    tuple_max_len = 13
    bert_hidden_size = 768  # bert隐层维度，固定
    lam = 0.85  # 越大tag越重要`

    # --------------main.py ----------------#
    load_ckpt = False
    ckpt_path = './checkpoints/BERT_MUL_CNN_sl512_k[5, 9, 13]_fn230_lam0.85_lr3e-05_epoch0'
    num_workers = 1
    seed = 9979
    epochs = 10
    batch_size = 8
    use_gpu = 0
    gpu_id = 0
    # ------------optimizer ------------------#
    lr = 3e-5
    full_finetuning = True
    optimizer = 'Adam'
    model = 'BERT_MUL_CNN'  # 'BERT_CNN_CRF'
    clip_grad = 2  # 梯度的最大值
    use_all_positions = False
    is_cut = True
    # ----------预测数据集----------#
    case = 1  # 0:dev(并测试数据质量) 1:test1, 2:test2

    def parse(self, kwargs):
        '''
        user can update the default hyperparamter
        '''
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise Exception('opt has No key: {}'.format(k))
            setattr(self, k, v)

        print('*************************************************')
        print('user config:')
        for k, v in self.__class__.__dict__.items():
            if not k.startswith('__'):
                print("{} => {}".format(k, getattr(self, k)))

        print('*************************************************')


opt = Config()
