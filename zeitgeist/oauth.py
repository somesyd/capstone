from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils.decorators import make_middleware_decorator
from requests_oauthlib import OAuth1Session

from zeitgeist.db_query import pull_queries_by_user
from zeitgeist.models import UserProfile
from django.contrib.auth import login
from .settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from json import loads


TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_VERIFY_CRED_URL = 'https://api.twitter.com/1.1/account/verify_credentials.json'


def authenticate_user(request, response):
    # link to user if user_id exists
    user_id = response.json()['id']
    my_user = UserProfile.objects.filter(twitter_id=user_id)
    if len(my_user) != 0:
        auth_user = User.objects.get(userprofile__twitter_id=user_id)
        user_first_last = UserProfile.objects.get(user=auth_user).twitter_name
        login(request, auth_user)
        print(response.status_code)
        print(user_first_last)
    else:
        # if user is not in db, create a new user from twitter credentials
        user_name = response.json()['screen_name']
        user_first_last = response.json()['name']
        new_user = User.objects.create_user(username=user_name)
        new_user_profile = UserProfile(
            user=new_user,
            twitter_id=user_id,
            twitter_name=user_first_last
        ).save()
        login(request, new_user)
        print(response.status_code)
        print(user_first_last)
    return user_first_last


def verify_Twitter_credentials(request, twitter_token):
    # decode the user cookie token
    access_token_dict = loads(twitter_token)
    # send verification request to Twitter
    oauth = OAuth1Session(
        client_key=TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=access_token_dict['oauth_token'],
        resource_owner_secret=access_token_dict['oauth_token_secret'])
    response = oauth.get(TWITTER_VERIFY_CRED_URL)
    return response


class TwitterOauthMiddleware(object):

    def process_request(self, request):

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        try:
            twitter_token = request.COOKIES['token']

            # Verify the user's credentials through Twitter
            response = verify_Twitter_credentials(request, twitter_token)

            # If Twitter bounces back a 200 status code, authenticate the user
            # and return a success message
            if response.status_code == 200:
                auth_user_name = authenticate_user(request, response)
                return None
            # If 200 status code is not bounced back, return a failure message
            else:
                status_reason = response.reason
                message = 'Authentication failure reason:' + status_reason + '. ' \
                             + 'Please authorize through Twitter to log in.'
                return render(request, 'error.html', {'error': message})
        except KeyError:
            print('No token found: redirect to Twitter for authorization')
            return get_oauth_request_token(
                lambda key, secret: redirect(build_oauth_url(key, secret)),
                lambda message: render(request, 'error.html', {'error': message}))


def get_oauth_request_token(callback, error):
    oauth = OAuth1Session(
        client_key=TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET)
    fetch_response_json = oauth.fetch_request_token(TWITTER_REQUEST_TOKEN_URL)
    if fetch_response_json and fetch_response_json["oauth_callback_confirmed"]:
        resource_owner_key = fetch_response_json.get('oauth_token')
        resource_owner_secret = fetch_response_json.get('oauth_token_secret')
        return callback(resource_owner_key, resource_owner_secret)
    else:
        return error("Request token failed")


def build_oauth_url(resource_owner_key, resource_owner_secret):
    oauth = OAuth1Session(
        client_key=TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret)
    return oauth.authorization_url(TWITTER_AUTHORIZATION_URL)


def get_access_token(request):
    oauth_token = request.GET['oauth_token']
    oauth_verifier = request.GET['oauth_verifier']
    oauth = OAuth1Session(
        client_key=TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=oauth_token)
    access_token = oauth.fetch_access_token(url=TWITTER_ACCESS_TOKEN_URL, verifier=oauth_verifier)
    return access_token


def build_query_string(lat, lng):
    q = ('q=&geocode=' + lat + ',' + lng + ',' +
              '5mi&result_type=recent&lang=en&count=100')
    q = 'https://api.twitter.com/1.1/search/tweets.json?' + q
    return q


def get_twitter_data(latitude, longitude, access_token):
    access_token_dict = loads(access_token)
    oauth = OAuth1Session(
        client_key=TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=access_token_dict['oauth_token'],
        resource_owner_secret=access_token_dict['oauth_token_secret'])
    query_string = build_query_string(latitude, longitude)
    return oauth.get(query_string)

