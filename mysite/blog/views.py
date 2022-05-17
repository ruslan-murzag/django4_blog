from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, CreateView
from .forms import *
from django.core.mail import send_mail
from taggit.models import Tag
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.auth.decorators import login_required


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blog/post/list.html',
                  {'page': page,
                   'posts': posts,
                   'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    return render(request,
                  'blog/post/detail.html',
                  {"post": post,
                   "comments": comments,
                   "new_comment": new_comment,
                   "comment_form": comment_form})


def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'rus.mur2001@gmail.com',
                      [cd['to']])

            sent = True
    else:
        form = EmailPostForm()
    print(post_id)
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    # print(request.GET)
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request, 'blog/post/search.html', {'form': form,
                                                     'query': query,
                                                     'results': results})


# class AddPostView(CreateView):
#     model = Post
#     template_name = 'blog/post/add_post.html'
#     fields = ['title', 'slug', 'author', 'body', 'status', 'tags']


@login_required
def add_post(request):
    new_post_form = False
    if request.method == 'POST':
        create_post_form = PostCreateForm(data=request.POST)
        # print(create_post_form)
        if create_post_form.is_valid():
            create_post_form = create_post_form.save(commit=False)
            create_post_form.author = request.user
            create_post_form.save()
            new_post_form = True
    else:
        create_post_form = PostCreateForm()

    return render(request, 'blog/post/add_post.html', {
        'post_form': create_post_form,
        'new': new_post_form
    })


@login_required
def post_edit(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    permission = (request.user == post.author)
    new_post = False
    if request.method == 'POST':
        post_form = PostEditForm(data=request.POST, instance=post)

        if post_form.is_valid():
            post_form = post_form.save(commit=False)
            post_form.author = request.user
            post_form.save()
            new_post = True
    else:
        post_form = PostEditForm(instance=post)
    return render(request,
                  'blog/post/post_edit.html',
                  {'post_form': post_form,
                   'permission': permission,
                   'new_post': new_post})
