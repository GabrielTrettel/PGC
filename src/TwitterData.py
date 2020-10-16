#!/usr/bin/python3.8
import os, toml, sys, datetime, json, time, signal
import tweepy as tw
from tqdm import tqdm


class TwitterDriver:
    def __init__(self, config_file):
        self.config_f = config_file

        self.config_values = self.__parse_keys()
        self.api = self.__create_api_handler()

        self.tw_attrs = ['id_str', 'lang', 'retweeted', 'text']
        self.user_attr = ['id_str', 'name', 'screen_name', 'description']
        self.still_compute = True
        self.closing_requests = 0
        signal.signal(signal.SIGINT, self.signal_handler)

    def __parse_keys(self):
        with open(self.config_f) as f:
            key_values = toml.loads(f.read())
            return key_values

    def signal_handler(self, sig, frame):
        print('Okay, closing!')
        self.closing_requests += 1
        if self.closing_requests > 3: sys.exit()
        self.still_compute = False


    def __create_api_handler(self):
        oaut = self.config_values['autentication']
        api_key = oaut['api_key']
        api_key_secret = oaut['api_key_secret']
        access_token = oaut['access_token']
        access_token_secret = oaut['access_token_secret']

        auth = tw.OAuthHandler(api_key, api_key_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tw.API(auth, wait_on_rate_limit=True)
        return api


    def tweets_ids_from_file(self):
        cfg =  self.config_values['download_tweets_from_list']
        init_idx  = cfg['start_by_line']
        file_name = cfg['tweets_list_file']

        content = 'h'
        for i,line in enumerate(open(file_name, 'r')):
            if i < init_idx:
                continue
            if not self.still_compute or len(content) <= 0:
                break

            content = line.strip()
            print(f"{i} \t {content} \t", end='')

            time.sleep(0.1)
            yield i, [content]


    def __request_tweet_data(self, tw_ids, i):
        try:
            result = self.api.statuses_lookup(id_=tw_ids, map_=True)
            return result

        except tw.RateLimitError:
            print(f"\nRequest timeout in {i} request")
            time.sleep(15 * 60)
            self.__request_tweet_data(tw_ids, i)

        except tw.TweepError:
            print(f"skipped due error")
            time.sleep(0.1)


    def save_user_description(self, user):
        out_folder = self.config_values['download_tweets_from_list']['save_on']
        user_description_folder = out_folder+user[0] + '/'
        os.mkdir(user_description_folder)
        with open(user_description_folder + f'user-{user[0]}', 'w') as f:
            user_str = '|'.join(self.user_attr) + '\n'
            user_str += '|'.join(user)
            f.writelines(user_str)


    def save_tweet_data(self, data, user_id):
        out_folder = self.config_values['download_tweets_from_list']['save_on']
        with open(out_folder+user_id+'/'+data[0], 'w') as f:
            tweet_data = '|'.join(data[:-1]) + '\n' + data[-1]
            f.writelines(tweet_data)


    def persist_into_disk(self, user_data, tweet_data):
        out_folder = self.config_values['download_tweets_from_list']['save_on']
        users = set(os.listdir(out_folder))
        if user_data[0] not in users:
            self.save_user_description(user_data)

        self.save_tweet_data(tweet_data, user_data[0])


    def log_tweet(self, tw_id):
        file = self.config_values['download_tweets_from_list']['saved_tweets_log']
        with open(file, 'a') as f:
            f.write(tw_id)


    def __parse_and_save_data(self, result, i):
        if not result: return
        for tw in result:
            try:
                user_data  = [str(getattr(tw.user, attr, None)) for attr in self.user_attr]
                tweet_data = [str(getattr(tw, attr, None)) for attr in self.tw_attrs]
                self.persist_into_disk(user_data, tweet_data)
                self.log_tweet(tweet_data[0])
                print(f'Fetched')
            except AttributeError:
                print("A wild attribute error happened")



    def get_data_from_tweets_ids(self):
        for i,tw_ids in self.tweets_ids_from_file():
            data = self.__request_tweet_data(tw_ids,i)
            self.__parse_and_save_data(data, i)


if __name__ == '__main__':
    init_file = sys.argv[1]
    td = TwitterDriver(init_file)
    td.get_data_from_tweets_ids()
