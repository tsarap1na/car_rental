import pytest
from django.core.management import call_command

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

@pytest.fixture(autouse=True)
def clean_database():
    call_command('flush', '--no-input')
    yield 