# backend/app/tools/__init__.py
from .time_tools import get_current_time
from .math_tools import simple_calculator

# 导出一个包含所有基础工具的列表，方便外部统一导入和绑定
basic_tools = [
    get_current_time,
    simple_calculator
]

__all__ = ["basic_tools", "get_current_time", "simple_calculator"]