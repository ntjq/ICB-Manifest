# auth by ntjq and 0xRussi
# if you got any problem with that tool just open ticket in ICB discord server.
import requests
import zipfile
import os
import io
import platform
import itertools
import time
import sys
import threading
import tkinter as tk
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration constants
GITHUB_TOKENS = []
TOKEN_CYCLE = None
CONFIG_FILE = "config"
SESSION = requests.Session()
DOWNLOAD_TIMEOUT = 10
MAX_WORKERS = 8
REPO_CHECK_TIMEOUT = 8
PARALLEL_REPOS = 4

def create_gui():
    root = tk.Tk()
    root.title("ICB Manifest Downloader")  # Set window title
    root.geometry("400x300")
    
def create_gui():
    root = tk.Tk()
    root.title("ICB Manifest Downloader")  # Set window title
    root.geometry("400x300")
    
def main():
    load_github_tokens()
    save_folder = get_save_folder()
    create_gui()

class Spinner:
    """Animated spinner for activity indication"""
    def __init__(self):
        self.spinner_chars = '|/-\\'
        self.stop_running = False
        
    def spin(self):
        i = 0
        while not self.stop_running:
            sys.stdout.write(f"\rChecking... {self.spinner_chars[i]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % 4

def load_github_tokens():
    global GITHUB_TOKENS, TOKEN_CYCLE
    token_file = "github_tokens.txt"
    
    # Check if the token file exists
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            GITHUB_TOKENS = [line.strip() for line in f.readlines() if line.strip()]
    else:
        # Prompt user for tokens if file doesn't exist
        print("No github_tokens.txt file found. Please enter your GitHub tokens.")
        print("Enter each token on a new line. Press Enter twice to finish.")
        tokens = []
        while True:
            token = input("Enter GitHub token: ").strip()
            if not token and tokens:  # Stop if empty line and at least one token entered
                break
            if token:
                tokens.append(token)
            elif not tokens:  # Keep prompting if no tokens entered yet
                print("At least one token is required.")
        
        # Save tokens to github_tokens.txt
        try:
            with open(token_file, 'w') as f:
                for token in tokens:
                    f.write(token + '\n')
            GITHUB_TOKENS = tokens
            print(f"Saved {len(tokens)} tokens to {token_file}")
        except Exception as e:
            print(f"Error saving tokens to {token_file}: {str(e)}")
            GITHUB_TOKENS = []
    
    if GITHUB_TOKENS:
        TOKEN_CYCLE = itertools.cycle(GITHUB_TOKENS)
        print(f"Loaded {len(GITHUB_TOKENS)} GitHub tokens")
    else:
        print("Warning: No GitHub tokens found\ncreate (github_tokens.txt) so you can use the tool")

def make_github_request(url):
    global TOKEN_CYCLE

    for _ in range(len(GITHUB_TOKENS) * 2):
        current_token = next(TOKEN_CYCLE) if TOKEN_CYCLE else None
        headers = {'Authorization': f'token {current_token}'} if current_token else {}

        try:
            response = SESSION.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT)
            
            if response.status_code == 200:
                return response
                
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                sleep_time = max(reset_time - int(time.time()), 0) + 5
                
                print(f"Rate limited on {current_token[-4:] if current_token else 'no-token'}, "
                      f"retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue

        except Exception as e:
            print(f"Request error: {str(e)}")
            time.sleep(2)
            continue

    try:
        return SESSION.get(url, timeout=DOWNLOAD_TIMEOUT)
    except Exception as e:
        print(f"Final request failed: {str(e)}")
        return None

def clear_console():
    os.system('cls' if platform.system() == "Windows" else 'clear')
    
def set_terminal_title(title):
    # Works on Unix-like systems (Linux, macOS); less reliable on Windows
    print(f"\033]0;{title}\007", end="")
    
def show_banner():
    set_terminal_title("ICB Manifest Downloader")  # Set terminal title
    clear_console()
    print("\033[1;36m")
    print(r"""
 ██╗ ██████╗██████╗     ███╗   ███╗ █████╗ ███╗   ██╗██╗███████╗███████╗███████╗████████╗
 ██║██╔════╝██╔══██╗    ████╗ ████║██╔══██╗████╗  ██║██║██╔════╝██╔════╝██╔════╝╚══██╔══╝
 ██║██║     ██████╔╝    ██╔████╔██║███████║██╔██╗ ██║██║█████╗  █████╗  ███████╗   ██║   
 ██║██║     ██╔══██╗    ██║╚██╔╝██║██╔══██║██║╚██╗██║██║██╔══╝  ██╔══╝  ╚════██║   ██║   
 ██║╚██████╗██████╔╝    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║██║     ███████╗███████║   ██║   
 ╚═╝ ╚═════╝╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   
                                                                                        
 """)
    print("\033[37m- Author:\033[1;36m ntjq - 0xRussi \033[37m| Version:\033[1;36m 1.1 \033[37m| Discord:\033[1;36m https://discord.gg/Ch3PpUQAjf \033[37m")
    print("\033[37m  - latest version will be in my GitHub:\033[1;36m https://github.com/ntjq/ICB-Manifest")
    print("\033[1;91m     ( THIS PROJECT IS FULLY FREE IF YOU BOUGHT THIS TOOL YOU GOT SCAMMED )\033[0m\n")
    print("")

REPOSITORIES = [
    {
        'name': 'REPOSITORIES NAME1', # repositories name
        'branches_api': 'https://api.', # branches api
        'raw_base': 'https://raw.' # raw base
    },
    {
        'name': 'REPOSITORIES NAME2', # repositories name
        'branches_api': 'https://api.', # branches api
        'raw_base': 'https://raw.' # raw base
    }
]

ACCEPTED_EXTENSIONS = {'.manifest', '.lua', '.st'}

def get_save_folder():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return f.read().strip()
    
    while True:
        folder = input("Enter folder name to save downloaded appids: ").strip()
        if not folder:
            print("Folder name cannot be empty!")
            continue
            
        try:
            os.makedirs(folder, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                f.write(folder)
            return folder
        except Exception as e:
            print(f"Error creating folder: {str(e)}")

def download_file(file_info):
    try:
        return file_info['name'], SESSION.get(file_info['url'], timeout=DOWNLOAD_TIMEOUT).content
    except Exception as e:
        print(f"Error downloading {file_info['name']}: {str(e)}")
        return None

def create_zip_with_files(appid, files, save_folder):
    zip_buffer = io.BytesIO()
    added_files = set()
    total_files = len(files)
    downloaded = 0
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(download_file, file): file for file in files}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    name, content = result
                    if name not in added_files:
                        zipf.writestr(name, content)
                        added_files.add(name)
                        downloaded += 1
                        print(f"\033[0;32mDownloaded {downloaded}/{total_files} files\033[1;37m", end='\r')
        
        zipf.writestr("README.txt", """Thanks For using ICB
For more manifest & lua files join ICB : https://discord.gg/Ch3PpUQAjf""")
    
    zip_buffer.seek(0)
    print(f"\n\033[0;32mSuccessfully downloaded {downloaded}/{total_files} files")
    return zip_buffer

def search_appid(save_folder):
    clear_console()
    show_banner()
    
    appid = input("\033[1;37mEnter the appid: ").strip().lower()
    if appid == 'exit':
        return False

    if not appid.isdigit():
        print("Please enter a valid numeric appid")
        return True
    print("Checking ICB Database...\n")
    
    spinner = Spinner()
    spinner_thread = threading.Thread(target=spinner.spin)
    spinner_thread.start()
    
    all_files = []
    found_repos = 0
    start_time = time.time()
    
    try:
        with ThreadPoolExecutor(max_workers=PARALLEL_REPOS) as executor:
            future_to_repo = {
                executor.submit(get_repo_files, repo, appid): repo 
                for repo in REPOSITORIES
            }
            
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    files = future.result(timeout=REPO_CHECK_TIMEOUT)
                    if files:
                        all_files.extend(files)
                        found_repos += 1
                        print(f"\r\033[0;32mFound {len(files)} files\033[1;37m".ljust(50))
                except TimeoutError:
                    print(f"\rTimeout checking ICB Database".ljust(50))
                except Exception as e:
                    print(f"\rError checking ICB Database: {str(e)}".ljust(50))
    finally:
        spinner.stop_running = True
        spinner_thread.join()
        sys.stdout.write('\r' + ' '*50 + '\r')

    if not all_files:
        total_time = time.time() - start_time
        print(f"\n\033[1;91m{appid} not found in ICB Database (checked {len(REPOSITORIES)} repos in {total_time:.1f}s)\033[0m")
        return True

    zip_buffer = create_zip_with_files(appid, all_files, save_folder)
    
    save_locally(zip_buffer, appid, save_folder)
    return True

def save_locally(zip_buffer, appid, save_folder):
    file_path = os.path.join(save_folder, f'{appid}.zip')
    with open(file_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    print(f"\n\033[1;37mFiles saved in ({file_path})")

def get_repo_files(repo, appid):
    try:
        branch_url = f"{repo['branches_api']}{appid}"
        branch_response = make_github_request(branch_url)
        if branch_response.status_code != 200:
            return None
            
        owner, repo_name = repo['name'].split('/')
        contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/?ref={appid}"
        contents_response = make_github_request(contents_url)
        if contents_response.status_code != 200:
            return None
            
        contents = contents_response.json()
        files = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_content_item, item, repo, appid) for item in contents]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    files.extend(result)

        return files
    except Exception as e:
        print(f"Error checking ICB Database: {str(e)}")
        return None

def process_content_item(item, repo, appid):
    file_list = []
    try:
        if item['type'] == 'file' and os.path.splitext(item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
            file_list.append({
                'name': item['name'],
                'url': f"{repo['raw_base']}{appid}/{item['path']}"
            })
        elif item['type'] == 'dir':
            dir_response = make_github_request(item['url'])
            if dir_response.status_code == 200:
                dir_contents = dir_response.json()
                for file_item in dir_contents:
                    if file_item['type'] == 'file' and os.path.splitext(file_item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
                        file_list.append({
                            'name': file_item['name'],
                            'url': f"{repo['raw_base']}{appid}/{item['path']}/{file_item['name']}"
                        })
    except Exception as e:
        print(f"Error processing item: {str(e)}")
    return file_list

def main():
    load_github_tokens()
    save_folder = get_save_folder()
    
    while True:
        try:
            if not search_appid(save_folder):
                break
            input("\nPress Enter to search again...")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            input("Press Enter to restart...")

if __name__ == "__main__":
    main()
