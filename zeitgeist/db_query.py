from json import loads

from .models import User, SearchQuery, SearchResultSet, SearchResultItem, Filter, ParcelType, UserProfile


def pull_queries_by_user(user):
    user_queries = SearchQuery.objects.filter(searchresultset__user=user)
    return user_queries

def rebuild_query_by_id(search_id):
    query_list = []
    lat = SearchQuery.objects.get(id=search_id).latitude
    lng = SearchQuery.objects.get(id=search_id).longitude
    result_items_set = SearchResultItem.objects.filter(search_result__search_query_id=search_id)
    for item in result_items_set:
        parcel = ParcelType.objects.get(search_result_item=item).parcel_type
        dict_item = {'parcel': parcel, 'text': item.item_text, 'count': item.item_count}
        query_list.append(dict_item)
    query_dict = {'lat': lat, 'lng': lng, 'twitter': query_list}
    return query_dict

def delete_selected_queries(id_array):
    sq = SearchQuery.objects.filter(pk__in=id_array)
    sq.delete()

def get_current_user_name(request):
    if 'token' in request.COOKIES:
        token = loads(request.COOKIES['token'])
        twitter_id = token['user_id']
        this_user_name = UserProfile.objects.get(twitter_id=twitter_id).twitter_name
        return this_user_name
    else:
        print('no token')
