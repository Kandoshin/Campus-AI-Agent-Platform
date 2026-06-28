from langchain_core.tools import tool


@tool
def simple_calculator(expression: str) -> str:
    """
    执行基础的数学计算。
    参数 expression 必须是一个有效的数学表达式字符串，例如 "12 + 34"、"1234 * 5678" 或 "100 / 3"。
    当用户让你进行算术运算时，调用此工具。
    """
    # 基础安全校验：仅允许数字和基础数学符号，防止恶意代码注入
    allowed_chars = set("0123456789+-*/(). ")
    if not set(expression).issubset(allowed_chars):
        return "计算失败：表达式包含非法字符。仅支持数字及 + - * / ( )"

    try:
        # 使用 eval 执行计算，通过禁用 __builtins__ 来限制运行环境，保证基本的安全性
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except ZeroDivisionError:
        return "计算出错: 除数不能为零"
    except Exception as e:
        return f"计算出错: 无法解析的表达式 ({str(e)})"