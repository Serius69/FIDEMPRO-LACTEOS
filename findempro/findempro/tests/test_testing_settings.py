from django.conf import settings


def test_testing_hosts_are_explicit_and_do_not_use_wildcard():
    assert set(settings.ALLOWED_HOSTS) <= {'localhost', '127.0.0.1', 'testserver'}
    assert '*' not in settings.ALLOWED_HOSTS
