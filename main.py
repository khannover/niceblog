from nicegui import app, ui, run, events
from datetime import datetime
from slugify import slugify
import pytz

from typing import Optional

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import base64
from user_agents import parse

tz = pytz.timezone(os.environ.get("NICEBLOG_TIMEZONE", "UTC"))
markdown_extras = ['fenced-code-blocks', 'tables', 'mermaid']

# in reality users passwords would obviously need to be hashed
passwords = {os.environ["NICEBLOG_USER"]: os.environ["NICEBLOG_PASSWORD"]}

unrestricted_page_routes = {'/login', '/show'}

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui'):
                if request.url.path == "/":
                    return await call_next(request)
                for r in unrestricted_page_routes:
                    if request.url.path.startswith(r):
                        return await call_next(request)
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)

@ui.page("/.aws/credentials")
@ui.page("/.env")
@ui.page("/.env.production")
@ui.page("/.git/HEAD")
@ui.page("/.kube/config")
@ui.page("/.ssh/id_ecdsa")
@ui.page("/.ssh/id_ed25519")
@ui.page("/.ssh/id_rsa")
@ui.page("/.svn/wc.db")
@ui.page("/.vscode/sftp.json")
@ui.page("/Public/home/js/check.js")
@ui.page("/_vti_pvt/administrators.pwd")
@ui.page("/_vti_pvt/authors.pwd")
@ui.page("/_vti_pvt/service.pwd")
@ui.page("/api/.env")
@ui.page("/backup.sql")
@ui.page("/backup.tar.gz")
@ui.page("/backup.zip")
@ui.page("/cloud-config.yml")
@ui.page("/config.json")
@ui.page("/config.php")
@ui.page("/config.xml")
@ui.page("/config.yaml")
@ui.page("/config.yml")
@ui.page("/config/database.php")
@ui.page("/config/production.json")
@ui.page("/database.sql")
@ui.page("/docker-compose.yml")
@ui.page("/dump.sql")
@ui.page("/etc/shadow")
@ui.page("/etc/ssl/private/server.key")
@ui.page("/feed")
@ui.page("/phpinfo.php")
@ui.page("/secrets.json")
@ui.page("/server-status")
@ui.page("/server.key")
@ui.page("/static/admin/javascript/hetong.js")
@ui.page("/user_secrets.yml")
@ui.page("/web.config")
@ui.page("/wordpress/wp-admin/setup-config.php")
@ui.page("/wp-admin/setup-config.php")
@ui.page("/wp-config.php")
def deal_with_naughty_bots(request:Request, response:Response):
    if not app.storage.general.get("blocked_ips"):
        app.storage.general["blocked_ips"] = []
    
    client_ip = get_client_ip(request)
    if not is_ip_blocked(client_ip):
        app.storage.general["blocked_ips"].append(client_ip)

    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "| malicious request from ip", client_ip, "|", request.url)
    return RedirectResponse("https://httpbin.org/delay/10")

def get_client_ip(request:Request):
        # Prüfen, ob der X-Forwarded-For-Header gesetzt ist
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Falls mehrere IPs in der Liste stehen, die erste ist die Client-IP
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        # Andernfalls auf die direkte Client-IP zugreifen
        client_ip = request.client.host
    return client_ip

def is_ip_blocked(ip:str):
    if ip in app.storage.general.get("blocked_ips", []):
        return True
    else:
        return False

def count_visitors():
    count = 0
    for f in os.listdir(".nicegui"):
        if f.startswith("storage-user"):
            count = count +1
    return count

@ui.page('/login')
async def login(request:Request) -> Optional[RedirectResponse]:
    ui.page_title("NiceBLOG Login")
    await detect_device(request.headers["user-agent"])

    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({'username': username.value, 'authenticated': True})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
    return None


@ui.page("/edit")
def edit_new():
    ui.navigate.to("/edit/new")

@ui.page("/edit/{id}")
async def edit(request:Request, id: str):
    ui.page_title("NiceBLOG Edit " + id)
    await detect_device(request.headers["user-agent"])
    await header()

    placeholder_image = "https://placehold.co/600x400"

    def delete(id:str):
        del app.storage.general["pages"][id]
        ui.navigate.to("/")
    
    
    def save(id:str):
        ui.notify(id)
        if not "pages" in app.storage.general:
            app.storage.general["pages"] = {}
        old_id = id
        id = slugify(edit_headline.value)
        
        if old_id != id and old_id != "new":
            del app.storage.general["pages"][old_id]

        app.storage.general["pages"][id] = {
            "id": id,
            "headline": edit_headline.value,
            "text": edit_textarea.value,
            "datetime": datetime.now(tz).strftime("%d.%m.%Y / %H:%M:%S"),
            "image": post_image.source if post_image.source != "https://placehold.co/600x400" else ""
        }
        ui.navigate.to(f"/show/{slugify(edit_headline.value)}")    
    
    
    def handle_upload(e: events.UploadEventArguments):
        text = base64.b64encode(e.content.read())
        post_image.set_source("data:image/jpg;base64," + text.decode("utf-8"))


    pages = app.storage.general.get("pages", {})
    page = pages[id] if id in pages else None

    if not app.storage.user["is_mobile"]:
        with ui.grid(columns=2).classes("w-full h-full"):
            with ui.column():
                ui.label("Überschrift").classes("text-xs")
                edit_headline = ui.input().classes("w-full p-3 border text-4xl").props("clearable")
                ui.separator()
                with ui.row():
                    ui.label("Text").classes("text-xs")
                    ui.label("(MarkDown)").classes("text-xs")
                edit_textarea = ui.textarea().classes("border pe-4 w-full").props("filled autogrow clearable")
            
            with ui.column().classes("w-full justify-center"):
                ui.label("Vorschau").classes("text-xs")
                
                ui.label().classes("text-6xl").bind_text_from(edit_headline, "value").classes("justify-center w-full")
                post_image = ui.image(placeholder_image).classes("justify-center w-[50%] ms-[auto] me-[auto]")
                ui.markdown(extras=markdown_extras).bind_content_from(edit_textarea, "value").classes("justify-center w-full")
                if page:
                    edit_headline.value = page["headline"]
                    edit_textarea.value = page["text"]
                    post_image.source = page.get("image") if page.get("image") is not None and page.get("image") != "" else placeholder_image
            with ui.row().classes("w-full"):
                ui.button("SAVE", icon="o_save", on_click=lambda: save(id)).classes("p-3")
                ui.space()
                ui.upload(on_upload=handle_upload)
                ui.button("DELETE", icon="o_delete", on_click=lambda: delete(id)).classes("p-3")
    else: # mobile
        ui.label("Überschrift").classes("text-xs")
        edit_headline = ui.input().classes("w-full p-3 border text-4xl").props("clearable")
        ui.separator()
        with ui.row():
            ui.label("Text").classes("text-xs")
            ui.label("(MarkDown)").classes("text-xs")
        edit_textarea = ui.textarea().classes("border pe-4 w-full").props("filled autogrow clearable")
        with ui.row().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Bild:").classes("text-xl mt-[auto] mb-[auto]")
                ui.upload(on_upload=handle_upload).classes("h-12")
            ui.button("SAVE", icon="o_save", on_click=lambda: save(id)).classes("w-full")
            ui.button("DELETE", icon="o_delete", on_click=lambda: delete(id)).classes("w-full")
            
        ui.separator().classes("bg-info")    
        ui.label("Vorschau").classes("text-xs")

        ui.label().classes("text-6xl justify-center w-full").bind_text_from(edit_headline, "value")
        post_image = ui.image(placeholder_image).classes("w-[50%] justify-center w-full")
        ui.markdown(extras=markdown_extras).bind_content_from(edit_textarea, "value").classes("justify-center w-full")
        if page:
            edit_headline.value = page["headline"]
            edit_textarea.value = page["text"]
            post_image.source = page.get("image") if page.get("image") is not None and page.get("image") != "" else placeholder_image


@ui.page("/show/{id}")
async def show(request:Request, id:str):
    ui.page_title("NiceBLOG Post " + id)
    await detect_device(request.headers["user-agent"])
    await header()
    pages = app.storage.general.get("pages", {})
    page = pages[id] if id in pages else None

    if page:
        if not app.storage.user["is_mobile"]:
            if app.storage.user.get('authenticated', False):
                ui.button("EDIT", icon="edit", on_click=lambda e: ui.navigate.to(f"/edit/{id}"))

            with ui.grid(columns="1fr 2fr 1fr").classes("w-full"):
                ui.label()
                with ui.column():
                    with ui.row().classes("w-full items-center"):
                        ui.label(page["datetime"]).classes("text-xs text-center w-full")
                    with ui.row().classes("w-full items-center"):
                        ui.label(page["headline"]).classes("text-6xl text-center w-full")
                    if page["image"] != "":
                        with ui.row().classes("w-full items-center justify-center"):
                            ui.image(page.get("image", None)).classes("w-[50%]")
                    with ui.row().classes("w-full justify-center"):
                        ui.markdown(page["text"], extras=markdown_extras).classes("justify-center")
                ui.label()
        else: # mobile
            if app.storage.user.get('authenticated', False):
                ui.button("EDIT", icon="edit", on_click=lambda e: ui.navigate.to(f"/edit/{id}"))
            with ui.row().classes("w-full items-center"):
                ui.label(page["datetime"]).classes("text-xs text-center w-full")
            with ui.row().classes("w-full items-center"):
                ui.label(page["headline"]).classes("text-6xl text-center w-full")
            if page["image"] != "":
                with ui.row().classes("w-full items-center justify-center"):
                    ui.image(page.get("image", None))
            with ui.row().classes("w-full justify-center"):
                ui.markdown(page["text"], extras=markdown_extras).classes("")
    else:
        ui.label("404").classes("w-[30%] text-5xl absolute-center")

async def header():
    def logout() -> None:
        app.storage.user.clear()
        ui.navigate.to('/')
    
    ui.colors(primary="#6836a1")
    if not app.storage.user["is_mobile"]:
        with ui.header().classes("justify-center").classes("bg-primary"):
            #ui.icon("home").classes("text-3xl mt-[auto] mb-[auto]")
            with ui.row().classes("mt-[auto] mb-[auto]").tooltip("Visitors"):
                ui.icon("person").classes("text-2xl")
                ui.label(count_visitors()).classes("text-xl")
            with ui.link(target="/").classes("text-white").style("text-decoration: none;"):
                ui.label(os.environ.get("NICEBLOG_HEADER_NAME", "NiceBLOG")).classes("text-6xl")
            ui.label(os.environ.get("NICEBLOG_HEADER_TITLE", "A minimal blog engine, written in NiceGU")).classes("text-xl mt-[auto] mb-[auto]") 
            if app.storage.user.get('authenticated', False):
                ui.button(on_click=lambda: ui.navigate.to("/edit/new"), icon="add").props("flat round").classes("mt-[auto] mb-[auto] text-white").tooltip("Add post")
                ui.button(on_click=logout, icon='logout').props('flat round').classes("text-white mt-[auto] mb-[auto]").tooltip("Logout")
            else:
                ui.button(on_click=lambda: ui.navigate.to("/login"), icon="login").props("flat round").classes("text-white mb-[auto] mt-[auto]").tooltip("Login")
    else: # mobile
        with ui.header().classes("").classes("bg-primary"):            
            with ui.column():
                with ui.link(target="/").classes("text-white").style("text-decoration: none;"):
                    ui.label(os.environ.get("NICEBLOG_HEADER_NAME", "NiceBLOG")).classes("text-3xl")
                ui.label(os.environ.get("NICEBLOG_HEADER_TITLE", "A minimal blog engine, written in NiceGU")).classes("text-md mt-[auto] mb-[auto]") 
            if app.storage.user.get('authenticated', False):
                ui.space()
                with ui.column():
                    ui.button(on_click=lambda: ui.navigate.to("/edit/new"), icon="add").props("flat")
                    ui.button(on_click=logout, icon='logout').props('flat')    
            else:
                with ui.column():
                    ui.button(on_click=lambda: ui.navigate.to("/login"), icon="login").props("")

@ui.page("/")
async def root(request:Request):
    ui.page_title("NiceBLOG Home")
    await detect_device(request.headers["user-agent"])

    await header()
    pages = app.storage.general.get("pages", {})
    pages = dict(sorted(pages.items(), reverse=True, key=lambda item: tz.localize(datetime.strptime(item[1]['datetime'], "%d.%m.%Y / %H:%M:%S"))))
    
    for page in list(pages.keys()):
        if not app.storage.user["is_mobile"]:
            with ui.row().classes("items-center justify-center ms-[auto] me-[auto]] w-full"):
                with ui.link(target="/show/" + pages[page]["id"]).style("text-decoration:none").classes("text-white"):
                    with ui.grid(columns="1fr 1fr 2fr 1fr").classes("items-center justify-center"):                
                        ui.label()
                        with ui.row():
                            ui.space()
                            ui.image(pages[page]["image"]).classes("w-96") if pages[page]["image"] != "" else ui.label()  
                        with ui.row():
                            with ui.column():
                                ui.badge(f'{pages[page]["datetime"]}')
                                ui.label(f'{pages[page]["headline"]}').classes("text-2xl")        
                                ui.markdown(pages[page]["text"].split("\n")[0], extras=markdown_extras)
                            ui.space()
                        ui.label()
            ui.separator()
        else: #mobile
            with ui.row().classes("items-center justify-center ms-[auto] me-[auto] w-full"):
                with ui.link(target="/show/" + pages[page]["id"]).style("text-decoration:none").classes("text-white"):
                    with ui.grid(columns="1fr 2fr").classes("items-center justify-center"):                
                        ui.image(pages[page]["image"]).classes("w-32") if pages[page]["image"] != "" else ui.label()  
                        with ui.column():
                            ui.badge(f'{pages[page]["datetime"]}')
                            ui.label(f'{pages[page]["headline"]}').classes("text-2xl")        
                            ui.markdown(pages[page]["text"].split("\n")[0], extras=markdown_extras)
            

async def detect_device(ua:str):
    user_agent = parse(ua)
    app.storage.user["is_mobile"] = user_agent.is_mobile



ui.run(
        port=1080,
        favicon="🍺",
        dark=True,
        show=False,
        reload=True,
        storage_secret=os.environ.get("NICEBLOG_STORAGE_SECRET"),
        language=os.environ.get("NICEBLOG_LANGUAGE", "en-US")
)
