import gitlab
from datetime import datetime, timedelta
import configparser
import os

# --- 1. 读取配置文件 ---
config = configparser.ConfigParser()
config_file = 'config.ini'

if not os.path.exists(config_file):
    print(f"错误：配置文件 '{config_file}' 不存在。请创建该文件并配置相关信息。")
    exit()

try:
    config.read(config_file)

    # GitLab 配置
    GITLAB_URL = config.get('gitlab', 'url')
    PRIVATE_TOKEN = config.get('gitlab', 'private_token')
    USERNAME = config.get('gitlab', 'username')

    # 日期范围配置
    START_DATE_STR = config.get('date_range', 'start_date')
    END_DATE_STR = config.get('date_range', 'end_date')

except configparser.Error as e:
    print(f"错误：读取配置文件时出错。请检查格式是否正确。{e}")
    exit()

# 将日期字符串转换为 ISO 8601 格式
start_date_obj = datetime.strptime(START_DATE_STR, '%Y-%m-%d')
end_date_obj = datetime.strptime(END_DATE_STR, '%Y-%m-%d') + timedelta(days=1)
SINCE_DATE = start_date_obj.isoformat() + 'Z'
UNTIL_DATE = end_date_obj.isoformat() + 'Z'

# --- 2. 初始化 GitLab 客户端 ---
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

try:
    # --- 3. 获取用户 ID ---
    print(f"正在获取用户 '{USERNAME}' 的信息...")
    users = gl.users.list(username=USERNAME)
    if not users:
        print(f"错误：未找到用户 '{USERNAME}'。请检查用户名是否正确。")
        exit()
    user_id = users[0].id
    print(f"用户 ID：{user_id}")

    # --- 4. 获取所有你拥有的或作为成员的项目 ---
    print("\n正在获取所有你（或你的访问令牌）有权限访问的项目...")
    all_projects = gl.projects.list(owned=True, membership=True, all=True)
    print(f"找到 {len(all_projects)} 个项目。")

    total_commits = 0
    projects_with_commits = {}

    # --- 5. 遍历每个项目并统计指定用户的提交 ---
    print("\n开始统计提交数...")
    for project in all_projects:
        try:
            commits = project.commits.list(author_id=user_id, since=SINCE_DATE, until=UNTIL_DATE, all=True)
            commit_count = len(commits)

            if commit_count > 0:
                projects_with_commits[project.name] = commit_count
                total_commits += commit_count
                print(f"  - 项目 '{project.name}'：找到 {commit_count} 次提交。")

        except gitlab.exceptions.GitlabError as e:
            if e.response_code == 404:
                print(f"  - 无法访问项目 '{project.name}'，跳过。")
            else:
                print(f"  - 访问项目 '{project.name}' 时发生错误：{e}")
            continue

    # --- 6. 打印结果 ---
    print("\n--- 统计报告 ---")
    print(f"日期范围：{START_DATE_STR} 至 {END_DATE_STR}")
    print(f"用户：{USERNAME}")
    print("------------------")

    if total_commits == 0:
        print("在此时间范围内没有找到任何提交。")
    else:
        for project_name, count in projects_with_commits.items():
            print(f"项目 '{project_name}'：{count} 次提交")

        print("------------------")
        print(f"总提交数：{total_commits} 次")

except gitlab.exceptions.GitlabError as e:
    print(f"GitLab API 错误：{e}")
except Exception as e:
    print(f"发生未知错误：{e}")