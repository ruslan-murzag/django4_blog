from django.urls import path, include
from . import views
from .feeds import LatestPostFeed
from rest_framework import routers


router = routers.DefaultRouter()

router.register(r'posts', views.PostViewSet)
app_name = 'blog'

urlpatterns = [
    # path('', views.post_list, name='post_list'),
    path('', views.post_list, name='post_list'),
    path('tag.<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/share/',
         views.post_share, name='post_share'),
    path('feed/', LatestPostFeed(), name='post_feed'),
    path('search/', views.post_search, name='post_search'),
    path('add_post/', views.add_post, name='add_post'),
    path('edit/<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_edit, name='post_edit'),
    path('api/', include(router.urls))
]
