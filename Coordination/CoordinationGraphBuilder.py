# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 16:52:27 2020

@author: Amit Shakarchy
"""
from matplotlib.colors import ListedColormap
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import pickle
import numpy as np
# from DataPreprocessing.load_tracks_xml import load_tracks_xml
import pandas as pd


class CoordinationGraphBuilder():

    def read_coordination_df(self, coord_df, pkl=False):
        '''
        The method receives a coordination dataframe and calculates its mean value for each time point.
        :param coord_df: coordination dataframe
        :return: mean coordination for each time point
        '''
        if not pkl:
            coord_df["Spot frame"] = coord_df["cos_theta"].apply(lambda x: x[0])
            coord_df["cos_theta_"] = coord_df["cos_theta"].apply(lambda x: x[1])
            mean_cos_theta = coord_df.groupby("Spot frame")["cos_theta_"].mean()
            std_cos_theta = coord_df.groupby("Spot frame")["cos_theta_"].std()
        else:
            mean_time = None
            K = coord_df.shape[0]
            ar = np.zeros((K, 927))
            ar[:] = np.nan
            time = np.zeros((K, 927))
            time[:] = np.nan
            for i in range(K):
                t0 = int(coord_df['t0'].iloc[i])
                cost = coord_df['cos_theta'].iloc[i]
                time_ = coord_df['t0'].iloc[i]
                N = len(cost)
                ar[i, t0:t0 + N] = cost
                time[i, t0:t0 + N] = time_ * 5 / 60
            mean_cos_theta = np.nanmean(ar, axis=0)
            std_cos_theta = np.nanstd(ar, axis=0)
            mean_time = np.nanmean(time, axis=0)
        return std_cos_theta, mean_cos_theta

    def get_mean_coordination(self, ind1, ind2):
        elements_num = 2
        coord_length = 927
        pickle_path = r'coordination_outputs/coordination_dfs/different_densities/small field of view/coordination_df_s{}_30_small.pkl'
        total_coord = np.zeros(shape=(coord_length,))
        total_time = np.zeros(shape=(coord_length,))
        for i in (ind1, ind2):
            df = pickle.load(
                open(pickle_path.format(i), 'rb'))
            coord, time = self.read_coordination_df(df)
            total_time += time
            total_coord += coord
        return total_coord / elements_num, total_time / elements_num

    def plot_coord_over_time(self, coordination_dfs, name_for_saving, legend, line_styles,
                             label_casting_param=0.025, pkl=False):
        '''
        The method plots average coordination over time, of all of the cells in the given dataframes
        :param coordination_dfs: list of coordination dataframes to display [coord1, coord2, ... ]
        :param name_for_saving: wanted file name
        :param legend: list containing labels of the coordination dataframes ["coord1", "coord2", ... ]
        :param line_styles: list of line styles ['--', '-', None... ]
        :param label_casting_param: casting parameter for adjusting xticks to the experiment times in hours. usually * 1.5 / 60
        :return: -
        '''
        if pkl:
            fig = plt.figure(figsize=(6, 4))
            for (coord_df, style) in zip(coordination_dfs, line_styles):
                std_cos_theta, mean_cos_theta = self.read_coordination_df(coord_df, pkl)
                # mean_cos_theta.index = mean_cos_theta.index * 5 / 60
                # std_cos_theta.index = std_cos_theta.index * 5 / 60
                # m_std = mean_cos_theta - std_cos_theta
                # p_std = mean_cos_theta + std_cos_theta
                # plt.fill_between([i  for i in range(927)], m_std, p_std, alpha=0.2)
                plt.plot(pd.DataFrame(mean_cos_theta[:550]).rolling(window=10).mean(), linestyle=style)
            plt.legend(legend)
            plt.title(r'Cos of $\theta$ measure')
            plt.xticks(np.arange(0, 550, 100),
                       labels=np.around(np.arange(0, 550, 100) * label_casting_param * 2, decimals=1))
            plt.ylim(0.6, 1, 0.5)
            # plt.xlim(0, 22, 0.5)
            plt.xlabel('Time [h]')
            plt.ylabel(r'Cos of $\theta$')
            plt.savefig(name_for_saving)
            plt.show()
            plt.close(fig)
        else:
            fig = plt.figure(figsize=(6, 4))
            for (coord_df, style) in zip(coordination_dfs, line_styles):
                std_cos_theta, mean_cos_theta = self.read_coordination_df(coord_df, pkl)
                mean_cos_theta.index = mean_cos_theta.index * 5 / 60
                std_cos_theta.index = std_cos_theta.index * 5 / 60
                # m_std = mean_cos_theta - std_cos_theta
                # p_std = mean_cos_theta + std_cos_theta
                # plt.fill_between([i  for i in range(927)], m_std, p_std, alpha=0.2)
                plt.plot(pd.DataFrame(mean_cos_theta).rolling(window=1).mean(), linestyle=style)
            plt.legend(legend)
            plt.title(r'Cos of $\theta$ measure')
            # plt.xticks(np.arange(0, 550, 100),
            #            labels=np.around(np.arange(0, 550, 100) * label_casting_param * 2, decimals=1))
            plt.ylim(0.6, 1, 0.5)
            plt.xlim(0, 22, 0.5)
            plt.xlabel('Time [h]')
            plt.ylabel(r'Cos of $\theta$')
            plt.savefig(name_for_saving)
            plt.show()
            plt.close(fig)


    def get_density(self, tracks_xml):
        '''
        Calculates the density in a plate for each time point.
        :param tracks_xml: path of the tracking XML file
        :return: numpy array with density values
        '''
        tracks, df = load_tracks_xml(tracks_xml)
        s01den = np.empty((len(tracks), 926))
        for k, track in enumerate(tracks):
            start = int(np.min(np.asarray(track['t_stamp'])))
            stop = int(np.max(np.asarray(track['t_stamp'])))
            s01den[k, start:stop] = 1
        s01out = np.sum(s01den, axis=0)
        return s01out

    def get_coord_density_df(self, coord_df, coord_xml_path):
        '''
        Calculates density dataframe, with density values and coordination values for each time point
        :param coord_df: coordination dataframe
        :param coord_xml_path: matching XML tracking file
        :return: dataframe
        '''
        # Read coordination DFs
        coord, time = self.read_coordination_df(coord_df)
        # Get density from xml
        density = self.get_density(coord_xml_path)

        # Attach to one DF
        df = pd.DataFrame({'density': pd.DataFrame(density)[0][:920],
                           'coordination': pd.DataFrame(coord)[0][:920],
                           'time': pd.DataFrame(time)[0][:920]})
        return df

    def get_mean_density(self, ind1, ind2, ind3):
        elements_num = 3
        coord_length = 926
        xml_path = r"../data/tracks_xml/Adi/201209_p38iexp_live_1_Widefield550_s{}_all_8bit_ScaleTimer.xml"
        total_density = np.zeros(shape=(coord_length,))
        for i in (ind1, ind2, ind3):
            density = self.get_density(xml_path.format(i))
            total_density += density
        return total_density / elements_num

    def get_mean_density_df(self, ind1, ind2, ind3):
        mean_den = self.get_mean_density(ind1, ind2, ind3)
        mean_coord, time = self.get_mean_coordination(1, 2, 3)
        # Attach to one DF
        den_df = pd.DataFrame({'density': pd.DataFrame(mean_den)[0][:920],
                               'coordination': pd.DataFrame(mean_coord)[0][:920],
                               'time': pd.DataFrame(time)[0][:920]})
        return den_df

    def plot_coord_over_density(self, coordination_dfs, xml_paths, name_for_saving, colors, labels, cmaps):
        '''
        The method plots coordination over density of all given coordination dataframes
        :param coordination_dfs: list of coordination dataframes to display [coord1, coord2, ... ]
        :param xml_paths: list of xml tracking files [XML_path_1, XML_path_1, ... ]
        :param name_for_saving: wanted file name
        :param colors: list of line colors ["blue", "orange", ... ]
        :param labels: list containing labels of the coordination dataframes ["coord1", "coord2", ... ]
        :param cmaps: list of color-maps to display change in time [cmap1, cmap2, ... ]
        :return: -
        '''

        fig = plt.figure(figsize=(8, 4))
        for (coord_df, xml_path, color, label, cmap) in zip(coordination_dfs, xml_paths, colors, labels, cmaps):
            density_df = self.get_coord_density_df(coord_df, xml_path)
            plt.scatter(x=density_df["density"], y=density_df["coordination"], marker=".", color=color,
                        label=label)
            scatter = plt.scatter(x=density_df["density"], y=density_df["coordination"],
                                  c=density_df["time"], marker=".", cmap=cmap)
            plt.colorbar(scatter, shrink=0.6)

        plt.legend(labels)

        plt.ylim(0.6, 1, 0.5)
        plt.title(r'Cos of $\thet'
                  r'a$ measure (Coordination over Density)')
        plt.xlabel('Density')
        plt.ylabel(r'Cos of $\theta$')
        plt.savefig(name_for_saving)
        plt.show()
        plt.close(fig)


if __name__ == '__main__':
    print()
    coord_diff_path = r"coordination_outputs/coordination_dfs/Adi/coordination_df_s4_Adi.pkl"
    coord_diff = pickle.load(open(coord_diff_path, 'rb'))

    coord_con_path = r"coordination_outputs/coordination_dfs/Adi/coordination_df_s1_Adi.pkl"
    coord_con = pickle.load(open(coord_con_path, 'rb'))

    coord_p38_path = r"coordination_outputs/coordination_dfs/Adi/coordination_df_s8_Adi.pkl"
    coord_p38 = pickle.load(open(coord_p38_path, 'rb'))

    coord_p38_erk_path = r"coordination_outputs/coordination_dfs/Adi/coordination_df_s12_Adi.pkl"
    coord_p38_erk = pickle.load(open(coord_p38_erk_path, 'rb'))

    null_coord_path = r"coordination_outputs/coordination_dfs/validations/null_model_s5.pkl"
    null_coord = pickle.load(open(null_coord_path, 'rb'))

    # df = pd.DataFrame()
    # for i in range(len(null_coord)):
    #     row = null_coord.iloc[i]
    #     for t, cos_theta in enumerate(row["cos_theta"]):
    #         tmp_df = pd.DataFrame({"Track #": [row["Track #"]], "t0": [row["t0"]], "cos_theta": [(t, cos_theta)]})
    #         df = df.append(tmp_df, ignore_index=True)
    # pickle.dump(df, open(r"coordination_outputs/coordination_dfs/validations/null_model_2606.pkl", 'wb'))

    # select color maps
    GnBu_rBig = cm.get_cmap('Blues_r', 512)
    GnBu = ListedColormap(GnBu_rBig(np.linspace(0.25, 0.75, 256)))
    RdPu_rBig = cm.get_cmap('Oranges_r', 512)
    RdPu = ListedColormap(RdPu_rBig(np.linspace(0.25, 0.75, 256)))

    builder = CoordinationGraphBuilder()
    builder.plot_coord_over_time(coordination_dfs=[coord_con, coord_diff, coord_p38, coord_p38_erk, null_coord],
                                 name_for_saving="Coordination over time validation",
                                 legend=["control", "ERK", "p38", "ERKi + p38", "randomized null model"],
                                 label_casting_param=0.025,
                                 line_styles=[None, None, None, None, '--'],
                                 pkl=True)

    # builder.plot_coord_over_density(coordination_dfs=[coord_con, coord_diff], xml_paths=[xml_con_path, xml_diff_path],
    #                                 name_for_saving="manual_tracking_coordination_over_density 1,3",
    #                                 colors=["blue", "orange"],
    #                                 labels=["control", "ERK"], cmaps=[GnBu, RdPu])
