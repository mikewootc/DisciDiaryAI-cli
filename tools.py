import os
import re, json
import datetime
import imaplib
import poplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from utils import logger

load_dotenv()


EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT'))
EMAIL_RECV_SERVER = os.getenv('EMAIL_RECV_SERVER')
EMAIL_ACCOUNT=os.getenv('EMAIL_ACCOUNT')
# EMAIL_PASSWORD=os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVE_KEY = os.getenv('EMAIL_RECEIVE_KEY')
EMAIL_ACCOUNT_PEER=os.getenv('EMAIL_ACCOUNT_PEER')

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

#def email_receive_diary(runtime: ToolRuntime) -> str:
#    """接收指定邮箱的邮件, 从邮箱中提取日记片段. 并返回日记片段内容.
#        1. 从 cache 文件中上次接收邮件的时间戳开始, 接收所有未读邮件.
#        2. 从邮件内容中提取日记片段. 并将新时间戳记录到 cache 中.
#        3. 返回提取到的日记片段.
#
#    Args:
#        runtime: The runtime object.
#    """
#    try:
#        # 1. 获取缓存文件中的上次接收时间戳
#        cache_file_path = os.path.join(".", ".aid", "cache", "cache.json")
#        cache_data = {}
#        last_receive_time = None
#        
#        # 确保缓存目录存在
#        cache_dir = os.path.dirname(cache_file_path)
#        os.makedirs(cache_dir, exist_ok=True)
#        
#        # 读取缓存文件
#        if os.path.exists(cache_file_path):
#            try:
#                with open(cache_file_path, "r", encoding="utf-8") as f:
#                    cache_data = json.load(f)
#                last_receive_time_str = cache_data.get("last_email_receive_time")
#                if last_receive_time_str:
#                    try:
#                        last_receive_time = datetime.datetime.strptime(last_receive_time_str, "%Y-%m-%d %H:%M:%S")
#                    except ValueError:
#                        logger.error(f"##### Invalid date format in cache: {last_receive_time_str}")
#                        last_receive_time = None
#            except json.JSONDecodeError:
#                logger.error(f"##### Failed to decode cache file: {cache_file_path}")
#                cache_data = {}
#                last_receive_time = None
#        
#        # 2. 连接到邮件服务器
#        # 添加缺失的命令
#        imaplib.Commands['ID'] = ('AUTH')
#        imap = imaplib.IMAP4_SSL(EMAIL_RECV_SERVER)
#        logger.debug(f"##### Connected to IMAP server: {EMAIL_RECV_SERVER}")
#        
#        # 登录邮箱
#        login_status, login_data = imap.login(EMAIL_ACCOUNT, EMAIL_RECEIVE_KEY)
#        if login_status != 'OK':
#            login_error = login_data[0].decode('utf-8') if login_data else "未知错误"
#            logger.error(f"##### Failed to login: {login_error}")
#            
#            # 针对126.com/163.com的安全限制错误提供指导
#            if any(keyword in login_error for keyword in ["Unsafe Login", "安全登录", "授权"]):
#                return f"错误: 邮箱登录失败. 服务器信息: {login_error}\n\n" \
#                       f"解决方案: 1. 登录网页版邮箱，检查安全通知并授权登录\n" \
#                       f"          2. 启用IMAP/SMTP服务：设置 → POP3/SMTP/IMAP → 开启IMAP服务\n" \
#                       f"          3. 生成授权码：使用授权码代替登录密码\n" \
#                       f"          4. 联系邮箱客服获取帮助"
#            
#            return f"错误: 邮箱登录失败. 服务器信息: {login_error}"
#        logger.debug(f"##### Logged in to email account: {EMAIL_ACCOUNT}")
#        
#        # 选择收件箱
#        select_status, select_data = imap.select("inbox")
#        if select_status != 'OK':
#            error_msg = select_data[0].decode('utf-8') if select_data else "未知错误"
#            logger.error(f"##### Failed to select inbox: {error_msg}")
#            imap.logout()
#            
#            # 针对126.com/163.com的安全限制错误提供更详细的指导
#            # 匹配包含"Unsafe Login"或"安全登录"的错误信息
#            if any(keyword in error_msg for keyword in ["Unsafe Login", "安全登录", "授权失败"]):
#                detailed_msg = f"错误: 邮箱服务器安全限制. 服务器信息: {error_msg}\n\n"
#                detailed_msg += "解决方案: 请按照以下步骤操作:\n"
#                detailed_msg += "1. 登录网页版邮箱，检查安全通知并授权本次登录\n"
#                detailed_msg += "2. 启用IMAP/SMTP服务：设置 → POP3/SMTP/IMAP → 开启IMAP服务\n"
#                detailed_msg += "3. 生成授权码：在邮箱设置中生成专用授权码，使用授权码代替密码\n"
#                detailed_msg += "4. 如仍有问题，请联系邮箱客服获取帮助\n"
#                return detailed_msg
#            
#            return f"错误: 选择收件箱失败. 服务器信息: {error_msg}"
#        logger.debug(f"##### Selected inbox with {select_data[0]} messages")
#        
#        # 3. 搜索未读邮件
#        status, messages = imap.search(None, "UNSEEN")
#        if status != 'OK':
#            logger.error(f"##### Failed to search messages: {messages}")
#            imap.close()
#            imap.logout()
#            return "错误: 搜索邮件失败."
#        message_ids = messages[0].split()
#        logger.debug(f"##### Found {len(message_ids)} unread messages")
#        
#        diary_fragments = []
#        latest_receive_time = datetime.datetime.now()
#        
#        # 4. 遍历所有未读邮件
#        for msg_id in message_ids:
#            # 获取邮件内容
#            status, msg_data = imap.fetch(msg_id, "(RFC822)")
#            
#            # 解析邮件
#            for response_part in msg_data:
#                if isinstance(response_part, tuple):
#                    msg = email.message_from_bytes(response_part[1])
#                    
#                    # 获取发件人信息
#                    from_ = msg["From"]
#                    sender_email = from_.split("<")[-1].rstrip(">")
#                    
#                    # 只处理来自指定发件人的邮件
#                    if sender_email != EMAIL_ACCOUNT_PEER:
#                        continue
#                    
#                    # 获取邮件主题
#                    subject, encoding = decode_header(msg["Subject"])[0]
#                    if isinstance(subject, bytes):
#                        subject = subject.decode(encoding if encoding else "utf-8")
#                    
#                    # 获取邮件正文
#            body = ""
#            if msg.is_multipart():
#                for part in msg.walk():
#                    content_type = part.get_content_type()
#                    content_disposition = str(part.get("Content-Disposition"))
#                    
#                    try:
#                        if content_type == "text/plain" and "attachment" not in content_disposition:
#                            payload = part.get_payload(decode=True)
#                            # 尝试多种编码解码
#                            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
#                            for encoding in encodings:
#                                try:
#                                    body = payload.decode(encoding)
#                                    break
#                                except UnicodeDecodeError:
#                                    continue
#                            else:
#                                # 如果所有编码都失败，使用latin-1作为兜底
#                                body = payload.decode('latin-1', errors='replace')
#                            break
#                    except Exception as e:
#                        logger.error(f"##### Failed to decode email body: {e}")
#            else:
#                content_type = msg.get_content_type()
#                if content_type == "text/plain":
#                    try:
#                        payload = msg.get_payload(decode=True)
#                        # 尝试多种编码解码
#                        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
#                        for encoding in encodings:
#                            try:
#                                body = payload.decode(encoding)
#                                break
#                            except UnicodeDecodeError:
#                                continue
#                        else:
#                            # 如果所有编码都失败，使用latin-1作为兜底
#                            body = payload.decode('latin-1', errors='replace')
#                    except Exception as e:
#                        logger.error(f"##### Failed to decode email body: {e}")
#                    
#                    # 将邮件正文作为日记片段
#                    if body:
#                        print(f"##### Received email from {sender_email} with subject: {subject}")
#                        diary_fragments.append(body)
#        
#        # 5. 更新缓存文件中的时间戳
#        cache_data["last_email_receive_time"] = latest_receive_time.strftime("%Y-%m-%d %H:%M:%S")
#        try:
#            with open(cache_file_path, "w", encoding="utf-8") as f:
#                json.dump(cache_data, f, ensure_ascii=False, indent=2)
#            logger.debug(f"##### Email receive time updated in cache")
#        except Exception as e:
#            logger.error(f"##### Failed to save cache: {e}")
#        
#        # 6. 关闭邮件连接
#        imap.close()
#        imap.logout()
#        
#        # 返回提取到的日记片段
#        return "\n".join(diary_fragments) if diary_fragments else ""
#        
#    except Exception as e:
#        logger.error(f"##### Failed to receive email: {e}")
#        return "错误: 接收邮件失败."


def email_receive_diary_pop(runtime: ToolRuntime) -> str:
    """
    从指定邮箱接收未读日记邮件，提取其中的内容作为日记片段。 仅处理来自指定发件人的邮件。
        1. 从 cache 文件中上次接收邮件的时间戳开始, 接收所有未读邮件.
        2. 从邮件内容中提取日记片段. 并将新时间戳记录到 cache 中.
        3. 返回提取到的日记片段.

    Args:
        runtime: The runtime object.
    """
    try:
        # 1. 获取缓存文件中的上次接收时间戳
        cache_file_path = os.path.join(".", ".aid", "cache", "cache.json")
        cache_data = {}
        last_receive_time = None
        
        # 确保缓存目录存在
        cache_dir = os.path.dirname(cache_file_path)
        os.makedirs(cache_dir, exist_ok=True)
        
        # 读取缓存文件
        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                last_receive_time_str = cache_data.get("last_email_receive_time")
                if last_receive_time_str:
                    try:
                        last_receive_time = datetime.datetime.strptime(last_receive_time_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        logger.error(f"##### Invalid date format in cache: {last_receive_time_str}")
                        last_receive_time = None
            except json.JSONDecodeError:
                logger.error(f"##### Failed to decode cache file: {cache_file_path}")
                cache_data = {}
                last_receive_time = None
        
        # 2. 连接到POP3服务器
        pop = poplib.POP3_SSL(EMAIL_RECV_SERVER)
        logger.debug(f"##### Connected to POP3 server: {EMAIL_RECV_SERVER}")
        
        # 登录邮箱
        try:
            pop.user(EMAIL_ACCOUNT)
            pop.pass_(EMAIL_RECEIVE_KEY)
        except poplib.error_proto as e:
            login_error = str(e)
            logger.error(f"##### Failed to login: {login_error}")
            
            # 针对126.com/163.com的安全限制错误提供指导
            if any(keyword in login_error for keyword in ["Unsafe Login", "安全登录", "授权"]):
                return f"错误: 邮箱登录失败. 服务器信息: {login_error}\n\n" \
                       f"解决方案: 1. 登录网页版邮箱，检查安全通知并授权登录\n" \
                       f"          2. 启用POP3/SMTP服务：设置 → POP3/SMTP/IMAP → 开启POP3服务\n" \
                       f"          3. 生成授权码：使用授权码代替登录密码\n" \
                       f"          4. 联系邮箱客服获取帮助"
            
            return f"错误: 邮箱登录失败. 服务器信息: {login_error}"
        logger.debug(f"##### Logged in to email account: {EMAIL_ACCOUNT}")
        
        # 获取邮件数量和大小
        num_messages = len(pop.list()[1])
        logger.debug(f"##### Total messages in inbox: {num_messages}")
        
        diary_fragments = []
        latest_receive_time = datetime.datetime.now()
        
        # 3. 遍历所有邮件
        for msg_num in range(1, num_messages + 1):
            # 获取邮件内容
            resp, lines, octets = pop.retr(msg_num)
            
            # 解析邮件
            msg_content = b"\n".join(lines)
            msg = email.message_from_bytes(msg_content)
            
            # 获取发件人信息
            from_ = msg["From"]
            sender_email = from_.split("<")[-1].rstrip(">")
            
            # 只处理来自指定发件人的邮件
            if sender_email != EMAIL_ACCOUNT_PEER:
                continue

            # 获取邮件主题
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            # 判断时间是否比上次接收时间新
            date_str = msg["Date"]
            date = email.utils.parsedate_to_datetime(date_str)
            # 移除时区信息，以便与缓存中的时间戳比较
            if date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            if last_receive_time and date <= last_receive_time:
                continue
            
            # 获取邮件正文
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    try:
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            # 尝试多种编码解码
                            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                            for encoding in encodings:
                                try:
                                    body = payload.decode(encoding)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                # 如果所有编码都失败，使用latin-1作为兜底
                                body = payload.decode('latin-1', errors='replace')
                            break
                    except Exception as e:
                        logger.error(f"##### Failed to decode email body: {e}")
            else:
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = msg.get_payload(decode=True)
                        # 尝试多种编码解码
                        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                        for encoding in encodings:
                            try:
                                body = payload.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # 如果所有编码都失败，使用latin-1作为兜底
                            body = payload.decode('latin-1', errors='replace')
                    except Exception as e:
                        logger.error(f"##### Failed to decode email body: {e}")
            
            # 将邮件正文作为日记片段
            if body:
                print(f"##### Received email from {sender_email} with subject: {subject}")
                diary_fragments.append(body)
        
        # 4. 更新缓存文件中的时间戳
        cache_data["last_email_receive_time"] = latest_receive_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"##### Email receive time updated in cache")
        except Exception as e:
            logger.error(f"##### Failed to save cache: {e}")
        
        # 5. 关闭邮件连接
        pop.quit()
        
        # 返回提取到的日记片段
        if not diary_fragments:
            logger.debug("##### No new emails received.")
            return "没有新的邮件."
        return "\n".join(diary_fragments) if diary_fragments else ""
        
    except Exception as e:
        logger.error(f"##### Failed to receive email via POP3: {e}")
        return "错误: 接收邮件失败."


def email_send_notification(runtime: ToolRuntime, subject: str, body: str) -> str:
    """发送指定邮箱的通知邮件.

    Args:
        runtime: The runtime object.
        subject: The subject of the email.
        body: The body of the email.
    """
    try:
        # 1. 配置SMTP服务器
        smtp_server = EMAIL_SMTP_SERVER
        smtp_port = EMAIL_SMTP_PORT
        smtp_username = EMAIL_ACCOUNT
        smtp_password = EMAIL_RECEIVE_KEY

        logger.debug(f"##### send notification email. enter.")
        # 2. 创建SMTP连接
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            # server.starttls()
            logger.debug(f"##### Log in ...")
            server.login(smtp_username, smtp_password)
            logger.debug(f"##### Logged in OK")

            # 3. 构造邮件
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = EMAIL_ACCOUNT_PEER

            # 4. 发送邮件
            str_msg = msg.as_string()
            logger.debug(f"##### Email content: {str_msg}")
            server.sendmail(smtp_username, EMAIL_ACCOUNT_PEER, str_msg)
            logger.debug(f"##### Notification email sent to {EMAIL_ACCOUNT_PEER} with subject: {subject}")
            return "通知邮件发送成功."
    except Exception as e:
        logger.error(f"##### Failed to send notification email: {e}")
        return "错误: 发送通知邮件失败."