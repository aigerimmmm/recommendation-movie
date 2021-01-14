from django.shortcuts import render, get_object_or_404
from .models import Review, Movie

from .form import ReviewForm
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
import datetime
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import pandas as pd
import numpy as np
import scipy as sp
from sklearn.metrics import pairwise_distances
from scipy.spatial.distance import cosine, correlation
import operator
from sklearn.metrics.pairwise import cosine_similarity
import requests
import urllib.parse
from bs4 import BeautifulSoup
from requests import get
import lxml
import re
import imdb
import urllib.request
    

# Create your views here.
def review_list(request):
    latest_review_list = Review.objects.order_by('-pub_date')[:9]
    context = {'latest_review_list': latest_review_list}
    return render(request, 'review_list.html', context)


def review_detail(request, pk):
    review = get_object_or_404(Review, id=pk)
    return render(request, 'review_detail.html', {'review': review})
    

def movie_list(request):
    movie_list = Movie.objects.order_by('-title')[40:52]
    splitStrings = re.findall('\<Movie:(.*?)\>',str(movie_list))
    covers = []
    for i in range(len(splitStrings)):
        im = imdb.IMDb() 
        search = im.search_movie(splitStrings[i])
        # get the id 
        id = search[0].movieID 
        series = im.get_movie(id)
        # getting cover url of the series 
        cover = series.data['cover url'] 
        covers.append(cover)
    zip_image_and_movies = zip(movie_list, covers)
    zipped_image_and_movies = list(zip_image_and_movies)

    zipped_image_and_movies_half = zipped_image_and_movies[0:6]
    zipped_image_and_movies_sec_half = zipped_image_and_movies[6:12]
    context = {'zipped_image_and_movies_half': zipped_image_and_movies_half, 'zipped_image_and_movies_sec_half': zipped_image_and_movies_sec_half}
    return render(request, 'movie_list.html', context)

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    form = ReviewForm()
    return render(request, 'movie_detail.html', {'movie': movie})

def add_review(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        rating = form.cleaned_data['rating']
        comment = form.cleaned_data['comment']
        user_name = form.cleaned_data['user_name']
        review = Review()
        review.movie = movie
        review.user_name = user_name
        review.rating = rating
        review.comment = comment
        review.pub_date = datetime.datetime.now()
        review.save()
        return HttpResponseRedirect(reverse('movie_detail', args=(movie.id, )))
    return render(request, 'movie_detail.html', {'movie': movie, 'form': form})

def logout_view(request):
    logout(request)
    return redirect('/')

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def get_recommendation(request):
    num_reviews = Review.objects.count()
    all_user_names = list(map(lambda x: x.id, User.objects.only("id")))
    # all user id's
    all_movie_ids = set(map(lambda x: x.movie.id, Review.objects.only("movie")))
    # all movie titles
    all_movie_title = list(Movie.objects.only("title"))
    # all rating
    all_movie_ratings = set(map(lambda x: x.movie.id, Review.objects.only("rating")))
    
    num_users = len(list(all_user_names))
    movieRatings_m = sp.sparse.dok_matrix((num_users, max(all_movie_ids)+1), dtype=np.float32)
    for i in range(num_users):
        user_reviews = Review.objects.filter(user_id=all_user_names[i])
        for user_review in user_reviews:
            movieRatings_m[i, user_review.movie.id] = user_review.rating
    movieRatings = movieRatings_m.transpose()
    coo = movieRatings.tocoo(copy=False)
    df=pd.DataFrame({'movies': coo.row, 'users': coo.col, 'rating': coo.data})[['movies', 'users', 'rating']].sort_values(['movies', 'users']).reset_index(drop=True)
    #df = df.fillna(lambda x: x.median())
    mo = df.pivot_table(index=['movies'], columns=['users'],values='rating')
    mo = mo.transpose()
    mo.replace(np.nan, 0, inplace=True)
    user_similiarity = cosine_similarity(mo)
    user_sim_df=pd.DataFrame(user_similiarity, index= mo.index, columns=mo.index)
    mo = mo.T
    # find current user id
    user = request.user.id
    if user not in mo.columns:
    	return ('no data is avaible on this user')
    # most 10 similar users
    sim_user = user_sim_df.sort_values(by= user, ascending = False).index[1:11]

    # best contains the most highest rated movies of each sim_users, which is 5
    best =[]
    for i in sim_user:
    	max_score=mo.loc[:, i].max()
    	best.append(mo[mo.loc[:, i] == max_score].index.tolist())

    # all seen movies rated by given user
    user_seen_movies=mo[mo.loc[:, user]> 0].index.tolist()

    for i in range(len(best)):
    	for j in best[i]:
    		if (j in user_seen_movies):
    			# remove all the movies that current user has with his similar user movies
    			best[i].remove(j)

    # dictionary that holds movies from all similar users to given user
    most_common ={}
    for i in range(len(best)):
    	for j in best[i]:
    		if j in most_common:
    			most_common[j]+=1
    		else:
   		    	most_common[j] =1

    #print(most_common)
    #sorted_list=sorted(most_common.items(), key=operator.itemgetter(1), reverse=True)
    sorted_list=sorted(most_common.items(), key=operator.itemgetter(1), reverse=True)

    # list saves most recommended movies 
    highest_rated_recommended = []
    for index,tuple in enumerate(sorted_list[1:5]):
        element_one = tuple[0]
        highest_rated_recommended.append(element_one)
    
    
    
    # list of recommendated movies
    recommendation = []
    for x in highest_rated_recommended:
        recommendation.append(Movie.objects.filter(id=x))


   
    str1 = ''.join(str(e) for e in recommendation)
    splitString = re.findall('\<Movie:(.*?)\>',str1)
    splitString2 = '\n'.join(str(i) for i in splitString)
    splitString3 = splitString2.replace(")",")\n")
    movie_titles_list = []

    for s in range (0, 4, 1):
        # creating instance of IMDb 
        ia = imdb.IMDb() 
        # searching the name  
        #search = ia.search_movie(splitString[s]) 
        search = ia.search_movie(splitString[s]) 
        for i in range(len(search)): 
        # get the id 
            id = search[0].movieID 
            #print(search[0]['title'] + " : " + id ) 
        movie_titles_list.append('https://www.imdb.com/title/tt' + id +'/?ref_=fn_al_tt_1')
    
    splitStringformovie = '\n'.join(str(i) for i in movie_titles_list)
    splitStringformovie2 = splitStringformovie.replace(", ","\n")

    # zip the movie titles and the links for the movies
    a_zipp = zip(splitString, movie_titles_list)
    zipp_list = list(a_zipp)
    context = str(zipp_list).replace("'", "")
    context = context.replace(", ",":")
    context = context.replace("):(","\n\n")
    context = context.replace("):","):    ")
    context = context.replace("[(","")
    context = context.replace(")]","")
    context = context.replace(">","")

    return render(request, 'get_suggestions.html', {'context': context})
    