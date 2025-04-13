import requests
import zipfile
import os
import io
import platform
import itertools
import time
from concurrent.futures import ThreadPoolExecutor

# GitHub API Configuration
GITHUB_TOKENS = []  # List of personal access tokens for rate limit bypass, Recommended 5-10 tokens for heavy usage
TOKEN_CYCLE = None  # Iterator for cycling through tokens
CONFIG_FILE = "config"  # File storing download directory preference
SESSION = requests.Session()  # Persistent HTTP session
DOWNLOAD_TIMEOUT = 15  # Seconds before timing out a download
MAX_WORKERS = 8  # Parallel download threads

def load_github_tokens():
    global GITHUB_TOKENS, TOKEN_CYCLE
    token_file = "github_tokens.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            GITHUB_TOKENS = [line.strip() for line in f.readlines() if line.strip()]
    if GITHUB_TOKENS:
        TOKEN_CYCLE = itertools.cycle(GITHUB_TOKENS)
        print(f"Loaded {len(GITHUB_TOKENS)} GitHub tokens")
    else:
        print("Warning: No GitHub tokens found - using unauthenticated requests")

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

def show_banner():
    print("\033[1;36m")
    print(r"""
 ██╗ ██████╗██████╗     ███╗   ███╗ █████╗ ███╗   ██╗██╗███████╗███████╗███████╗████████╗
 ██║██╔════╝██╔══██╗    ████╗ ████║██╔══██╗████╗  ██║██║██╔════╝██╔════╝██╔════╝╚══██╔══╝
 ██║██║     ██████╔╝    ██╔████╔██║███████║██╔██╗ ██║██║█████╗  █████╗  ███████╗   ██║   
 ██║██║     ██╔══██╗    ██║╚██╔╝██║██╔══██║██║╚██╗██║██║██╔══╝  ██╔══╝  ╚════██║   ██║   
 ██║╚██████╗██████╔╝    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║██║     ███████╗███████║   ██║   
 ╚═╝ ╚═════╝╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   
                                                                                        
 """)
    print("\033[37m- Author:\033[1;36m ntjq - 0xRussi \033[37m| Version:\033[1;36m 1.0 \033[37m| Discord:\033[1;36m https://discord.gg/Ch3PpUQAjf \033[37m")
    print("\033[37m- latest version will in my GitHub:\033[1;36m https://github.com/ntjq/ICB-Manifest")
    print("\033[1;91m- ( This Project is fully Free If you bought this tool you got scammed )\033[0m\n")
    print("")

REPOSITORIES = [
    {
        'name': 'SteamAutoCracks/ManifestHub',
        'branches_api': 'https://api.github.com/repos/SteamAutoCracks/ManifestHub/branches/',
        'raw_base': 'https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/'
    },
    {
        'name': 'ikun0014/ManifestHub',
        'branches_api': 'https://api.github.com/repos/ikun0014/ManifestHub/branches/',
        'raw_base': 'https://raw.githubusercontent.com/ikun0014/ManifestHub/'
    },
    {
        'name': 'Auiowu/ManifestAutoUpdate',
        'branches_api': 'https://api.github.com/repos/Auiowu/ManifestAutoUpdate/branches/',
        'raw_base': 'https://raw.githubusercontent.com/Auiowu/ManifestAutoUpdate/'
    },
    {
        'name': 'tymolu233/ManifestAutoUpdate',
        'branches_api': 'https://api.github.com/repos/tymolu233/ManifestAutoUpdate/branches/',
        'raw_base': 'https://raw.githubusercontent.com/tymolu233/ManifestAutoUpdate/'
    },
    {
        'name': 'hulovewang/ManifestAutoUpdate',
        'branches_api': 'https://api.github.com/repos/hulovewang/ManifestAutoUpdate/branches/',
        'raw_base': 'https://raw.githubusercontent.com/hulovewang/ManifestAutoUpdate/'
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
            futures = [executor.submit(download_file, file) for file in files]
            
            for future in futures:
                result = future.result()
                if result:
                    name, content = result
                    if name not in added_files:
                        zipf.writestr(name, content)
                        added_files.add(name)
                        downloaded += 1
                        print(f"Downloaded {downloaded}/{total_files} files", end='\r')
        
        zipf.writestr("README.txt", """Thanks For using ICB
For more manifest & lua files join ICB : https://discord.gg/Ch3PpUQAjf""") # Read me File - README.txt 
    
    zip_buffer.seek(0)
    print(f"\nSuccessfully downloaded {downloaded}/{total_files} files")
    return zip_buffer

def search_appid(save_folder):
    clear_console()
    show_banner()
    
    appid = input("Enter the appid: ").strip().lower()
    if appid == 'exit':
        return False

    if not appid:
        print("Please enter a valid appid")
        return True

    print(f"\nSearching for appid: {appid}")
    print("Checking ICB Database...")
    
    all_files = []
    for repo in REPOSITORIES:
        if files := get_repo_files(repo, appid):
            all_files.extend(files)
            print(f"Found {len(files)} files in {repo['name']}")

    if not all_files:
        print(f"\n\033[1;91m{appid} not found in ICB Database")
        return True

    print(f"\nCreating zip file with {len(all_files)} files...")
    zip_buffer = create_zip_with_files(appid, all_files, save_folder)
    
    save_locally(zip_buffer, appid, save_folder)
    return True

def save_locally(zip_buffer, appid, save_folder):
    file_path = os.path.join(save_folder, f'{appid}.zip')
    with open(file_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    print(f"\nFiles saved to: {os.path.abspath(file_path)}")

def get_repo_files(repo, appid):
    try:
        if 'fallback' in repo['name']:
            return [{
                'name': 'package.manifest',
                'url': f"{repo['raw_base']}{repo['name'].split('/')[0]}/{repo['name'].split('/')[1]}/{appid}/package.manifest"
            }]
            
        branch_url = f"{repo['branches_api']}{appid}"
        response = make_github_request(branch_url)
        if response.status_code != 200:
            return None
            
        owner, repo_name = repo['name'].split('/')
        contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/?ref={appid}"
        response = make_github_request(contents_url)
        if response.status_code != 200:
            return None
            
        contents = response.json()
        files = []
        
        for item in contents:
            if item['type'] == 'file' and os.path.splitext(item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
                files.append({'name': item['name'], 'url': f"{repo['raw_base']}{appid}/{item['path']}"})
            elif item['type'] == 'dir':
                dir_response = make_github_request(item['url'])
                if dir_response.status_code == 200:
                    dir_contents = dir_response.json()
                    for file_item in dir_contents:
                        if file_item['type'] == 'file' and os.path.splitext(file_item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
                            files.append({'name': file_item['name'], 'url': f"{repo['raw_base']}{appid}/{item['path']}/{file_item['name']}"})
        return files
    except Exception as e:
        print(f"Error checking ICB Database: {str(e)}")
        return None

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
