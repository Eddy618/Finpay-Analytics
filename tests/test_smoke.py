def test_python_environment():
    import sys

    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 10


def test_required_packages():
    import fastapi
    import pandas
    import requests
    import sqlalchemy
    import streamlit

    assert fastapi.__version__
    assert pandas.__version__
    assert requests.__version__
    assert sqlalchemy.__version__
    assert streamlit.__version__