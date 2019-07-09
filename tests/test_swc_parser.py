#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `swc_parser` package."""

import pytest

from swc_parser import _parse_swc
from pathlib import Path


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""

    x = _parse_swc(Path("tests", "G-001.swc"))
    assert x.nodes is None
