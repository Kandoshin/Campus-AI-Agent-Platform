from datetime import datetime
from langchain_core.tools import tool

@tool
def get_current_time() -> str:
    """
    获取当前系统的日期和时间。
    当用户询问“现在几点”、“今天几号”、“当前时间”等与此刻时间相关的问题时，调用此工具。
    """
    # 格式化输出当前时间，例如：2026-6-28 15:30:00
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")