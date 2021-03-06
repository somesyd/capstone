import json
from datetime import datetime

from django.http import HttpResponse

from django.shortcuts import render, redirect

from zeitgeist.twitter_data import deserialized_twitter_data, get_most_common_words, pull_tweet_text, \
    find_most_common_parcels, save_search_to_db
from .oauth import get_oauth_request_token, get_access_token, build_oauth_url, get_twitter_data, TwitterOauthMiddleware
from .db_query import pull_queries_by_user, rebuild_query_by_id, delete_selected_queries, get_current_user_name
from django.http import JsonResponse

from django.utils.decorators import decorator_from_middleware


@decorator_from_middleware(TwitterOauthMiddleware)
def home(request):
    # get user name:
    twitter_name = get_current_user_name(request)
    return render(request, 'home.html', {'username': twitter_name})


def authorization(request):
    access_token = get_access_token(request)
    response = redirect('/home')
    response.set_cookie('token', json.dumps(access_token))
    return response


def coordinates(request):
    my_lat = request.GET.get('lat')
    my_lng = request.GET.get('lng')
    twitter_token = request.COOKIES['token']
    twitter_response = get_twitter_data(my_lat, my_lng, twitter_token)

    # record datetime of query and get username
    query_datetime = datetime.utcnow()
    user_name = request.user

    # deserialize the Twitter response json object into tweets
    tweet_list = deserialized_twitter_data(twitter_response.json())
    # get a list of most common phrases/keywords
    phrase_list = get_most_common_words(tweet_list)
    # get the most common occurrences of hashtags, user_mentions, and urls
    hashtag_list = find_most_common_parcels(tweet_list, 'hashtags')
    user_mention_list = find_most_common_parcels(tweet_list, 'user_mentions')
    urls_list = find_most_common_parcels(tweet_list, 'urls')
    # combine return lists into one list:
    twitter_list = phrase_list + hashtag_list + user_mention_list
    save_search_to_db(user_name, twitter_list, query_datetime, p_filter=False, a_filter=False, u_filter=False,
                      lat=my_lat, lng=my_lng)
    # combine return lists into a json block and send it back to site.js
    json_return = JsonResponse({'lat': my_lat, 'lng': my_lng,
                                'twitter': twitter_list})
    return json_return


def logout_user(request):
    response = HttpResponse()
    response.delete_cookie('token')
    return response



@decorator_from_middleware(TwitterOauthMiddleware)
def queries(request):
    user = request.user
    user_queries = pull_queries_by_user(user)
    twitter_user = get_current_user_name(request)
    context = {'user_queries': user_queries, 'username': twitter_user}
    return render(request, 'queries.html', context)


@decorator_from_middleware(TwitterOauthMiddleware)
def rerun(request):
    search_id = request.GET.get('id')
    query_dict = rebuild_query_by_id(search_id)
    json_return = JsonResponse(query_dict)
    return json_return


@decorator_from_middleware(TwitterOauthMiddleware)
def deletequery(request):
    id_array = request.POST.getlist('checks[]')
    delete_selected_queries(id_array)
    message = 'success'
    return JsonResponse({'message': message})

