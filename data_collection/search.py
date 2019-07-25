#! /usr/bin/python

from time import strftime
import datetime
import time
import sys
import os
import re
import urllib
import re

from twython import Twython, TwythonStreamer
import paramiko
from scp import SCPClient

LIMIT = 10000

APP_KEY = ""
APP_SECRET = ""
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

sing_attr = ['text','id','source','lang']
nested_attr = {'user':['id','screen_name','verified','followers_count','friends_count','statuses_count','location','description'],'place':['full_name','id']}

URL_PATTERN = re.compile("^((ht|f)tp(s?)\:\/\/|~/|/)?([\w]+:\w+@)?([a-zA-Z]{1}([\w\-]+\.)+([\w]{2,5}))(:[\d]{1,5})?((/?\w+/)+|/?)(\w+\.[\w]{3,4})?((\?\w+=\w+)?(&\w+=\w+)*)?")

def convert_query(query):
    parts = re.split("___|PersonY", query)
    return '"' + '" "'.join(parts) + '"'

def get_results(twitter, query, count = 100):

    query = convert_query(query)
    full_query = query + " exclude:retweets -filter:links -filter:media"
    encoded_query = urllib.parse.quote_plus(full_query)
    params = {'q':full_query, 'lang':'en', 'result_type':'recent', 'count':str(count), 'tweet_mode':'extended'}
    successful = False
    result = None
    while not successful:
        try:
            result = twitter.search(**params)
            successful = True
        except Exception as e:
            print (e)
            # wait 900 sec = 15 min
            print ("waiting 15 minutes...")
            sys.stdout.flush()
            time.sleep(900)
    return result

def test():
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    queries = ['summer vacation ___ great']
    for query in queries:
        results = get_results(twitter, query, 5)
        print ("Metadata")
        print (results['search_metadata'])
        print
        print ("Statuses")
        print (results.keys())
        for result in results['statuses']:
            print ("--- " + result['full_text'])
        for k,v in result.items():
            print (k + ", " + v)
        print
#        print
#            print
#        print result['full_text'] #handle results here

def get_user_profiles(twitter, uid_list):
    params = {'user_id':uid_list}
    successful = False
    result = None
    while not successful:
        try:
            result = twitter.lookup_user(**params)
            successful = True
        except Exception as e:
            print (e)
            # 404 is not found
            # 401 is not authorized
            if '429' in str(e):
                # wait 900 sec = 15 min
                sys.stderr.write("waiting 15 minutes...\n")
                time.sleep(900)
            else:
                sys.stderr.write("Error: " + str(e) + '\n')
                return None

    return result


def get_user_timeline_(twitter, uid, max_id=None, count=200):
    params = {'user_id':uid, 'lang':'en', 'result_type':'recent', 'count':str(count), 'trim_user':'true', 'tweet_mode':'extended','include_rts':'false'}
    if max_id:
        params['max_id'] = max_id
    successful = False
    result = None
    while not successful:
        try:
            result = twitter.get_user_timeline(**params)
            successful = True
        except Exception as e:
            print (e)
            # 404 is not found
            # 401 is not authorized
            if '429' in str(e):
                # wait 900 sec = 15 min
                print ("waiting 15 minutes...")
                sys.stdout.flush()
                time.sleep(900)
            else:
                print ("Error " + str(e))
                return None

    return result

def get_min_id(r):
    m = sys.maxsize
    for res in r:
        if res['id'] < m:
            m = res['id']
    return m

def get_profiles_from_users(user_ids_file, user_profile_dir):

    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    profiles_output = []

    with open(user_ids_file) as user_ids_fh:
        uid_list = []
        for line in user_ids_fh.readlines():

            uid = line.strip()
            uid_list.append(uid)

            if len(uid_list) >= 100:
                results = get_user_profiles(twitter, ', '.join(uid_list))
                if results == None:
                    continue
                for result in results:
                    outline = str(result['id']) + ',' + result['location'] + '\t' + result['description'].replace('\n','<EOL>')
                    profiles_output.append(outline)
                    #print (outline.encode('utf-8'))
                uid_list = []

    #print (profiles_output)

    with open(user_profile_file, 'w', encoding='utf-8') as user_profile_file_handle:
        user_profile_file_handle.writelines(["%s\n" % item  for item in profiles_output])

def get_tweets_from_users(user_ids_file, output_dir):

    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    with open(user_ids_file) as user_ids_fh:

        for line in user_ids_fh.readlines():

            uid = line.strip()
            print ("User: " + uid)
            print ("Time: " +  str(datetime.datetime.now()))

            prev_min_id = -1
            with open(output_dir.rstrip(os.sep) + os.sep + str(uid) + '.tweets','w') as out:
                results = get_user_timeline_(twitter, uid)
                if results:
                    min_id = get_min_id(results)
                    while prev_min_id != min_id:
                        print (len(results), "results")
                        for result in results:
                            tweet = result['full_text']
                            tid = int(result['id'])
                            print ('cur ',tid)
                            if tid < min_id:
                                min_id = tid
                            print ('min ', min_id)
                            tweet = tweet.replace("\n",'\\n').encode('utf8')
                            print (tweet)
                            out.write(str(tweet) + '\n')
                        results = get_user_timeline_(twitter, uid, min_id - 1)
                        prev_min_id = min_id
                        if results:
                            min_id = get_min_id(results)
                        else:
                            prev_min_id = -1
                            min_id = -1
                        print ('prev ', prev_min_id)
                        print ('new_min ', min_id)

def get_tweets_from_queries(queries_file, output_file, user_id_file):

    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    with open(output_file,'w') as out:
        out.write("QueryID,Query,UserID,TweetID,Tweet\n")

    user_ids = []

    with open(queries_file) as queries_fh:
        for line in queries_fh.readlines():
            qid, query = line.split(',',1)
            query = query.strip()
            results = get_results(twitter, query)
            for result in results['statuses']:
                # store tweetid, userid, and tweet content
                tweet = result['full_text']
                tid = result['id']
                uid = result['user']['id']
                user_ids.append(uid)
                tweet = tweet.replace("\n","\\n").encode('utf8')
                with open(output_file,'a') as out:
                    out.write( str(qid)+','+str(query)+','+str(uid)+','+str(tid)+','+ str(tweet)+'\n' )

    with open(user_id_file, 'w') as user_id_fh:
        user_id_fh.writelines(["%s\n" % item  for item in user_ids])

#test()

if __name__ == "__main__":
    user_id_file = "valid_user_ids.txt"
    user_profile_dir = "profiles_out"
    output_dir = "output_tweets"
    query_file = "query.txt"
    query_output_file = "query_output.txt"

    get_tweets_from_queries(query_file, query_output_file, user_id_file)
    get_profiles_from_users(user_id_file, user_profile_dir)
    get_tweets_from_users(user_id_file, output_dir)

