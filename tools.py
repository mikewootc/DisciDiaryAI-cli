import os
import re, json
import datetime
from langchain.tools import tool
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from utils import logger

@tool
def get_current_date_time() -> str:
    """Get the current date and time.

    Returns:
        The current date and time in the format YYYY-MM-DD HH:MM:SS.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_diary_file(diary_file: str) -> list[str]:
    """Read the diary file and return its lines.

    Args:
        diary_file: The path to the diary file.

    Returns:
        The lines read from the diary file.
    """
    # logger.debug(f"read_diary_file_: {diary_file}")
    with open(diary_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) > 0:
        logger.debug(f"##### read_diary_file_: {len(lines)} lines.")
        # runtime.state["lst_diary_lines"] = lines
        return lines

    return []
    # return len(lines)
    #return Command(update={
    #    "lst_diary_lines": lines,
    #    # update the message history
    #    "messages": [
    #        ToolMessage(
    #            "Successfully read the diary file",
    #            tool_call_id=runtime.tool_call_id
    #        )
    #    ]
    #})


# Get day diary
@tool
def get_day_diary(runtime: ToolRuntime, date: str) -> str:
    """Read the diary for a specific date.

    Args:
        runtime: The runtime object.
        date: The date to read the diary for, in the format YYYY-MM-DD

    Returns:
        The diary string for the specified date, or an empty string if no entry is found.
    """

    lst_diary_lines = runtime.state.get('lst_diary_lines', None)
    if lst_diary_lines is None or len(lst_diary_lines) == 0:
        # Read the diary file if lst_diary_lines is empty
        lst_diary_lines = read_diary_file(runtime.state.get('diary_file_path', None))
        runtime.state["lst_diary_lines"] = lst_diary_lines

    start_idx = None
    end_idx = None

    # Pattern to match the target date entry line (allowing leading whitespace and -)
    target_pattern = rf'^\s*\-\s*{re.escape(date)}'

    # Pattern to match any date entry line
    date_pattern = r'^\s*\-\s*\d{4}-\d{2}-\d{2}'

    # Find the start index of the target date entry
    for i, line in enumerate(lst_diary_lines):
        if re.match(target_pattern, line):
            # print(f"##### start_idx: {i}")
            start_idx = i
            break

    if start_idx is None:
        logger.error(f"##### start_idx not found: {date}")
        return ""

    # Find the end index (next date entry)
    for i in range(start_idx + 1, len(lst_diary_lines)):
        if re.match(date_pattern, lst_diary_lines[i]):
            # print(f"##### end_idx: {i}")
            end_idx = i
            break

    # If no next date entry found, go to end of list
    end_idx = end_idx if end_idx is not None else len(lst_diary_lines)

    # Return the diary entry
    # return '\n'.join(lst_diary_lines[start_idx:end_idx])
    return Command(update={
        # "str_day_diary": '\n'.join(lst_diary_lines[start_idx:end_idx]),
        "lst_diary_lines": lst_diary_lines,
        # update the message history
        "messages": [
            ToolMessage(
                '\n'.join(lst_diary_lines[start_idx:end_idx]),
                tool_call_id=runtime.tool_call_id
            )
        ]
    })


# Get month diary
@tool
def get_month_diary(runtime: ToolRuntime, date: str) -> str:
    """Read the diary for a specific month.

    Args:
        runtime: The runtime object.
        date: The date to read the diary for, in the format YYYY-MM
    """

    lst_diary_lines = runtime.state.get('lst_diary_lines', None)
    if lst_diary_lines is None or len(lst_diary_lines) == 0:
        # Read the diary file if lst_diary_lines is empty
        lst_diary_lines = read_diary_file(runtime.state.get('diary_file_path', None))
        runtime.state["lst_diary_lines"] = lst_diary_lines

    # Get month from date
    str_year = date.split('-')[0]
    str_month = date.split('-')[1]
    str_next_month = str(int(str_month) + 1).zfill(2)
    str_next_month_with_year = f"{str_year}-{str_next_month}"

    start_idx = None
    end_idx = None
    
    # Pattern to match the target date entry line (allowing leading whitespace and -)
    target_pattern = rf'^\s*\-\s*{re.escape(date)}'
    next_month_pattern = rf'^\s*\-\s*{re.escape(str_next_month_with_year)}'

    # Pattern to match any date entry line
    date_pattern = r'^\s*\-\s*\d{4}-\d{2}-\d{2}'

    # Find the start index of the target date entry
    for i, line in enumerate(lst_diary_lines):
        if re.match(target_pattern, line):
            start_idx = i
            break

    if start_idx is None:
        logger.error(f"##### start_idx not found: {date}")
        return ""

    # Find the end index (str_next_month_with_year)
    for i in range(start_idx + 1, len(lst_diary_lines)):
        if re.match(next_month_pattern, lst_diary_lines[i]):
            end_idx = i
            break

    # If no next date entry found, go to end of list
    end_idx = end_idx if end_idx is not None else len(lst_diary_lines)

    # Return the diary entry
    return '\n'.join(lst_diary_lines[start_idx:end_idx])

# Get year diary
@tool
def get_year_diary(runtime: ToolRuntime, date: str) -> str:
    """Read the diary for a specific year.

    Args:
        runtime: The runtime object.
        date: The date to read the diary for, in the format YYYY
    """
    lst_diary_lines = runtime.state.get('lst_diary_lines', None)
    if lst_diary_lines is None or len(lst_diary_lines) == 0:
        # Read the diary file if lst_diary_lines is empty
        lst_diary_lines = read_diary_file(runtime.state.get('diary_file_path', None))
        runtime.state["lst_diary_lines"] = lst_diary_lines

    # 直接返回全部日记
    return '\n'.join(lst_diary_lines)

def show_diary(diary: str) -> None:
    """Show the diary text.

    Args:
        diary: The diary string to show.
    """
    print(diary)


@tool
def calc_sum_from_expression(expression: str) -> int:
    """Calculate the sum from the given expression.

    Args:
        expression: The expression string to calculate. e.g.: "+2-3+1+2-4+2"
    
    Returns:
        The sum of the expression.
    """
    # Split the expression into a list of tokens
    tokens = re.findall(r'[+-]\d+', expression)
    # Convert tokens to integers
    nums = [int(token) for token in tokens]
    # Calculate the sum
    ret_sum = sum(nums)
    logger.trace(f"sum up: {expression} = {ret_sum}")
    return ret_sum


@tool
def get_plan(runtime: ToolRuntime, date: str) -> str:
    """获取指定时段的计划.

    Args:
        runtime: The runtime object.
        date: 计划日期. 如果是月度计划, 则格式为YYYY-MM. 如果是季度计划, 则格式为YYYY-Sn(表示第n季度).
    """

    plan_file_path = runtime.state.get('plan_file_path', None)
    llm = runtime.state.get('llm', None)
    if llm is None:
        logger.error(f"##### llm not found in state")
        return "错误: 未配置llm模型."
    
    # 获取计划文件时间标签
    str_plan_date = None
    try:
        # 获取计划文件的最后修改时间戳
        mtime = os.path.getmtime(plan_file_path)
        # 将时间戳转换为格式化字符串
        str_plan_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except FileNotFoundError:
        logger.error(f"##### plan file not found: {plan_file_path}")
    except Exception as e:
        logger.error(f"##### failed to get plan file time: {e}")
    
    if str_plan_date is None:
        logger.error(f"##### plan date not found: {plan_file_path}")
        return "错误: 计划文件时间标签获取失败."

    logger.trace(f"##### plan date: {str_plan_date}")

    # 计划文件与缓存内容记录的时间标签对比, 计划文件更新, 则重新调用llm读取计划文件, 并更新缓存内容(如果没有缓存文件则创建). 否则使用缓存内容.
    # 缓存文件路径为: ./.aid/cache/plan.json. 如果目录不存在, 则创建目录.
    # 缓存文件内容格式为: {YYYY-MM: {"update": "2025-12-01 12:00:00", "plan": "计划内容文本"}}
    cache_file_path = os.path.join(".", ".aid", "cache", "plan.json")
    
    # 确保缓存目录存在
    cache_dir = os.path.dirname(cache_file_path)
    os.makedirs(cache_dir, exist_ok=True)
    
    # 读取缓存内容
    cache_data = {}
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"##### Failed to decode cache file: {cache_file_path}")
            cache_data = {}
    
    # 检查缓存是否存在且未过期(缓存日期比计划文件更新时间晚)
    if date in cache_data and cache_data[date]["update"] >= str_plan_date:
        # 使用缓存内容
        logger.debug(f"##### Using cached plan for {date}")
        return cache_data[date]["plan"]
    
    # 缓存不存在或已过期，重新读取计划文件
    try:
        with open(plan_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except FileNotFoundError:
        logger.error(f"##### Plan file not found: {plan_file_path}")
        return "错误: 计划文件不存在."
    
    # 调用llm提取计划内容
    # plan_content = file_content
    plan_content = ""
    try:
        # plan_content = llm.invoke(f"请提取{date}的计划内容. 精确的输出提取到的计划原文内容, 不要添加与修改文本, 要全部计划内容如下:\n{file_content}").content
        plan_content = llm.invoke(f"请提取{date}的计划内容. 精确的输出提取到的计划原文内容, 不要添加与修改文本, 要全部计划内容如下:\n{file_content}").content
        # print(f"plan_content: >>>>{plan_content}<<<<")

        #for chunk in agent.stream({
        #    "messages": [{"role": "user", "content": user_input}],
        #    # "lst_diary_lines": [],
        #    "diary_file_path": diary_file_path,
        #}, {
        #    "configurable": {"thread_id": "1"}
        #}, stream_mode="values"):
    except Exception as e:
        logger.error(f"##### Failed to invoke llm: {e}")
        return "错误: 调用llm模型提取计划失败."
    
    # 更新缓存
    cache_data[date] = {
        "update": str_plan_date,
        "plan": plan_content
    }
    
    try:
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.debug(f"##### Cache updated for {date}")
    except Exception as e:
        logger.error(f"##### Failed to save cache: {e}")
    
    # 返回计划内容
    return plan_content

