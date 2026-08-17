#!/usr/bin/env python3
"""Smoke HTTP del flujo crítico (sin navegador) contra la instancia E2E."""
import os
import re
import sys

import requests

BASE = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:18800")
USER = os.environ.get("E2E_USER", "e2e")
PASSWORD = os.environ["E2E_PASSWORD"]
OTHER = os.environ.get("E2E_OTHER_USER", "e2e-otro")

ok, fail = 0, []


def check(label, cond, detail=""):
    global ok
    if cond:
        ok += 1
        print(f"  OK   {label}")
    else:
        fail.append(f"{label} — {detail}")
        print(f"  FALLA {label} — {detail}")


def login(username, password):
    s = requests.Session()
    page = s.get(f"{BASE}/account/login/", timeout=30)
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text)
    s.post(
        f"{BASE}/account/login/",
        data={
            "login": username, "password": password,
            "csrfmiddlewaretoken": token.group(1) if token else "",
        },
        headers={"Referer": f"{BASE}/account/login/"},
        timeout=30, allow_redirects=True,
    )
    return s


def api(session, method, path, json=None):
    csrf = session.cookies.get("csrftoken", "")
    response = session.request(
        method, f"{BASE}{path}", json=json, timeout=60,
        headers={"X-CSRFToken": csrf, "Referer": BASE, "Accept": "application/json"},
        allow_redirects=False,
    )
    try:
        payload = response.json()
    except Exception:
        payload = None
    return response.status_code, payload


print("== 1. Sesión ==")
owner = login(USER, PASSWORD)
status, _ = api(owner, "GET", "/business/list/")
check("el dueño queda autenticado", status == 200, str(status))

print("\n== 2. Superficie del producto ==")
for path in ("/modeling/businesses/", "/modeling/templates/", "/modeling/models/",
             "/modeling/runs/", "/simulate/list/", "/report/list/"):
    status, _ = api(owner, "GET", path)
    check(f"GET {path} responde sin error de servidor", status < 500, str(status))

status, businesses = api(owner, "GET", "/modeling/businesses/")
items = businesses if isinstance(businesses, list) else (businesses or {}).get("businesses", [])
business_id = items[0]["id"] if items else None
check("hay un negocio del dueño", business_id is not None, str(businesses)[:200])

status, templates = api(owner, "GET", "/modeling/templates/")
titems = templates if isinstance(templates, list) else (templates or {}).get("templates", [])
check("hay plantillas sintéticas disponibles", bool(titems), str(templates)[:200])

print("\n== 3. Modelo → validar → simular ==")
model_id = None
if business_id and titems:
    template = titems[0]
    status, created = api(owner, "POST", "/modeling/models/", {
        "business_id": business_id, "name": "Modelo HTTP",
        "sector": template.get("sector"), "spec": template.get("spec"),
    })
    check("se crea el modelo desde la plantilla", status in (200, 201),
          f"{status} {str(created)[:300]}")
    model_id = ((created or {}).get("model") or {}).get("id")

if model_id:
    status, _ = api(owner, "POST", f"/modeling/models/{model_id}/validate/", {})
    check("la validación responde", status in (200, 400), str(status))

    status, run = api(owner, "POST", f"/modeling/models/{model_id}/simulate/",
                      {"iterations": 200, "seed": 20260817})
    check("la simulación responde con un estado explícito",
          status in (200, 201, 202, 400, 409, 422), f"{status} {str(run)[:300]}")

    print("\n== 4. Negativos ==")
    status, _ = api(owner, "POST", f"/modeling/models/{model_id}/simulate/",
                    {"iterations": "muchas", "seed": "x"})
    check("iteraciones inválidas -> 400, no 500", status in (400, 422), str(status))

    csrf = owner.cookies.get("csrftoken", "")
    raw = owner.post(f"{BASE}/modeling/models/{model_id}/simulate/",
                     data="{no es json", timeout=30,
                     headers={"Content-Type": "application/json", "X-CSRFToken": csrf,
                              "Referer": BASE}, allow_redirects=False)
    check("JSON malformado -> 400, no 500", raw.status_code == 400, str(raw.status_code))

    status, _ = api(owner, "POST", f"/modeling/models/{model_id}/scenarios/",
                    {"label": "NaN", "changes": {"demand": "NaN"}})
    check("valor no finito rechazado", status in (400, 422), str(status))

    print("\n== 5. Autorización ==")
    other = login(OTHER, PASSWORD)
    status, _ = api(other, "GET", f"/modeling/models/{model_id}/")
    check("otro dueño no lee el modelo ajeno", status in (403, 404), str(status))
    status, _ = api(other, "POST", f"/modeling/models/{model_id}/simulate/",
                    {"iterations": 10, "seed": 1})
    check("otro dueño no simula el modelo ajeno", status in (403, 404), str(status))

anon = requests.Session()
response = anon.get(f"{BASE}/modeling/businesses/", timeout=30, allow_redirects=False)
check("sin sesión no se entregan datos",
      response.status_code in (301, 302, 401, 403), str(response.status_code))

print("\n" + "=" * 55)
print(f"OK: {ok}   FALLAS: {len(fail)}")
for item in fail:
    print(f"  - {item}")
sys.exit(1 if fail else 0)
