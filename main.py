import requests
import zipfile
import os
import io
import platform
from discord_webhook import DiscordWebhook

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
        'name': 'REPOSITORIES_NAME1',
        'branches_api': '',
        'raw_base': ' '
    },
    {
        'name': 'REPOSITORIES_NAME2',
        'branches_api': '',
        'raw_base': ' '
    }
]

WEBHOOK_FILE = "webhooks.txt"
ACCEPTED_EXTENSIONS = {'.manifest', '.lua', '.st'}

def get_webhook():
    if not os.path.exists(WEBHOOK_FILE):
        print(f"Error: Webhook file '{WEBHOOK_FILE}' not found.")
        exit(1)
    
    with open(WEBHOOK_FILE, 'r') as f:
        webhook_url = f.read().strip()
        
    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        print("Error: Invalid webhook URL in webhooks.txt")
        exit(1)
        
    return webhook_url

def send_to_discord(webhook_url, message=None, zip_data=None, filename=None):
    try:
        webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True, username="ICB Bot")
        if message:
            webhook.content = message
        if zip_data and filename:
            webhook.add_file(file=zip_data.getvalue(), filename=filename)
        return webhook.execute()
    except Exception as e:
        print(f"Error sending to Discord: {str(e)}")

def save_locally(zip_buffer, appid):
    os.makedirs('manifest', exist_ok=True)
    file_path = os.path.join('manifest', f'{appid}.zip')
    with open(file_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    print(f"File saved locally at: {file_path}")

def get_repo_files(repo, appid):
    try:
        branch_url = f"{repo['branches_api']}{appid}"
        if requests.get(branch_url, timeout=10).status_code != 200:
            return None
            
        owner, repo_name = repo['name'].split('/')
        contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/?ref={appid}"
        contents = requests.get(contents_url, timeout=10).json()
        
        files = []
        for item in contents:
            if item['type'] == 'file' and os.path.splitext(item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
                files.append({'name': item['name'], 'url': f"{repo['raw_base']}{appid}/{item['path']}"})
            elif item['type'] == 'dir':
                dir_contents = requests.get(item['url'], timeout=10).json()
                for file_item in dir_contents:
                    if file_item['type'] == 'file' and os.path.splitext(file_item['name'])[1].lower() in ACCEPTED_EXTENSIONS:
                        files.append({'name': file_item['name'], 'url': f"{repo['raw_base']}{appid}/{item['path']}/{file_item['name']}"})
        return files
    except Exception as e:
        print(f"Error checking ICB Database: {str(e)}")
        return None

def create_zip_with_files(appid, files):
    zip_buffer = io.BytesIO()
    added_files = set()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            if file['name'] not in added_files:
                try:
                    content = requests.get(file['url'], timeout=10).content
                    zipf.writestr(file['name'], content)
                    added_files.add(file['name'])
                except Exception as e:
                    print(f"Error downloading {file['name']}: {str(e)}")
        
        zipf.writestr("Made.txt", """Thanks For using ICB
For more manifest & lua files join ICB : https://discord.gg/Ch3PpUQAjf""")
    
    zip_buffer.seek(0)
    return zip_buffer

def process_appid():
    clear_console()
    show_banner()

    print("- Select an option:")
    print(" 1. Send the file to the webhook")
    print(" 2. Save the file locally (manifest folder)\n")
    choice = input("- Enter choice 1-2: ").strip()
    if choice not in ['1', '2']:
        print("Invalid choice")
        return True

    webhook_url = get_webhook() if choice == '1' else None

    appid = input("Enter the appid: ").strip().lower()
    if appid == 'exit':
        return False
    if not appid:
        print("Please enter a valid appid")
        return True

    clear_console()
    show_banner()
    print(f"Searching for appid: {appid}")
    print("Checking ICB Database...")
    
    all_files = []
    for repo in REPOSITORIES:
        if files := get_repo_files(repo, appid):
            all_files.extend(files)
            print(f"Found {len(files)} files in ICB Database...")

    if not all_files:
        if choice == '1':
            send_to_discord(webhook_url, f"{appid} not found in ICB Database. ❌")
        print(f"\n\033[1;91m{appid} not found in ICB Database")
        return True

    print(f"\nCreating zip file with {len(all_files)} files...")
    zip_buffer = create_zip_with_files(appid, all_files)

    if choice == '1':
        send_to_discord(
            webhook_url,
            f"**ICB Bot has found {len(all_files)} files for: {appid} . ✅**\n*`ICB BOT - github.com/ntjq/icb-manifest`*",
            zip_buffer,
            f"{appid}.zip"
        )
        print("\nFiles sent successfully!")
    else:
        save_locally(zip_buffer, appid)
        print("\nFiles saved locally!")
    return True

def main():
    while True:
        try:
            show_banner()
            if not process_appid():
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
