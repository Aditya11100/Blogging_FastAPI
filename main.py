from fastapi import FastAPI, HTTPException, Request, status
# from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from schemas import PostCreate, PostResponse

posts: list[dict] = [
    {
        "id": 1,
        "author": "Corey Schafer",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory = "templates")

# @app.get("/")
# def home():
#     return { "message" : "Hello World"}

# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def getHTMLPosts():
#     return f"<h1>{posts[0]["title"]}</h1>"

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def getHTMLPosts(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts" : posts, "title": "HomeBlogging"})

@app.get("/post/{post_id}", include_in_schema=False)
def getHTMLPost(request: Request, post_id:int):
    for post in posts:
        if post.get("id")==post_id:
            title = post.get("title")[:50]
            return templates.TemplateResponse(request, "post.html", {"post" : post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found.")



@app.post("/api/post", response_model=PostResponse,status_code=status.HTTP_201_CREATED)
def create_post(post:PostCreate):

    id = max(p["id"] for p in posts) + 1 if posts else 1

    new_post={
        "id":id,
        "author":post.author,
        "title":post.title,
        "content":post.content,
        "date_posted":"November 17, 2025"
    }

    posts.append(new_post)
    return new_post

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts

@app.get("/api/post/{post_id}", response_model=PostResponse)
def get_post(post_id:int):
    for post in posts:
        if post.get("id")==post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found.")