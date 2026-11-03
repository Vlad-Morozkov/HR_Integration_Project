import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "timezone_detector",
    path=os.path.join(
        os.path.dirname(__file__),
        "frontend"
    )
)

def detect_timezone():
    return _component_func(
        default=None,
        key="timezone_detector"
    )