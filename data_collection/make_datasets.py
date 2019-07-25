# -*- coding: utf-8 -*-

# make both the "full" dataset and and "small" dataset in one shot!
# let's do this independent of the cluster assignment

# let's use
# 200k for train
# 10k for test
# the rest for dev

# inputs:
# - valid_user_list
# - user_tweets_dir (no q)
# - cluster assignments (file that is userid, clusters)
# - user_profiles
# - user values
# - user acts (no q)

# - full data dir path
# - small data dir path

# outputs:
# - full data dir will have : dev, train, test
# - in each of those: clusters, profiles, tweets, values
# - in each of those: 1 file per user
# - small data dir will have: all of the same things, except:
# -- generate list of valid users from the list of users that were
#    assigned to the "dev" set from the previous step

import os
import random
import shutil
import sys

FULL_TRAIN_SIZE = 200
FULL_TEST_SIZE = 28
SMALL_TRAIN_SIZE = 50
SMALL_TEST_SIZE = 10

def load_user_list_from_file(path):
    return [x.strip() for x in open(path).readlines()]

# copy files in file list from source to dest, adding extension to the end of each file name in src (but not dst)
def dir2dir_copy(source_dir, dest_dir, file_list, extension=""):
    dest_dir += os.sep
    for file_name in file_list:
        src = source_dir + file_name + extension
        dst = dest_dir + file_name
        try:
            shutil.copy(src,dst)
        except:
            pass

def file2dir_copy(source_file_path, dest_dir, valid_list, split_char=None, valid_col=0, data_col=-1, num_splits=-1):
    dest_dir = str(dest_dir) + "/"
    found_set = set([])

    print(source_file_path)
    print(dest_dir)

    with open(source_file_path) as source_file:
        for line in source_file:
            line = line.strip('\n')
            #parts = line.split(split_char,num_splits)
            parts = line.split(',')
            out_file_name = parts[0]
            if out_file_name in valid_list:
                found_set.add(out_file_name)
                with open(dest_dir + os.sep + out_file_name,'w') as out_file:
                    out_file.write(parts[data_col] + '\n')

    #valid_list = valid_list.replace("{", "")
    #valid_list = valid_list.replace("}", "")
    #valid_list_split = valid_list.split(",")

    #if len(found_set) != len(valid_list_split):
    #    unfound = set(valid_list_split) - found_set
    #    print("While searching",source_file_path,", didn't find entries for these users:",unfound)

def make_single_dataset(user_list, user_tweets_dir, user_acts_dir, cluster_file_path, profiles_path, \
                            values_path, out_dir, train_size, test_size):

    num_users = len(user_list)
    assert train_size + test_size <= num_users

    print("Creating directories...")
    sys.stdout.flush()

    # make all of the directories where we will store the data
    for split in ['train','dev','test']:
        for item in ['clusters','profiles','tweets','values','activities']:
            if not os.path.exists(out_dir + split + os.sep + item):
                os.makedirs(out_dir + split + os.sep + item)

    print("done.\nCreating splits...")
    sys.stdout.flush()

    # assign users to splits
    # shuffle user_list in place
    random.shuffle(user_list)
    # make the splits
    train_user_list = user_list[:train_size]
    test_user_list = user_list[train_size:train_size + test_size]
    dev_user_list = user_list[train_size + test_size:]

    print("done.")
    sys.stdout.flush()

    # for each of train, dev, and test
    for split_user_list, split in zip([train_user_list, dev_user_list, test_user_list],\
                                      ['train','dev','test']):

        print("starting to create data for split:",split)
        sys.stdout.flush()

        split_user_set = set(split_user_list)
        split_dir = out_dir + split + os.sep

        # create the cluster files in the clusters dir
        print("creating cluster files...")
        sys.stdout.flush()
        file2dir_copy(cluster_file_path, split_dir + 'clusters', split_user_set, num_splits=1)

        # create the profiles files in the profiles dir
        print("done.\ncreating profile files...")
        sys.stdout.flush()
        file2dir_copy(profiles_path, split_dir + 'profiles', split_user_set, split_char='\t', num_splits=2)

        # create the values files in the values dir
        print("done.\ncreating values files...")
        sys.stdout.flush()
        file2dir_copy(values_path, split_dir + 'values', split_user_set, num_splits=1)

        # move the tweets into the correct subdirectory
        print("done.\nmoving tweets...")
        sys.stdout.flush()
        dir2dir_copy(user_tweets_dir, split_dir + 'tweets', split_user_set, ".tweets")

        # move the activities into the correct subdirectory
        print("done.\nmoving activities...")
        sys.stdout.flush()
        dir2dir_copy(user_acts_dir, split_dir + 'activities', split_user_set, ".acts")

        print("done.")
        sys.stdout.flush()


def make_datasets(valid_user_list_path, user_tweets_dir, user_acts_dir, cluster_file_path, profiles_path, \
                    values_path, full_data_dir, small_data_dir):

    # ensure base directories have exactly one separator
    user_tweets_dir = user_tweets_dir.rstrip(os.sep) + os.sep
    user_acts_dir = user_acts_dir.rstrip(os.sep) + os.sep
    full_data_dir = full_data_dir.rstrip(os.sep) + os.sep
    small_data_dir = small_data_dir.rstrip(os.sep) + os.sep

    print("Making full dataset...")
    sys.stdout.flush()

    # make the full dataset
    user_list = load_user_list_from_file(valid_user_list_path)
    make_single_dataset(user_list, user_tweets_dir, user_acts_dir, cluster_file_path, profiles_path, \
                            values_path, full_data_dir, FULL_TRAIN_SIZE, FULL_TEST_SIZE)

    print("Making small dataset...")
    sys.stdout.flush()

    # make the small dataset (i.e., make splits over the dev dataset)
    small_user_list = os.listdir(full_data_dir + 'dev' + os.sep + 'profiles')
    make_single_dataset(user_list, user_tweets_dir, user_acts_dir, cluster_file_path, profiles_path, \
                            values_path, small_data_dir, SMALL_TRAIN_SIZE, SMALL_TEST_SIZE)

if __name__ == "__main__":
    # valid_users tweets_dir acts_dir clusters_file profiles_file values_file full_out_dir small_out_dir

    valid_users = 'valid_user_ids.txt'
    tweets_dir = 'converted_tweets'
    clusters_file = 'cluster_tweets_out.txt'
    profiles_file = 'profiles_out'
    full_out_dir = 'full_out'
    small_out_dir = 'small_out'
    acts_dir = 'activities_dir'
    values_file = 'values.txt'
 
    make_datasets(valid_users, tweets_dir, acts_dir, clusters_file, profiles_file, values_file, full_out_dir, small_out_dir) 
