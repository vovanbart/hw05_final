from yatube.settings import PST_ON_PAGE
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, PST_ON_PAGE)
    page_num = request.GET.get('page')
    page_obj = paginator.get_page(page_num)
    title = f'Записи сообщества <{group}>'
    context = {
        'group': group,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, PST_ON_PAGE)
    page_num = request.GET.get('page')
    page_obj = paginator.get_page(page_num)
    following = Follow.objects.filter(author=author,
                                      user=request.user).exists()
    context = {
        'post_count': post_count,
        'paginator': paginator,
        'author': author,
        'page_obj': page_obj,
        'following': following, }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_count = Post.objects.count()
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post_count': post_count,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id, is_edit=True):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'is_edit': is_edit, 'post': post}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).values('author')
    post_list = Post.objects.filter(author_id__in=following).all()
    paginator = Paginator(post_list, PST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    status_follow = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    if status_follow or author == request.user:
        return redirect('posts:profile', username=request.user)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=request.user)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect('posts:profile_unfollow', username=request.user)
