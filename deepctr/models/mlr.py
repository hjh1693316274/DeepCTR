# -*- coding:utf-8 -*-
"""
Author:
    Weichen Shen,wcshen1994@163.com

Reference:
    [1] Gai K, Zhu X, Li H, et al. Learning Piece-wise Linear Models from Large Scale Data for Ad Click Prediction[J]. arXiv preprint arXiv:1704.05194, 2017.(https://arxiv.org/abs/1704.05194)
"""
from tensorflow.python.keras.layers import  Activation, dot
from tensorflow.python.keras.models import Model

from ..layers.core import PredictionLayer
from ..inputs import build_input_features,get_linear_logit
from ..layers.utils import concat_fun

def MLR(region_feature_columns, base_feature_columns=None, region_num=4,
        l2_reg_linear=1e-5,
        init_std=0.0001, seed=1024, task='binary',
        bias_feature_columns=None):
    """Instantiates the Mixed Logistic Regression/Piece-wise Linear Model.

    :param region_feature_columns: dict,to indicate sparse field and dense field like {'sparse':{'field_1':4,'field_2':3,'field_3':2},'dense':['field_4','field_5']}
    :param base_feature_columns: dict or None,to indicate sparse field and dense field of base learner.if None, it is same as region_feature_dim_dict
    :param region_num: integer > 1,indicate the piece number
    :param l2_reg_linear: float. L2 regularizer strength applied to weight
    :param init_std: float,to use as the initialize std of embedding vector
    :param seed: integer ,to use as random seed.
    :param task: str, ``"binary"`` for  binary logloss or  ``"regression"`` for regression loss
    :param bias_feature_columns: dict,to indicate sparse field and dense field like {'sparse':{'field_1':4,'field_2':3,'field_3':2},'dense':['field_4','field_5']}
    :return: A Keras model instance.
    """

    #todo 还没修改
    if region_num <= 1:
        raise ValueError("region_num must > 1")
    # if not isinstance(region_feature_columns,
    #                   dict) or "sparse" not in region_feature_columns or "dense" not in region_feature_columns:
    #     raise ValueError(
    #         "feature_dim must be a dict like {'sparse':{'field_1':4,'field_2':3,'field_3':2},'dense':['field_5',]}")

    same_flag = False
    if base_feature_columns is None or len(base_feature_columns) == 0:
        base_feature_columns = region_feature_columns
        same_flag = True
    if bias_feature_columns is None:
        bias_feature_columns = []
    #for feat in region_feature_columns['sparse'] + base_feature_columns['sparse'] + bias_feature_columns['sparse']:
    #    if feat.hash_flag:
    #        raise ValueError("Feature Hashing on the fly is no supported in MLR") #TODO:support feature hashing on the MLR


    features = build_input_features(region_feature_columns + base_feature_columns+bias_feature_columns)

    inputs_list = list(features.values())

    region_score = get_region_score(features,region_feature_columns,region_num,l2_reg_linear,init_std,seed)
    learner_score = get_learner_score(features,base_feature_columns,region_num,l2_reg_linear,init_std,seed,task=task)

    final_logit = dot([region_score,learner_score],axes=-1)

    if bias_feature_columns is not None and len(bias_feature_columns) > 0:
        bias_score =get_learner_score(features,bias_feature_columns,1,l2_reg_linear,init_std,seed,prefix='bias_',task='binary')

        final_logit = dot([final_logit,bias_score],axes=-1)

    model = Model(inputs=inputs_list, outputs=final_logit)
    return model


def get_region_score(features,feature_columns, region_number, l2_reg, init_std, seed,prefix='region_',seq_mask_zero=True):

    region_logit =concat_fun([get_linear_logit(features, feature_columns, l2_reg=l2_reg, init_std=init_std,
                                               seed=seed + i, prefix=prefix + str(i + 1)) for i in range(region_number)])
    return Activation('softmax')(region_logit)

def get_learner_score(features,feature_columns, region_number, l2_reg, init_std, seed,prefix='learner_',seq_mask_zero=True,task='binary'):
    region_score = [PredictionLayer(task=task,use_bias=False)(
        get_linear_logit(features, feature_columns, l2_reg=l2_reg, init_std=init_std, seed=seed + i,
                         prefix=prefix + str(i + 1))) for i in
                    range(region_number)]

    return concat_fun(region_score)

