import arrow
import requests
import json
import time

now = arrow.now()
cliff = now.shift(days=-180)
tw_date_fmt = "YYYYMMDDhhmm"

def work(api, user_id, bearer):
    tweets = search_archive_statuses(bearer, user_id)
    # tweets = fetch_statuses(api, user_id)
    # rm(api, tweets)

def search_archive_statuses(bearer, user_id):
    tweets = set()
    all_data = []
    endpoint = "https://api.twitter.com/1.1/tweets/search/fullarchive/testing.json"
    headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}
    data = f'{{"query":"from:{user_id}", "toDate": "{cliff.format(tw_date_fmt)}"}}'

    response = requests.post(endpoint, data=data, headers=headers).json()
    all_data += response["results"]
    for tweet in response["results"]:
        tweets.add(tweet["id"])
    print(f"Fetched {len(tweets)} tweets...")
    while "next" in response:
        next_token = response.get("next")
        data = f'{{"query":"from:{user_id}", "toDate": "{cliff.format(tw_date_fmt)}", "next": "{next_token}"}}'
        time.sleep(2)
        response = requests.post(endpoint, data=data, headers=headers).json()
        all_data += response["results"]
        for tweet in response["results"]:
            tweets.add(tweet["id"])
        print(f"Fetched {len(tweets)} tweets...")

    tweets_list = list(tweets)
    with open("/tmp/data.json", "w") as f:
        json.dump({"ids": tweets_list, "tweets": all_data}, f, indent=2)
    return tweets


def fetch_statuses(api, user_id):
    tweets_to_delete = set()
    max_id = None
    while True:
        latest_tweets = api.GetUserTimeline(user_id=user_id, count=200, trim_user=True, max_id=max_id)
        if latest_tweets[-1].id == max_id:
            break
        max_id = latest_tweets[-1].id
        print(arrow.get(latest_tweets[-1].created_at_in_seconds))
        tweets_to_delete.update(set(t for t in latest_tweets if t.created_at_in_seconds < cliff.timestamp))
    print("fetched all available tweets....")
    return tweets_to_delete

def rm(api, tweets):
    # TODO: shard set of tweets to delete across workers 
    for tweet in tweets:
        api.DestroyStatus(tweet.status_id, trim_user=True)
