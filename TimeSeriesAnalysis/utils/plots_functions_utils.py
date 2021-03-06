import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.metrics import roc_curve
import pandas as pd


def plot_roc(clf, X_test, y_test, path):
    # plt.figure(figsize=(20, 6))
    # roc curve for models
    fpr1, tpr1, thresh1 = roc_curve(y_test, clf.predict_proba(X_test)[:, 1], pos_label=1)

    # roc curve for tpr = fpr
    random_probs = [0 for i in range(len(y_test))]
    p_fpr, p_tpr, _ = roc_curve(y_test, random_probs, pos_label=1)

    plt.style.use('seaborn')
    # plot roc curves
    plt.plot(fpr1, tpr1, linestyle='--', color='orange', label='Random Forest')
    plt.plot(p_fpr, p_tpr, linestyle='--', color='blue')
    # title
    plt.title('ROC curve')
    # x label
    plt.xlabel('False Positive Rate')
    # y label
    plt.ylabel('True Positive rate')

    plt.legend(loc='best')
    plt.savefig(path + "/" + 'ROC', dpi=300)
    plt.show()
    plt.close()
    plt.clf()


def build_pca(num_of_components, df):
    """
    The method creates component principle dataframe, with num_of_components components
    :param num_of_components: number of desired components
    :param df: encoded images
    :return: PCA dataframe
    """
    pca = PCA(n_components=num_of_components)
    principal_components = pca.fit_transform(df)
    columns = ['principal component {}'.format(i) for i in range(1, num_of_components + 1)]
    principal_df = pd.DataFrame(data=principal_components, columns=columns)
    return principal_df, pca


def plot_pca(principal_df, pca, path):
    """
    The method plots the first 3 dimensions of a given PCA
    :param path: path for saving the graph
    :param pca: pca object
    :param principal_df: PCA dataframe
    :return: no return value
    """
    variance = pca.explained_variance_ratio_
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        x="principal component 1", y="principal component 2",
        hue='principal component 3',
        palette=sns.color_palette("hls", len(principal_df['principal component 3'].unique())),
        data=principal_df,
        legend=False,
        alpha=0.3
    )
    plt.xlabel(f"PC1 ({variance[0]}) %")
    plt.ylabel(f"PC2 ({variance[1]}) %")
    plt.title("PCA")
    plt.savefig(path + "/pca.png")
    plt.show()
    plt.close()
    plt.clf()


def plot_feature_importance(clf, feature_names, path):
    # Figure Size
    top_n = 30
    fig, ax = plt.subplots(figsize=(16, 9))

    sorted_idx = clf.feature_importances_.argsort()

    ax.barh(feature_names[sorted_idx[-top_n:]], clf.feature_importances_[sorted_idx[-top_n:]])
    # Add padding between axes and labels
    ax.xaxis.set_tick_params(pad=5)
    ax.yaxis.set_tick_params(pad=50)

    plt.xlabel("Random Forest Feature Importance")
    plt.title('Feature Importance Plot')
    plt.savefig(path + "/feature importance.png")
    plt.show()
    plt.close()
    plt.clf()
