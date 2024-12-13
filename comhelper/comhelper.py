import importlib.resources
import json
import subprocess
import requests
import questionary
from questionary import Style
from rich.console import Console
import pyperclip  # 导入 pyperclip 用于剪切板操作
import argparse
import sys
import platform
import os
import psutil  # 新增导入

console = Console()

API_KEY = "fFB7iMf8ANCblJ37m92xPUCZ"
SECRET_KEY = "zFGTM7pmRpevYqnk81IVnXyQEE1xCEVm"

# 定义自定义样式
custom_style = Style([
    ('qmark', 'fg:#FF5733 bold'),  # 标签颜色
    ('question', 'bold'),  # 问题文本加粗
    ('answer', 'fg:#FF5733 bold'),  # 已选择的答案颜色
    ('pointer', 'fg:#00FF00 bold'),  # 当前选中的指针颜色
    ('highlighted', 'fg:#FFFF00 bold'),  # 高亮选中的选项
    ('selected', 'fg:#00FF00 bold'),  # 已选择选项的颜色
    ('separator', 'fg:#6C6C6C'),  # 分隔符颜色
    ('instruction', ''),  # 指令颜色
    ('text', ''),  # 普通文本颜色
    ('disabled', 'fg:#858585 italic')  # 禁用选项颜色
])

# 获取 access_token
def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    response = requests.post(url, params=params)
    try:
        return response.json().get("access_token")
    except ValueError:
        console.print("[red]无法获取 Access Token，返回内容不是有效的 JSON。[/red]")
        return None

# 读取 prompt 文件内容
def read_prompt_from_file(prompt):
    try:
        # 使用 importlib.resources 读取包内的 prompt.txt 文件
        with importlib.resources.open_text('comhelper', resource=prompt, encoding='utf-8') as file:
            prompt_content = file.read().strip()
            return prompt_content
    except FileNotFoundError:
        console.print(f"[red]{prompt} 文件未找到！[/red]")
        return ""

def execute_command(command):
    """
    执行命令行命令，并打印输出
    """
    try:
        # 执行命令
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # 输出命令的结果
        if result.returncode == 0:
            console.print(f"[green]命令执行成功:[/green] {result.stdout}")
            return 0
        else:
            console.print(f"[red]命令执行失败:[/red] {result.stderr}")
            return "executeFalse"

    except Exception as e:
        console.print(f"[red]执行命令时出错: {e}[/red]")
        return 0

def llm(message, Prompt):
    prompt = read_prompt_from_file(Prompt)  # 从文件中读取 prompt
    if not prompt and Prompt != "prompt_chat.txt":
        return "Promptfalse"

    # 获取 access_token
    access_token = get_access_token()
    if access_token is None:
        return "Access_Token_False"

    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-pro-128k?access_token={access_token}"

    # 构建消息内容，确保消息数量是奇数
    messages = [{"role": "user", "content": prompt + message}]

    payload = json.dumps({"messages": messages})
    headers = {'Content-Type': 'application/json'}

    # 发送请求
    response = requests.post(url, headers=headers, data=payload)

    # 解析响应
    try:
        response_data = response.json()  # 将响应解析为 JSON 格式
        if response.status_code == 200 and "result" in response_data:
            model_reply = response_data["result"]
            return model_reply
        else:
            console.print(f"[red]错误: {response_data.get('error_msg', '未知错误')}[/red]")
            return ""
    except ValueError:
        console.print("[red]无法解析响应，返回内容可能不是有效的 JSON。[/red]")
        return ""

def get_current_shell():
    """
    检测当前使用的 shell。
    在 Windows 上区分 PowerShell 和 cmd。
    在类 Unix 系统上，返回 SHELL 环境变量。
    """
    if platform.system() == "Windows":
        # 尝试通过环境变量检测 PowerShell
        if 'PSModulePath' in os.environ:
            return "PowerShell"
        else:
            # 使用 psutil 获取父进程名
            try:
                parent = psutil.Process(os.getppid())
                parent_name = parent.name().lower()
                if 'powershell' in parent_name:
                    return "PowerShell"
                elif 'cmd' in parent_name:
                    return "cmd.exe"
                else:
                    return parent_name
            except Exception:
                return os.environ.get('COMSPEC', 'Unknown')
    else:
        # 在类 Unix 系统上，使用 SHELL 环境变量
        return os.environ.get('SHELL', 'Unknown')

def collect_system_info():
    """
    收集当前系统和命令行环境信息
    """
    system_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "shell": get_current_shell(),  # 使用改进后的函数
        "cwd": os.getcwd(),  # 当前工作目录
        "env_vars": dict(os.environ)  # 所有环境变量
    }
    console.print(f"所在系统及命令行环境信息：{ system_info['system']},{system_info['shell']}")
    return system_info

def work():
    console.print("[bold blue]与 ERNIE 对话开始！输入 'exit' 退出。[/bold blue]")

    # 收集系统信息
    system_info = collect_system_info()
    system_info_str = json.dumps(system_info, indent=2, ensure_ascii=False)

    # 将系统信息传递给 prompt
    system_context = f"当前系统信息如下：\n{system_info_str}\n\n"

    while True:
        message = questionary.text("你: ").ask()

        if message.lower() == 'exit':
            console.print("[bold red]退出程序[/bold red]")
            break

        max_attempts = 3
        attempt = 0
        success = False

        while attempt < max_attempts:
            # 将系统上下文信息与用户消息合并
            full_message = system_context + message
            command = llm(full_message, 'prompt.txt')

            if command == "Access_Token_False":
                console.print("[bold red]您的密钥无效，请您检查您的 API_KEY 和 SECRET_KEY 是否正确。[/bold red]")
                return  # 退出程序
            elif command == "Promptfalse":
                console.print("[bold red]您的prompt文件为空，请您检查您的prompt.txt文件是否正确。[/bold red]")
                return  # 退出程序

            inp = "我的输入是”" + command + "“"
            explain = llm(inp, 'prompt_check.txt')

            if "no" not in explain:
                success = True
                break  # 成功，退出重试循环
            else:
                attempt += 1
                if attempt < max_attempts:
                    console.print(
                        f"[yellow]无法将您的要求转化为命令，正在尝试重新理解... (尝试 {attempt}/{max_attempts})[/yellow]")
                else:
                    console.print("[bold red]无法将您的要求转化为命令，请重新说明您想要进行的操作。[/bold red]")

        if not success:
            continue  # 返回到用户输入部分

        console.print(f"\n[bold green]生成的命令是: {command}[/bold green]")
        console.print(f"[bold yellow]命令解释: {explain}[/bold yellow]")

        # 添加一个内部循环，用于反复选择操作
        while True:
            # 使用 questionary 进行选择，并应用自定义样式
            console.print(f"\n[bold green]当前命令: {command}[/bold green]")
            action = questionary.select(
                "请选择操作:",
                choices=[
                    "编辑命令",
                    "执行命令",
                    "复制到剪切板",
                    "返回上一层",
                    "退出"
                ],
                style=custom_style
            ).ask()

            if action == "编辑命令":
                # 编辑命令，预填充当前命令
                edited_command = questionary.text(
                    "编辑命令:",
                    default=command
                ).ask().strip()
                if edited_command:
                    command = edited_command
                    console.print(f"[bold green]命令修改成功: {command}[/bold green]")
            elif action == "执行命令":
                # 执行命令前进行确认
                console.print(f"[bold red]Warning: [/bold red]")
                confirm = questionary.confirm(f"确认要执行命令: {command}?").ask()
                if confirm:
                    console.print(f"[bold green]执行命令: {command}[/bold green]")
                    f = execute_command(command)
                    if f == "executeFalse":
                        continue
                    break
                else:
                    console.print("[bold yellow]命令取消执行。[/bold yellow]")
            elif action == "复制到剪切板":
                try:
                    pyperclip.copy(command)
                    console.print(f"[bold green]命令已复制到剪切板: {command}[/bold green]")
                except pyperclip.PyperclipException as e:
                    console.print(f"[red]复制到剪切板时出错: {e}[/red]")
            elif action == "返回上一层":
                # 返回到消息输入层
                console.print("[bold blue]返回到消息输入。[/bold blue]")
                break
            elif action == "退出":
                console.print("[bold red]退出程序[/bold red]")
                return
            else:
                console.print("[bold red]无效的选择，请重新选择。[/bold red]")

    return

def chat():
    console.print("[bold blue]与 ERNIE 对话开始！输入 'exit' 退出。[/bold blue]")
    while True:
        message = questionary.text("你: ").ask()
        if message.lower() == 'exit':
            console.print("[bold red]退出程序[/bold red]")
            break
        result = llm(message, 'prompt_chat.txt')
        console.print(f"[bold green]{result}[/bold green]")

def main():
    parser = argparse.ArgumentParser(
        description="comhelper 命令行工具",
        usage="comhelper <command> [<args>]"
    )
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # work 子命令
    parser_work = subparsers.add_parser('work', help='执行 work 函数')
    # 在这里可以为 work 子命令添加特定的参数（如果有需要）

    # chat 子命令
    parser_chat = subparsers.add_parser('chat', help='执行 chat 函数')
    # 在这里可以为 chat 子命令添加特定的参数（如果有需要）

    # 解析参数
    args = parser.parse_args()

    if args.command == 'work':
        work()
    elif args.command == 'chat':
        chat()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
