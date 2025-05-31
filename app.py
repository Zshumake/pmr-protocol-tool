from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

app = FastAPI()

# Directory setup
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "protocols.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Load protocols
def load_protocols():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_protocols(protocols):
    with open(DATA_PATH, "w") as f:
        json.dump(protocols, f, indent=2)

@app.get("/", response_class=HTMLResponse)
async def search(request: Request, q: str = "", category: str = "", priority: str = ""):
    protocols = load_protocols()
    filtered = []
    for pid, proto in protocols.items():
        if q.lower() in proto["issue"].lower():
            if (not category or proto["category"] == category) and (not priority or proto["priority"] == priority):
                filtered.append((pid, proto))
    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "category": category,
        "priority": priority,
        "results": filtered,
        "count": len(filtered)
    })

@app.get("/protocol/{protocol_id}", response_class=HTMLResponse)
async def protocol_detail(request: Request, protocol_id: str):
    protocols = load_protocols()
    protocol = protocols.get(protocol_id)
    if not protocol:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Protocol not found"})
    return templates.TemplateResponse("protocol_detail.html", {
        "request": request,
        "protocol_id": protocol_id,
        "protocol": protocol
    })

@app.get("/admin/list", response_class=HTMLResponse)
async def list_protocols(request: Request):
    protocols = load_protocols()
    return templates.TemplateResponse("admin_list.html", {
        "request": request,
        "protocols": list(protocols.items())
    })

@app.get("/admin/edit/{protocol_id}", response_class=HTMLResponse)
async def edit_protocol(request: Request, protocol_id: str):
    protocols = load_protocols()
    protocol = protocols.get(protocol_id)
    if not protocol:
        return RedirectResponse(url="/admin/list", status_code=302)
    return templates.TemplateResponse("admin_edit_form.html", {
        "request": request,
        "protocol_id": protocol_id,
        "protocol": protocol
    })

@app.post("/admin/edit/{protocol_id}")
async def update_protocol(
    request: Request,
    protocol_id: str,
    issue: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    steps: list[str] = Form(...)
):
    protocols = load_protocols()
    protocols[protocol_id] = {
        "issue": issue,
        "category": category,
        "priority": priority,
        "steps": steps
    }
    save_protocols(protocols)
    return RedirectResponse(url="/admin/list", status_code=303)

@app.get("/admin/new", response_class=HTMLResponse)
async def new_protocol_form(request: Request):
    return templates.TemplateResponse("admin_edit_form.html", {
        "request": request,
        "protocol_id": "",
        "protocol": {
            "issue": "",
            "category": "",
            "priority": "Medium",
            "steps": [""]
        }
    })

@app.post("/admin/new")
async def create_protocol(
    request: Request,
    protocol_id: str = Form(...),
    issue: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    steps: list[str] = Form(...)
):
    protocols = load_protocols()
    protocols[protocol_id] = {
        "issue": issue,
        "category": category,
        "priority": priority,
        "steps": steps
    }
    save_protocols(protocols)
    return RedirectResponse(url="/admin/list", status_code=303)

@app.post("/admin/delete/{protocol_id}")
async def delete_protocol(request: Request, protocol_id: str):
    protocols = load_protocols()
    if protocol_id in protocols:
        del protocols[protocol_id]
        save_protocols(protocols)
    return RedirectResponse(url="/admin/list", status_code=303)
