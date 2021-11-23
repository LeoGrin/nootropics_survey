import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from surprise import KNNBaseline
from surprise import Dataset
from surprise import Reader
from new_names import short_dic

import streamlit as st
from copy import deepcopy


rating_example = {'Modafinil': 6,
'Caffeine': 6,
'Coluracetam': None,
'Phenylpiracetam': None,
'Theanine': 7,
'Noopept': None,
'Oxiracetam': None,
'Aniracetam': None,
'Rhodiola': None,
'Creatine': 4,
'Piracetam': None,
'Ashwagandha': None,
'Bacopa': None,
'Choline': None,
'DMAE': None,
'Fasoracetam': None,
'SemaxandNASemaxetc': None,
'SelankandNASelanketc': None,
'Inositol': None,
'Seligiline': None,
'AlphaBrainproprietaryblend': None,
'Cerebrolysin': None,
'Melatonin': 8,
'Uridine': None,
'Tianeptine': None,
'MethyleneBlue': None,
'Unifiram': None,
'PRL853': None,
'Emoxypine': None,
'Picamilon': None,
'Dihexa': None,
'Epicorasimmunebooster': None,
'LSD': 7,
'Adderall': 8,
"Phenibut": 6,
"Nicotine": 7}

nootropics_list = rating_example.keys()


def get_item_baseline():
    df_clean = pd.read_csv("data/dataset_clean_right_names.csv")

    final_model = KNNBaseline(k=60, min_k=2, sim_options={'name': 'pearson_baseline', 'user_based': True})

    total_df = df_clean

    # A reader is still needed but only the rating_scale param is requiered.
    reader = Reader(rating_scale=(0, 10))

    # The columns must correspond to user id, item id and ratings (in that order).
    new_trainset = Dataset.load_from_df(total_df, reader).build_full_trainset()

    ## Fit the best model

    final_model.fit(new_trainset)

    item_baselines = final_model.default_prediction() + final_model.compute_baselines()[
        1]  # mean rating + item baseline ?

    return pd.DataFrame({"nootropic": nootropics_list, "item_baselines":item_baselines})


def predict(rating_dic):

    df_clean = pd.read_csv("data/dataset_clean_right_names.csv")
    avalaible_nootropics = np.unique(df_clean["itemID"]) #we want to ignore nootropics that are not in the df
    #######################
    # Fit surprise model
    #######################

    final_model = KNNBaseline(k=60, min_k=2, sim_options={'name': 'pearson_baseline', 'user_based': True})

    new_user_id = max(df_clean["userID"]) + 1 #TODO if merge
    items = np.array([item for item in list(rating_dic.keys()) if item in avalaible_nootropics])
    ratings = np.array([rating_dic[item] for item in items])
    rated_mask = ratings != None
    ratings = ratings[rated_mask]
    items = items[rated_mask]
    user = np.ones(len(items), dtype="int") * new_user_id
    new_user_df = pd.DataFrame({"userID": user, "itemID": items, "rating": ratings})

    total_df = df_clean.append(new_user_df)

    # A reader is still needed but only the rating_scale param is requiered.
    reader = Reader(rating_scale=(0, 10))

    # The columns must correspond to user id, item id and ratings (in that order).
    new_trainset = Dataset.load_from_df(total_df, reader).build_full_trainset()

    ## Fit the best model

    final_model.fit(new_trainset)

    predicted_ratings = []
    for nootropic in avalaible_nootropics:
            predicted_ratings.append(final_model.predict(new_user_id, nootropic).est)

    item_baselines = final_model.default_prediction() + final_model.compute_baselines()[1]  # mean rating + item baseline ?

    #print(final_model.compute_baselines()[0][-1])
    #item_baselines_user = final_model.default_prediction() + final_model.compute_baselines()[1] +\
    #                      final_model.compute_baselines()[0][-1] #not sure
    result_df = pd.DataFrame(
        {"nootropic": [short_dic[noot] for noot in avalaible_nootropics],
         "Your predicted rating": predicted_ratings,
         "Mean rating of this nootropic": item_baselines})
         #"baseline_rating_user": item_baselines_user}) #TODO ?


    return result_df.sort_values("Your predicted rating", ascending=False, ignore_index=True)

def evaluate(rating_dic):
    df_clean = pd.read_csv("data/dataset_clean_right_names.csv")
    avalaible_nootropics = np.unique(df_clean["itemID"]) #we want to ignore nootropics that are not in the df
    loo_ratings = []
    rating_dic_copy = deepcopy(rating_dic)
    rated_avalaible_nootropics = [nootropic for nootropic in rating_dic.keys() if nootropic in avalaible_nootropics]
    for nootropic in rated_avalaible_nootropics:
            rating_dic_copy.pop(nootropic)
            new_result_df = predict(rating_dic_copy)
            loo_ratings.append(new_result_df[new_result_df["nootropic"] == nootropic]["Your predicted rating"].values[0])
            rating_dic_copy = deepcopy(rating_dic)
    item_baselines_df = get_item_baseline()
    item_baselines = item_baselines_df[item_baselines_df["nootropic"].isin(rating_dic.keys())]["item_baselines"].values

    return pd.DataFrame({"nootropic": [short_dic[noot] for noot in rated_avalaible_nootropics],
                         "Your rating": [rating_dic[nootropic] for nootropic in rated_avalaible_nootropics],
                         "Predicted rating": loo_ratings,
                         "Baseline rating": item_baselines})

if __name__ == """__main__""":
    print(predict(rating_example))