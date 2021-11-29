import pandas as pd
from surprise import NormalPredictor, SVD, NMF, SlopeOne, CoClustering, KNNBasic, KNNWithZScore, KNNWithMeans, KNNBaseline, SVDpp, BaselineOnly
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import cross_validate, RandomizedSearchCV
from surprise import Reader, Dataset, KNNBaseline, SVD, accuracy
from new_names import all_nootropics
import numpy as np
import json

OVERWRITE = False

## Algorithm selection

# %%

df_clean = pd.read_csv("data/total_df.csv")

# A reader is still needed but only the rating_scale param is requiered.
reader = Reader(rating_scale=(0, 10))

# The columns must correspond to user id, item id and ratings (in that order).
data = Dataset.load_from_df(df_clean, reader)

# %%


# We can now use this dataset as we please, e.g. calling cross_validate
algorithms = ["SlopeOne",
              "CoClustering",
              "SVD",
              "SVDpp",
              "KNN_means_users",
              "KNN_zscore_users",
              "KNN_baselines_users",
              "KNN_means_items",
              "KNN_zscore_items",
              "KNN_baselines_items",
              "BaselineOnly"]
rmse = []
mae = []
fcp = []
print("SlopeOne")
res = cross_validate(SlopeOne(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
print(res)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("CoClustering")
res = cross_validate(CoClustering(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("SVD")
res = cross_validate(SVD(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("SVDpp")
res = cross_validate(SVDpp(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("KNN... (user based)")
print("with means")
res = cross_validate(KNNWithMeans(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("with z-score")
res = cross_validate(KNNWithZScore(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("with baselines")
res = cross_validate(KNNBaseline(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("KNN... (item based)")
print("with means")
res = cross_validate(KNNWithMeans(sim_options = {'user_based': False}), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("with z-scores")
res = cross_validate(KNNWithZScore(sim_options = {'user_based': False}), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("with baselines")
res = cross_validate(KNNBaseline(sim_options = {'user_based': False}), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))
print("BaselineOnly")
res = cross_validate(BaselineOnly(), data, cv=5, measures = ["rmse", "mae", "fcp"], verbose=True)
rmse.append(np.mean(res["test_rmse"]))
mae.append(np.mean(res["test_mae"]))
fcp.append(np.mean(res["test_fcp"]))

# %%

res_df = pd.DataFrame({"algo" :algorithms, "rmse" :rmse, "mae" :mae, "fcp" :fcp})
print(res_df)

if OVERWRITE:
    res_df.to_csv("model_selection/res.csv")

# %% md


# %% md

## Hyperparameters tuning

# %%

svd_params_dic = {"n_factors" :[10, 50, 100, 300], "n_epochs" :[20, 40, 100], "lr_all" :[0.005, 0.1], "reg_all" :[0.02, 0.1, 0.002]}

param_search = RandomizedSearchCV(SVD, svd_params_dic, cv=5, n_iter=50, n_jobs=-1)
param_search.fit(data)

# %%

print(param_search.best_params)
print(param_search.best_score)

# %%

knn_params_dic = {"k" :[10, 20, 40, 60, 100],
                  "min_k" :[1, 2, 5, 10],
                  "sim_options" :{'name': ['pearson_baseline', 'msd', 'cosine'], "user_based" :[True]}}

knn_param_search = RandomizedSearchCV(KNNBaseline, knn_params_dic, cv=5, n_iter=50, n_jobs=-1)
knn_param_search.fit(data)

# %%

print(knn_param_search.best_params)
print(knn_param_search.best_score)

if OVERWRITE:
    with open("model_selection/scores.txt", "w") as f:
        f.write(json.dumps(knn_param_search.best_params))
        f.write("\n")
        f.write(json.dumps(knn_param_search.best_score))
        f.write("\n")
        f.write(json.dumps(param_search.best_params))
        f.write("\n")
        f.write(json.dumps(param_search.best_score))

#Test models on original data

def evaluate(df_train, df_test, suffix=""):
    suprise_model_1 = KNNBaseline(k=60, min_k=2, sim_options={'name': 'pearson_baseline', 'user_based': True})
    suprise_model_2 = SVD(**{'n_factors': 50, 'n_epochs': 20, 'lr_all': 0.005, 'reg_all': 0.1})

    reader = Reader(rating_scale=(0, 10))
    # The columns must correspond to user id, item id and ratings (in that order).
    trainset = Dataset.load_from_df(df_train, reader).build_full_trainset()
    testset = Dataset.load_from_df(df_test, reader).build_full_trainset().build_testset()

    suprise_model_1.fit(trainset)
    suprise_model_2.fit(trainset)
    dic = {"model":[], "rmse":[], "mae":[], "fcp":[]}
    dic["model"].append("KNN_{}".format(suffix))
    print("Model 1")
    dic["rmse"].append(accuracy.rmse(suprise_model_1.test(testset)))
    dic["mae"].append(accuracy.mae(suprise_model_1.test(testset)))
    dic["fcp"].append(accuracy.fcp(suprise_model_1.test(testset)))

    dic["model"].append("SVD_{}".format(suffix))
    print("Model 2")
    dic["rmse"].append(accuracy.rmse(suprise_model_2.test(testset)))
    dic["mae"].append(accuracy.mae(suprise_model_2.test(testset)))
    dic["fcp"].append(accuracy.fcp(suprise_model_2.test(testset)))

    return pd.DataFrame(dic)


df_ssc = pd.read_csv("data/dataset_clean_right_names.csv")
df_new = pd.read_csv("data/new_df.csv")

remove_rare_noot = False

if remove_rare_noot:
    nootropics_with_enough_ratings = []
    for noot in all_nootropics:
        if df_new[df_new["itemID"] == noot].shape[0] > 10:  # TODO : optimize the number
            nootropics_with_enough_ratings.append(noot)
    df_train_total = df_new[df_new["itemID"].isin(nootropics_with_enough_ratings)]

n_ratings_ssc = len(df_ssc)
df1 = pd.DataFrame()
df2 = pd.DataFrame()

for i in range(10):
    train_indices = np.random.choice(list(range(n_ratings_ssc)), int(n_ratings_ssc * 0.6), replace=False)
    test_indices = np.array([i for i in range(n_ratings_ssc) if i not in train_indices])

    df_ssc_train, df_ssc_test = df_ssc.iloc[train_indices], df_ssc.iloc[test_indices]

    df1 = df1.append(evaluate(df_ssc_train, df_ssc_test, "ssc"))

    df_train_total = pd.concat([df_new, df_ssc_train])

    remove_rare_noot = False

    df2 = df2.append(evaluate(df_train_total, df_ssc_test, "new"))


df_total = df1.append(df2)
print(df_total.groupby("model").agg([np.mean, np.std]))

if OVERWRITE:
    df_total.groupby("model").agg([np.mean, np.std]).to_csv("score_on_original_mean.csv")
