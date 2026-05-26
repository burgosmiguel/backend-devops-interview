from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import LimitOffsetPagination, paginate

from blog.models import Comment, Post, Tag, User
from blog.schemas import (
    CommentCreateIn,
    CommentCreateOut,
    PostCreateIn,
    PostCreateOut,
    PostDetailOut,
    PostListOut,
    UserDetailOut,
)

router = Router()

_POST_LIST_QS = lambda qs: qs.select_related("author").prefetch_related("tags")


def _serialize_author(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
    }


def _serialize_tag(tag: Tag) -> dict:
    return {"id": tag.id, "name": tag.name, "slug": tag.slug}


@router.get("/posts", response=list[PostListOut])
@paginate(LimitOffsetPagination)
def list_posts(request, **kwargs):
    return _POST_LIST_QS(
        Post.objects.filter(is_published=True).order_by("-created_at")
    )


@router.get("/posts/search", response=list[PostListOut])
@paginate(LimitOffsetPagination)
def search_posts(request, q: str, **kwargs):
    if not q or not q.strip():
        return Post.objects.none()
    return _POST_LIST_QS(
        Post.objects.filter(
            Q(title__icontains=q) | Q(body__icontains=q),
            is_published=True,
        ).order_by("-created_at")
    )


@router.get("/posts/by-tag/{slug}", response=list[PostListOut])
@paginate(LimitOffsetPagination)
def posts_by_tag(request, slug: str, **kwargs):
    tag = get_object_or_404(Tag, slug=slug)
    return _POST_LIST_QS(
        tag.posts.filter(is_published=True).order_by("-created_at")
    )


@router.get("/posts/{post_id}", response=PostDetailOut)
def get_post(request, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    post.view_count += 1
    post.save()

    comments = [
        {
            "id": c.id,
            "author": _serialize_author(c.author),
            "body": c.body,
            "created_at": c.created_at,
        }
        for c in post.comments.order_by("created_at")
    ]
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "author": _serialize_author(post.author),
        "tags": [_serialize_tag(t) for t in post.tags.all()],
        "comments": comments,
        "view_count": post.view_count,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


@router.post("/posts", response={201: PostCreateOut})
def create_post(request, payload: PostCreateIn):
    author = get_object_or_404(User, id=payload.author_id)
    post = Post.objects.create(
        author=author,
        title=payload.title,
        body=payload.body,
    )
    for slug in payload.tag_slugs:
        tag = get_object_or_404(Tag, slug=slug)
        post.tags.add(tag)
    return {"id": post.id, "title": post.title}


@router.post("/posts/{post_id}/comments", response=CommentCreateOut)
def create_comment(request, post_id: int, payload: CommentCreateIn):
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=payload.author_id)
    comment = Comment.objects.create(post=post, author=author, body=payload.body)
    return {"id": comment.id}


@router.get("/users/find", response=UserDetailOut)
def find_user_by_email(request, email: str):
    user = get_object_or_404(User, email=email)
    return _user_detail(user)


@router.get("/users/{user_id}", response=UserDetailOut)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return _user_detail(user)


def _user_detail(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "bio": user.bio,
        "post_count": user.posts.count(),
        "comment_count": user.comments.count(),
    }
