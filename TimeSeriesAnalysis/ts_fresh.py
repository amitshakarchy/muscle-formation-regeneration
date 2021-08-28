import itertools
import sklearn
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from sklearn import clone
from sklearn.preprocessing import StandardScaler
# from xgboost import XGBClassifier
import joblib
from DataPreprocessing.load_tracks_xml import *
from tsfresh import extract_features, extract_relevant_features, select_features
from tsfresh.utilities.dataframe_functions import impute
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold, GridSearchCV
import pickle
import numpy as np
import matplotlib.pyplot as plt
import warnings
import os
from skimage import io

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # or any {'0', '1', '2'}
import tensorflow as tf

tf.get_logger().setLevel('ERROR')

warnings.filterwarnings("ignore", message="A value is trying to be set on a copy of a slice from a DataFrame")


def drop_columns(df, motility=True, intensity=True, basic=False):
    intensity_features = ['median_intensity', 'min_intensity', 'max_intensity', 'mean_intensity',
                          'total_intensity', 'std_intensity', 'contrast', 'snr', 'w', 'q']
    basic_features = ['t_stamp', 'z', 'spot_id', 'q']
    motility_features = ['x', 'y']
    to_remove = []
    to_remove.extend(basic_features) if not basic else to_remove.extend([])
    to_remove.extend(intensity_features) if not intensity else to_remove.extend([])
    to_remove.extend(motility_features) if not motility else to_remove.extend([])
    df = df[df.columns.drop(to_remove)]
    return df


def get_unique_indexes(y):
    idxs = y.index.unique()
    lst = [y[idx] if isinstance(y[idx], np.bool_) else y[idx].iloc[0] for idx in idxs]
    y_new = pd.Series(lst, index=idxs).sort_index()
    return y_new


def normalize_tracks(df, motility=False, intensity=False):
    if motility:
        for label in df.label:
            to_reduce_x = df[df.label == label].iloc[0].x
            to_reduce_y = df[df.label == label].iloc[0].y
            df.loc[(df.label == label).values, "x"] = df[df.label == label].x.apply(lambda num: num - to_reduce_x)
            df.loc[(df.label == label).values, "y"] = df[df.label == label].y.apply(lambda num: num - to_reduce_y)

    if intensity:
        columns = list(df.columns)
        try:
            columns.remove("t")
            columns.remove("label")
            columns.remove("target")
        except:
            pass

        # create a scaler
        scaler = StandardScaler()
        # transform the feature
        df[columns] = scaler.fit_transform(df[columns])
    return df


def concat_dfs(min_time_diff, lst_videos, crop_start=False, crop_end=False, time_window=False, diff_t_window=None,
               con_t_window=None):
    min_time_diff = min_time_diff
    max_val = 0
    total_df = pd.DataFrame()
    for i in lst_videos:
        xml_path = r"data/tracks_xml/manual_tracking/Experiment1_w1Widefield550_s{}_all_manual_tracking.xml".format(i)
        if not os.path.exists(xml_path):
            xml_path = "../" + xml_path if os.path.exists("../" + xml_path) else "muscle-formation-diff/" + xml_path
        _, df = load_tracks_xml(xml_path)

        if crop_start:
            # keep only the beginning of the track
            df = df[df["t"] <= 300]  # 300 time unites = 300*1.5/90 = 3.333 hours
        if crop_end:
            # keep only the end of the track
            df = df[df["t"] >= 700]  # 700 time unites = 700*1.5/90 = 17.5 hours

        if time_window:
            if i in (3, 4, 5, 6, 11, 12):  # ERK video
                # Cut the needed time window
                df = df[(df["t_stamp"] >= diff_t_window[0]) & (
                        df["t_stamp"] <= diff_t_window[1])]
            else:  # control video
                # Cut the needed time window
                df = df[(df["t_stamp"] >= con_t_window[0]) & (
                        df["t_stamp"] <= con_t_window[1])]

        df.label = df.label + max_val
        max_val = df["label"].max() + 1
        target = False
        if i in (3, 4, 5, 6, 11, 12):
            if df["t"].max() >= min_time_diff:
                target = True
        # target = True if i in (3, 4, 5, 6, 11, 12) else False
        df['target'] = np.array([target for i in range(len(df))])
        total_df = pd.concat([total_df, df], ignore_index=True)
    return total_df


def long_extract_features(df):
    y = pd.Series(df['target'])
    y.index = df["label"]
    y = get_unique_indexes(y)
    df = df[df.columns.drop(['target'])]
    extracted_features = extract_features(df, column_id="label", column_sort="t")
    impute(extracted_features)
    features_filtered = select_features(extracted_features, y)
    return features_filtered


def short_extract_features(df, y):
    features_filtered_direct = extract_relevant_features(df, y, column_id="label", column_sort='t', show_warnings=False,
                                                         n_jobs=8)
    return features_filtered_direct


def get_single_cells_diff_score_plot(tracks, clf, features_filtered_direct):
    all_probs = []
    for cell in (5, 7, 8, 9, 10):  # , 14, 16, 19, 27, 30
        true_prob = []
        n = 20
        for i in range(0, len(tracks[cell]), n):
            x = 0
            track_portion = tracks[cell][i:i + n]
            extracted_features = extract_features(track_portion, column_id="label", column_sort="t",
                                                  show_warnings=False, n_jobs=8)
            impute(extracted_features)
            X = extracted_features[features_filtered_direct.columns]
            probs = clf.predict_proba(X)
            true_prob.append(probs[0][1])
            print(f"track portion: [{i}:{i + n}]")
            print(clf.classes_)
            print(probs)
            track_len = len(tracks[cell])
            label_time = [(tracks[cell].iloc[val]['t'] / 60) / 60 for val in range(0, track_len, n)]

        plt.plot(range(0, track_len, n), true_prob)
        plt.xticks(range(0, track_len, n), labels=np.around(label_time, decimals=1))
        plt.ylim(0, 1, 0.1)
        plt.title(f"probability to differentiation over time- diff, cell #{cell}")
        plt.xlabel("time [h]")
        plt.ylabel("prob")
        plt.grid()
        plt.show()
        all_probs.append(true_prob)
        return all_probs


def train(X_train, X_test, y_train, y_test):
    clf = RandomForestClassifier()
    clf.fit(X_train, y_train)
    predicted = cross_val_predict(clf, X_test, y_test, cv=5)
    report = classification_report(y_test, predicted)
    auc_score = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
    print(report)
    print(auc_score)
    return clf, report, auc_score


def get_x_y(lst_videos, motility, intensity, min_length=0, max_length=950, min_time_diff=0, crop_start=False,
            crop_end=False,
            time_window=False, diff_t_window=None, con_t_window=None):
    df = concat_dfs(min_time_diff, lst_videos, crop_start, crop_end, time_window, diff_t_window, con_t_window)
    df = drop_columns(df, motility=motility, intensity=intensity)
    df = normalize_tracks(df, motility=motility, intensity=intensity)

    occurrences = df.groupby(["label"]).size()
    labels = []
    for label in df["label"].unique():
        if (min_length <= occurrences[label] <= max_length):
            labels.append(label)
    df = df[df["label"].isin(labels)]
    df = df.sample(frac=1).reset_index(drop=True)

    y = pd.Series(df['target'])
    y.index = df["label"]
    y = get_unique_indexes(y)
    df = df.drop("target", axis=1)
    return df, y

def extract_distinct_features(df, feature_list):
    df = extract_features(df, column_id="label", column_sort="t")
    impute(df)
    return df[feature_list]


def get_prob_over_track(clf, track, window, features_df, moving_window=False, aggregate_windows=False):
    '''
    Returns a list of the probability of being differentiated, for each track portion
    :param clf: classifier
    :param track: cell's track
    :param window: the size of the track's portion
    :param features_df: dataframe to take its features, fir using the same features on the tested data
    :return: list of probabilities
    '''
    true_prob = []

    step_size = 1 if moving_window or aggregate_windows else window

    if aggregate_windows:
        for i in range(1, len(track), step_size):
            track_portion = track[0:i * window]
            X = extract_distinct_features(df=track_portion, feature_list=features_df.columns)
            probs = clf.predict_proba(X)
            true_prob.append(probs[0][1])
            print(f"track portion: [{0}:{i * window}]")
            print(clf.classes_)
            print(probs)
            if len(track_portion) >= len(track):
                return true_prob

    else:
        for i in range(0, len(track), step_size):
            if i + window > len(track):
                break
            track_portion = track[i:i + window]
            X = extract_distinct_features(df=track_portion, feature_list=features_df.columns)
            probs = clf.predict_proba(X)
            true_prob.append(probs[0][1])
            print(f"track portion: [{i}:{i + window}]")
            print(clf.classes_)
            print(probs)

    return true_prob


def get_patches(track, bf_video):
    '''
    Returns list of cell crops (images) from a video, according to it's track
    :param track: the cell's track
    :param bf_video: video's path
    :return: list of crops
    '''
    image_size = 32
    im = io.imread(bf_video)
    crops = []
    for i in range(len(track)):
        x = int(track.iloc[i]["x"])
        y = int(track.iloc[i]["y"])
        single_cell_crop = im[int(track.iloc[i]["t_stamp"]), y - image_size:y + image_size,
                           x - image_size:x + image_size]
        crops.append(single_cell_crop)
    return crops


def plot_cell_probability(cell_ind, bf_video, clf, track, window, target_val, features_df, text, path=None):
    '''
    plot image crops together with their probability of being differentiated
    :param cell_ind: the index of the cell (in the dataframe)
    :param bf_video: video's path
    :param clf: classifier
    :param track: cell's track
    :param window: the size of the track's portion to calculate its probability
    :param target_val: True- REK treatment, False- control
    :param features_df: dataframe to take its features, fir using the same features on the tested data
    :param text: insert text on the figure
    :param path: path of a directory to save the figure to
    :return:-
    '''

    # compute tsfresh features
    X_full_track = extract_distinct_features(df=track, feature_list=features_df.columns)

    # predict the full track's probability of being differentiated
    pred = clf.predict(X_full_track)
    total_prob = clf.predict_proba(X_full_track)[0][1]

    # calculate list of probabilities per window
    true_prob = get_prob_over_track(clf, track, window, features_df)

    # create images crops of the cell during its track, adjust them to the window's splits
    cell_patches = get_patches(track, bf_video)
    windowed_cell_patches = [cell_patches[i] for i in range(0, len(cell_patches), window)]

    # plot probability over time
    plt.figure(figsize=(20, 6))
    fig, ax = plt.subplots()

    # plot the probability
    track_len = len(track)
    ax.scatter(range(0, track_len, window), true_prob)

    # add images on the scattered probability points
    for x0, y0, patch in zip(range(0, track_len, window), true_prob, windowed_cell_patches):
        ab = AnnotationBbox(OffsetImage(patch, 0.32), (x0, y0), frameon=False)
        ax.add_artist(ab)
        plt.gray()
        plt.grid()

    # plot the line between the probability points
    ax.plot(range(0, track_len, window), true_prob)

    # adjust axes
    label_time = [(track.iloc[val]['t']) * 90 / 60 / 60 for val in range(0, track_len, 2 * window)]
    plt.xticks(range(0, track_len, 2 * window), labels=np.around(label_time, decimals=1))
    plt.ylim(0.2, 1, 0.05)
    plt.grid()

    # add title and labels
    plt.title(f"cell #{cell_ind} probability of differetniation")
    plt.xlabel("time (h)")
    plt.ylabel("prob")

    # add target
    plt.text(0.1, 0.9, f'target: {target_val}', ha='center', va='center', transform=ax.transAxes)

    # total track's prediction probability
    plt.text(0.2, 0.8, f'total track prediction: {pred[0]}, {total_prob}',
             ha='center', va='center', transform=ax.transAxes)
    # add additional entered text
    plt.text(0.5, 0.9, text, ha='center', va='center', transform=ax.transAxes)

    # save image
    if path:
        print(path)
        plt.savefig(path + ".png")
    plt.show()


def plot_sampled_cells(track_length, clf, features_df, dir_name, con_diff, bf_video, tracks, n_cells=10):
    '''
    plot probability over time (with image crops), for several sampled cells
    :param track_length: minimal track length to plot
    :param clf: the classifier
    :param features_df: dataframe to take its features, fir using the same features on the tested data
    :param dir_name: directory path to save the outputs to
    :param con_diff: adds the inserted value to the images paths ("control" or "ERK")
    :param bf_video: video's path
    :param tracks: list of all cells tracks
    :param n_cells: how many cells to plot
    :return: -
    '''
    count = 0
    # iterate through all of the tracks
    for cell_ind, curr_track in enumerate(tracks):

        # skip the track if its shorter that 'track_length'
        if len(curr_track) < track_length:
            continue

        # plot only 'ne_cells' plots
        if count > n_cells:
            continue

        count += 1
        # plot cell's probability over time
        plot_cell_probability(cell_ind=cell_ind, bf_video=bf_video, clf=clf, track=curr_track, window=40,
                              target_val=True, features_df=features_df,
                              text="", path=dir_name + "/" + con_diff + "_" + str(cell_ind))


def get_path(path):
    return path if os.path.exists(path) else "muscle-formation-diff/" + path


def save_data(dir_name, clf, X_train, X_test, y_train, y_test):
    # save the model & train set & test set
    pickle.dump(X_train, open(dir_name + "/" + "X_train", 'wb'))
    pickle.dump(X_test, open(dir_name + "/" + "X_test", 'wb'))
    pickle.dump(y_test, open(dir_name + "/" + "y_test", 'wb'))
    pickle.dump(y_train, open(dir_name + "/" + "y_train", 'wb'))
    joblib.dump(clf, dir_name + "/" + "clf.joblib")


def load_data(dir_name):
    # load the model & train set & test set
    clf = joblib.load(dir_name + "/clf.joblib")
    X_train = pickle.load(open(dir_name + "/" + "X_train", 'rb'))
    X_test = pickle.load(open(dir_name + "/" + "X_test", 'rb'))
    y_train = pickle.load(open(dir_name + "/" + "y_train", 'rb'))
    y_test = pickle.load(open(dir_name + "/" + "y_test", 'rb'))
    return clf, X_train, X_test, y_train, y_test


if __name__ == '__main__':
    print(
        "Let's go! In this script, we will train ")

    # params
    motility = True
    intensity = False
    min_length = 0
    max_length = 950
    min_time_diff = 0
    auc_scores = []
    window = 40

    # split videos into their experiments
    exp_1 = [1, 2, 3, 4]
    exp_2 = [5, 6, 7, 8]
    exp_3 = [9, 10, 11, 12]

    # create combinations for leave one out training
    train_video_lists = [list(itertools.chain(exp_1, exp_2)),
                         list(itertools.chain(exp_1, exp_3)), list(itertools.chain(exp_2, exp_3))]
    test_video_lists = [exp_3, exp_2, exp_1]

# rf_best_prms, xgb_best_prms = nested_cross_validation(X_train, y_train)
# xgb_model = retrain_model(XGBClassifier(), xgb_best_prms, X_train, X_test, y_train, y_test)
# rf_model = retrain_model(RandomForestClassifier(), rf_best_prms, X_train, X_test, y_train, y_test)