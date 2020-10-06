import os, toml, sys, datetime, json
import tweepy as tw


"""
created_at
id_str
text
metadata/iso_language_code
user/id
user/name
user/screen_name
user/location

retweeted_status/iso_language_code
retweeted_status/user/id
retweeted_status/user/screen_name
retweeted_status/user/location

http://docs.tweepy.org/en/v3.6.0/api.html#API.search_users
http://docs.tweepy.org/en/v3.6.0/api.html#API.user_timeline

"""




class TwitterDriver:
    def __init__(self, config_file):
        self.config_f = config_file

        self.config_values = self.__parse_keys()
        self.api = self.__create_api_handler()


    def __parse_keys(self):
        with open(self.config_f) as f:
            key_values = toml.loads(f.read())
            return key_values



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


    def __parse_since_date(self):
        time_val = self.config_values['query']['time']
        if type(time_val) is int:
            return (datetime.datetime.utcnow().date() -
                    datetime.timedelta(days=time_val)).isoformat()

        return time_val


    def __queries(self):
        query_attrs = self.config_values['query']
        q_filter = " -filter " + query_attrs['filter'] if query_attrs['filter'] != [] else ""

        for term in query_attrs['search']:
            query = term.strip() + q_filter
            yield query


    def __tweets(self, query):
        # since = self.__parse_since_date()
        # tweets = tw.Cursor(self.api.search,
                           # q=query,
                           # since=since,
                           # ).items()

        tweets = self.api.user_timeline(user_id="1089609639786889216")


        for tweet in tweets:
            yield tweet


    def data(self):
        for query in self.__queries():
            for tweet in self.__tweets(query):
                print(json.dumps(tweet._json , indent=4))
                # print(tweet)
                # return


if __name__ == '__main__':
    init_file = sys.argv[1]
    td = TwitterDriver(init_file)
    td.data()
