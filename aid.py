#!/usr/bin/env python

import argparse
# from code import interact
import datetime, os, json
from typing import Any
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
# from pydantic_core.core_schema import is_instance_schema
from utils import logger
import tools

class CustomState(AgentState):
    user_preferences: dict
    diary_file_path: str = ""
    plan_file_path: str = ""
    lst_diary_lines: list[str] = []
    llm: ChatDeepSeek | ChatOpenAI | OllamaLLM = None

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    # tools = [tool1, tool2]

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        logger.debug(f"before_model: {state}")

logger.debug("start")

load_dotenv()

# 加载 aid_config.json 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'aid_config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

diary_file_path = config["diary_file"]
plan_file_path = config["plan_file"]



# ------------------------------------------------------------------------------
# models 
# ------------------------------------------------------------------------------

# 从配置文件中获取模型配置, 并创建模型
model_config = config["model_config"]
logger.debug(f"model_config: {model_config}")
default_model_name = config["model_selection"]["default_model"]

llms = {}

for model in model_config:
    name = model["name"]
    model_name = model["model_name"]
    model_api_url = model["model_api_url"]
    model_api_key_name = model["api_key_name"]
    model_api_key = os.getenv(model_api_key_name)
    
    logger.debug(f"name: {name}, model_name: {model_name}, model_api_url: {model_api_url}, model_api_key_name: {model_api_key_name}")

    if name == "deepseek":
        api_key_deepseek = model_api_key
        llms[name] = ChatDeepSeek(
            # model="deepseek-chat",
            model=model_name,
            api_key=api_key_deepseek,
            streaming=True,  # 启用流式输出
        )
    elif name == "ollama":
        llms[name] = OllamaLLM(
            model=model_name,
            # base_url=model_api_url,
            # api_key=model_api_key,
        )
    elif name == "qwen":
        # TODO: change to qwen specific creation
        llms[name] = ChatOpenAI(
            model_name=model_name,
            api_key=model_api_key,
            base_url=model_api_url,
        )
    else:
        llms[name] = name
        llms[name] = ChatOpenAI(
            model_name=model_name,
            api_key=model_api_key,
            base_url=model_api_url,
        )
    logger.trace(f"    model:{name}: {llms[name]}")

if len(llms) == 0:
    raise ValueError("No valid model configuration found in aid_config.json")

default_llm = llms[default_model_name]
logger.debug(f"default_llm: {default_llm}")

# 从配置文件中读取模型选择
model_selection = config["model_selection"]
logger.debug(f"model_selection: {model_selection}")

# ------------------------------------------------------------------------------
# tools 
# ------------------------------------------------------------------------------

lst_tools = [
    tools.get_current_date_time,
    tools.read_diary_file,
    tools.get_day_diary,
    tools.get_month_diary,
    tools.get_year_diary,
    tools.calc_sum_from_expression,
    tools.get_plan,
    tools.email_receive_diary_pop,
]

# Create system prompt for the agent
# Read system prompt from file
prompt_file_path = os.path.join(script_dir, 'aid_prompt_system.md')
with open(prompt_file_path, 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT = f.read()



is_bold = False
is_italic = False
def print_markdown_to_bash_shell(markdown_text: str) -> str:
    """
    将Markdown格式的文本转换为Bash Shell脚本格式.

    :param markdown_text: Markdown格式的文本
    :return: 转换后的Bash Shell脚本格式文本
    """
    global is_bold
    global is_italic
    
    # 处理加粗语法 **内容**
    i = 0
    while i < len(markdown_text):
        # 检查是否遇到加粗标记
        if markdown_text[i:i+2] == "**":
            # 切换加粗状态
            if not is_bold:
                print("\033[01;4m", flush=True, end = "")
                is_bold = True
            else:
                print("\033[0m", flush=True, end = "")
                is_bold = False
            i += 2  # 跳过两个星号

        # 检查是否遇到斜体标记
        elif markdown_text[i] == "_":
            # 切换斜体状态
            if not is_italic:
                print("\033[03;36m", flush=True, end = "")
                is_italic = True
            else:
                print("\033[0m", flush=True, end = "")
                is_italic = False
            i += 1  # 跳过1个星号
            
        # 检查是否遇到标题标记
        elif markdown_text[i] == "#":
            print("\033[01;34m", flush=True, end = "")
            print(f"{markdown_text[i]}", flush=True, end = "")
            i += 1
        # 检查是否遇到换行符
        elif markdown_text[i] == "\n":
            print(f"{markdown_text[i]}", flush=True, end = "")
            print("\033[0m", flush=True, end = "")
            is_bold = False
            i += 1
        else:
            print(f"{markdown_text[i]}", flush=True, end = "")
            i += 1
    
    if markdown_text.endswith("\n"):
        print("\033[0m", flush=True, end = "")
        is_bold = False


# Create a ReAct agent by LangGraph
def build_agent(llm, tools):
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        # middleware=[CustomMiddleware()],
        state_schema=CustomState,
        checkpointer=InMemorySaver(),
        # debug=True,
    )
    return agent



if __name__ == "__main__":
    logger.debug("main")
    # 获取命令行参数
    #     -h, --help: show help message
    #     -v, --version: show version
    #     -u, --user-prompt: user prompt
    #     -i, --interactive: interactive mode

    parser = argparse.ArgumentParser(description="Aid - AI Assistant for Diary Management")
    parser.add_argument("-s", "--shell", action="store_true", help="show in bash shell")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s 1.0")
    parser.add_argument("-v", "--verbose", help="verbose mode")
    parser.add_argument("-u", "--user_prompt", type=str, help="user prompt")
    parser.add_argument("-i", "--interactive", action="store_true", help="interactive mode")

    args = parser.parse_args()
    mode = None
    in_shell = args.shell
    if args.verbose:
        print(f"verbose: {args.verbose}")
        logger.set_level(int(args.verbose))

    if args.user_prompt:
        mode = "once"
    elif args.interactive:
        mode = "interactive"
        print("请输入您的问题（输入'q'结束）：")
    else:
        parser.print_help()
        exit(1)

    # Create agent instance
    agent = build_agent(default_llm, lst_tools)
    logger.debug(f"Created agent: {agent}")

    user_input = ""
    if args.user_prompt:
        user_input = args.user_prompt

    # 循环相应用户输入
    while True:
        if args.interactive:
            print("\n>\033[01;35m", flush=True, end = "")
            user_input = input("")
            print("\033[0m", flush=True, end = "")
            if user_input == 'q':
                break
            if len(user_input.strip()) == 0:
                continue
        #response = agent.invoke({
        #    # "input": user_input,
        #    "messages": [{"role": "user", "content": user_input}]
        #})
        #print(response)

        # ----------------------------------------
        #for chunk in agent.stream({
        #    "messages": [{"role": "user", "content": user_input}],
        #    # "lst_diary_lines": [],
        #    "diary_file_path": diary_file_path,
        #}, {
        #    "configurable": {"thread_id": "1"}
        #}, stream_mode="values"):
        #    # Each chunk contains the full state at that point
        #    latest_message = chunk["messages"][-1]
        #    # logger.debug(f"##### message type: {type(latest_message)}, dir(latest_message): {dir(latest_message)}")
        #    if latest_message.content:
        #        print(f"\033[01;34m[{latest_message.type}]\033[0m >>>{latest_message.content}<<<")
        #    elif hasattr(latest_message, "tool_calls"):
        #        logger.debug(f"[Tool] Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
        #    else:
        #        logger.debug(f"##### chunk: {chunk}")


        # ----------------------------------------
        str_current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_prompt = f"当前时间: {str_current_time}\n{user_input}"
        is_reasoning = False
        for token, metadata in agent.stream(
            {
                "messages": [{"role": "user", "content": user_prompt}],
                "diary_file_path": diary_file_path,
                "plan_file_path": plan_file_path,
                # "llm": default_llm,
                "llm": llms["deepseek"],
            }, {
                "configurable": {"thread_id": "1"}
            },
            stream_mode="messages",
        ):
            # print(f"node: {metadata}")
            # print(f"content: {token}")
            if token.content_blocks and token.content_blocks[0]["type"] == "text":
                if is_reasoning:
                    is_reasoning = False
                    print("#####\n")
                if metadata["langgraph_node"] == "tools":
                    logger.trace(f"\033[02;37m[Tool] {token.content_blocks[0]['text']}\033[0m", flush=True, end = "")
                else:
                    if in_shell:
                        print_markdown_to_bash_shell(token.content_blocks[0]["text"])
                    else:
                        print(token.content_blocks[0]["text"], flush=True, end = "")
            elif token.content_blocks and token.content_blocks[0]["type"] == "reasoning":
                is_reasoning = True
                print(f"\033[02;37m{token.content_blocks[0]['reasoning']}\033[0m", flush=True, end = "")


        if not args.interactive:
            print("\033[0m\n")
            break
##