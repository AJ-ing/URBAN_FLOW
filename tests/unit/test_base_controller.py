import pytest
from controllers.base_controller import BaseController


def test_base_controller_is_abstract():
    with pytest.raises(TypeError):
        BaseController()