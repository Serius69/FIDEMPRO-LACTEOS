from django.conf import settings
from django.test import RequestFactory
from django.http import HttpResponse

from findempro.security_headers import SecurityHeadersMiddleware


def test_spa_csp_has_no_eval_or_external_cdns():
    middleware = SecurityHeadersMiddleware(lambda request: HttpResponse("ok"))
    response = middleware(RequestFactory().get("/"))
    csp = response["Content-Security-Policy"]

    assert "'unsafe-eval'" not in csp
    assert "cdn." not in csp
    assert "jquery" not in csp
    assert "d3js.org" not in csp
    assert csp == settings.CONTENT_SECURITY_POLICY
