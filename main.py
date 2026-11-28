from fastapi import FastAPI, HTTPException, Request, status, Depends
# from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from schemas import PostCreate, PostUpdate, PostResponse, UserCreate, UserResponse
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory = "templates")

# @app.get("/")
# def home():
#     return { "message" : "Hello World"}

# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def getHTMLPosts():
#     return f"<h1>{posts[0]["title"]}</h1>"

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def getHTMLPosts(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )

@app.get("/post/{post_id}", include_in_schema=False)
def getHTMLPost(request: Request, post_id:int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


# API URLs

@app.post("/api/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.userName == user.userName)
    )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username Already exists",
        )

    result = db.execute(
            select(models.User).where(models.User.email == user.email)
        )
    
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email Already exists",
        )

    new_user = models.User(
        userName = user.userName,
        email = user.email,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/api/user/{user_id}", response_model=UserResponse)
def get_user(user_id:int,  db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
            select(models.User).where(models.User.id == user_id)
        )

    user = result.scalars().first()

    if(user):
        return user
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found.")

@app.get("/api/user/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id:int,  db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
            select(models.User).where(models.User.id == user_id)
        )

    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found.")

    result = db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts = result.scalars().all()
    return posts
        
    

@app.post("/api/post", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post:PostCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()

    if(not user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found."
        )

    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

@app.get("/api/post/{post_id}", response_model=PostResponse)
def get_post(post_id:int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id==post_id))
    post = result.scalars().first()

    if post:
        return post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found.")

@app.put("/api/post/{post_id}", response_model=PostResponse)
def update_post_full(post_id:int, post_data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id==post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found.")

    if post_data.user_id != post.user_id:

        result = db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found.")

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)

    return post