import os
import shutil
import json
from datetime import datetime, timedelta
from utils import logger

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# 获取当前工作目录（运行脚本的目录）
current_dir = os.getcwd()

def create_aid_workspace():
    """创建aid_workspace目录"""
    workspace_dir = os.path.join(current_dir, "aid_workspace")
    # 转换为相对路径
    rel_workspace_dir = os.path.relpath(workspace_dir)
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)
        logger.info(f"创建目录: {rel_workspace_dir}")
    else:
        logger.info(f"目录 {rel_workspace_dir} 已存在")
    return workspace_dir

def copy_sample_files(workspace_dir):
    """将模板文件拷贝到aid_workspace目录"""
    samples_dir = os.path.join(script_dir, "samples")
    current_year = datetime.now().year
    
    # 拷贝plan_sample.md，去掉_sample后缀，添加年份
    plan_src = os.path.join(samples_dir, "plan_sample.md")
    plan_dest = os.path.join(workspace_dir, f"{current_year}_plan.md")
    # 转换为相对路径
    rel_plan_src = os.path.relpath(plan_src)
    rel_plan_dest = os.path.relpath(plan_dest)
    if os.path.exists(plan_src):
        shutil.copy2(plan_src, plan_dest)
        logger.info(f"拷贝 plan_sample.md 到 {rel_plan_dest}")
    else:
        logger.error(f"文件 {rel_plan_src} 未找到")
    
    # 拷贝diary_sample.md，去掉_sample后缀，添加年份
    diary_src = os.path.join(samples_dir, "diary_sample.md")
    diary_dest = os.path.join(workspace_dir, f"{current_year}_diary.md")
    # 转换为相对路径
    rel_diary_src = os.path.relpath(diary_src)
    rel_diary_dest = os.path.relpath(diary_dest)
    if os.path.exists(diary_src):
        shutil.copy2(diary_src, diary_dest)
        logger.info(f"拷贝 diary_sample.md 到 {rel_diary_dest}")
    else:
        logger.error(f"文件 {rel_diary_src} 未找到")
    
    return diary_dest

def generate_diary_content(diary_file):
    """生成全年的周数和日期到diary.md文件"""
    current_year = datetime.now().year
    
    # 从1月1日开始
    start_date = datetime(current_year, 1, 1)
    
    # 计算第一周的开始日期（如果1月1日不是周一，仍然从1月1日开始算第一周）
    week_start = start_date
    week_num = 1
    
    content = []
    
    # 添加日历标题
    content.append(f"\n===========================================================")
    content.append(f"以上是例子内容, 您可以将本行以及以上内容都删除，并开始您的日记！")
    content.append(f"\n## {current_year}年日历")
    content.append("")
    
    # 生成全年的周数和日期
    while week_start.year == current_year:
        # 添加周标题
        content.append(f"第{week_num:02d}周:")
        
        # 生成一周的日期
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            if current_date.year != current_year:
                break
            
            # 获取星期几（实际计算，不是假设）
            weekday_num = current_date.weekday()  # 0-6，0表示周一
            weekday = "周一" if weekday_num == 0 else "周二" if weekday_num == 1 else "周三" if weekday_num == 2 else "周四" if weekday_num == 3 else "周五" if weekday_num == 4 else "周六" if weekday_num == 5 else "周日"
            content.append(f"- {current_date.strftime('%Y-%m-%d')} {weekday}:")
        
        # 添加周与周之间的空行
        content.append("")
        
        # 下一周的开始日期
        week_start += timedelta(days=7)
        week_num += 1
    
    # 追加到文件（保留原有内容）
    with open(diary_file, 'a', encoding='utf-8') as f:
        f.write('\n'.join(content))
    # 转换为相对路径
    rel_diary_file = os.path.relpath(diary_file)
    logger.info(f"在 {rel_diary_file} 中追加 {current_year} 年的日记内容")

def copy_config_files(workspace_dir):
    """拷贝配置文件"""
    samples_dir = os.path.join(script_dir, "samples")
    
    # 拷贝aid_config-sample.json为workspace/aid_config.json
    config_src = os.path.join(samples_dir, "aid_config-sample.json")
    config_dest = os.path.join(workspace_dir, "aid_config.json")
    # 转换为相对路径
    rel_config_src = os.path.relpath(config_src)
    rel_config_dest = os.path.relpath(config_dest)
    if os.path.exists(config_src):
        if not os.path.exists(config_dest):
            shutil.copy2(config_src, config_dest)
            logger.info(f"拷贝 {rel_config_src} 到 {rel_config_dest}")
        else:
            logger.info(f"文件 {rel_config_dest} 已存在，跳过")
    else:
        logger.error(f"文件 {rel_config_src} 未找到")
    
    # 拷贝.env.sample为.env
    env_src = os.path.join(samples_dir, ".env.sample")
    env_dest = os.path.join(workspace_dir, ".env")
    # 转换为相对路径
    rel_env_src = os.path.relpath(env_src)
    rel_env_dest = os.path.relpath(env_dest)
    if os.path.exists(env_src):
        if not os.path.exists(env_dest):
            shutil.copy2(env_src, env_dest)
            logger.info(f"拷贝 {rel_env_src} 到 {rel_env_dest}")
        else:
            logger.info(f"文件 {rel_env_dest} 已存在，跳过")
    else:
        logger.error(f"文件 {rel_env_src} 未找到")
    
    # 修改 config.json 中的日记文件路径 和 计划文件路径
    config_file = os.path.join(workspace_dir, "aid_config.json")
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 使用相对路径，添加年份
        current_year = datetime.now().year
        config['diary_file'] = f'{current_year}_diary.md'
        config['plan_file'] = f'{current_year}_plan.md'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"更新 {os.path.relpath(config_file)} 中的文件路径")
    


def init_project():
    """初始化项目的主函数"""
    logger.info("正在初始化 Aid 项目...")
    
    # 1. 创建aid_workspace目录
    workspace_dir = create_aid_workspace()
    
    # 2. 拷贝模板文件
    diary_file = copy_sample_files(workspace_dir)
    
    # 3. 生成日记内容
    generate_diary_content(diary_file)
    
    # 4. 拷贝配置文件
    copy_config_files(workspace_dir)
    
    # 5. 提示用户
    logger.info("\n初始化完成！")
    logger.info("请修改以下文件：")
    current_year = datetime.now().year
    logger.info(f"1. aid_config.json - 更新日记文件和计划文件路径（文件名为 diary_{current_year}.md 和 plan_{current_year}.md）")
    logger.info("2. .env - 设置您的 MODEL_API_KEY")
    logger.info("\n然后您可以按照 README 中的说明运行 aid.py。")

if __name__ == "__main__":
    init_project()
