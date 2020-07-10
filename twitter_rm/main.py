import json
from requests_oauthlib import OAuth1Session
from urllib.parse import parse_qs
import twitter
import socket

import rm

tw_request_endpoint = "https://api.twitter.com/oauth/request_token"
tw_access_endpoint = "https://api.twitter.com/oauth/access_token"
tw_auth_endpoint = "https://api.twitter.com/oauth/authenticate?oauth_token={}"

def socket_callback(serv):
    sock, addr = serv.accept()
    data = sock.recv(1024)
    request = str(data)
    qs = request.split()[1][2:]
    verifier = parse_qs(qs)["oauth_verifier"][0]
    sock.send(b"you can close this tab")
    return verifier

def get_resource_tokens(secrets):
    token_request = OAuth1Session(client_key=secrets["api_key"], client_secret=secrets["api_secret_key"])
    data = token_request.get(tw_request_endpoint)
    return {k: v[0] for k, v in parse_qs(data.text).items()}

def get_access_tokens(secrets, resources, verifier):
    token_request = OAuth1Session(
            client_key=secrets["api_key"],
            client_secret=secrets["api_secret_key"],
            resource_owner_key=resources["oauth_token"],
            resource_owner_secret=resources["oauth_token_secret"])
    access_token_data = token_request.post(tw_access_endpoint, data={"oauth_verifier": verifier})
    return {k:v[0] for k,v in parse_qs(access_token_data.text).items()}

def resume():
    try:
        with open("./tokens.json", 'r') as tokens_file:
            tokens = json.load(tokens_file)
        return tokens 
    except:
        return None

def flush(access_tokens):
    with open("./tokens.json", 'w') as tokens_file:
        json.dump(access_tokens, tokens_file)

def main():
    with open("./secrets.json", 'r') as secrets_file:
        secrets = json.load(secrets_file)
    resource_tokens = get_resource_tokens(secrets)
    access_tokens = resume()
    if access_tokens is None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("localhost", 5000))
        s.listen()
        print(f"Please go to " + tw_auth_endpoint.format(resource_tokens["oauth_token"]))
        verifier = socket_callback(s)
        s.close()
        access_tokens = get_access_tokens(secrets, resource_tokens, verifier)
        flush(access_tokens)

    t = twitter.Api(
            consumer_key=secrets["api_key"],
            consumer_secret=secrets["api_secret_key"],
            access_token_key=access_tokens["oauth_token"],
            access_token_secret=access_tokens["oauth_token_secret"])
    rm.work(t, access_tokens["user_id"], secrets["bearer"])

if __name__ == "__main__":
    main()

