import subprocess
import schedule
import time
import os
import sys
import configparser
import psutil
import winshell
from datetime import datetime


LOCK_FILE_PATH = 'wallpaper_lock.pid'
STOP_FILE_PATH = 'wallpaper_stop.flag'

config = configparser.ConfigParser()
config.read('config.ini')


def get_wallpapers_and_times():
    wallpapers = []
    periods = []
    for i in range(1, 5):
        wallpaper_key = f'wallpaper{i}'
        period_start_key = f'period{i}_start'
        period_end_key = f'period{i}_end'
        if (wallpaper_key in config['Wallpapers'] and 
                period_start_key in config['Times'] and 
                period_end_key in config['Times']):
            wallpapers.append(config['Wallpapers'][wallpaper_key])
            periods.append((int(config['Times'][period_start_key]), int(config['Times'][period_end_key])))
    return wallpapers, periods

wallpapers, periods = get_wallpapers_and_times()

WALLPAPER_ENGINE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\wallpaper64.exe"

def change_wallpaper(wallpaper_path):
    command = f'"{WALLPAPER_ENGINE_PATH}" -control openWallpaper -file "{wallpaper_path}"'
    try: 
        subprocess.run(command, shell=True)
    except Exception as e:
        print(f"Error changing wallpaper: {e}")

def update_wallpaper():
    now = datetime.now()
    hour = now.hour

    for i, (start, end) in enumerate(periods):
        if start < end:
            if start <= hour < end:
                change_wallpaper(wallpapers[i])
                break
        else: 
            if start <= hour or hour < end:
                change_wallpaper(wallpapers[i])
                break



def add_to_startup():
    startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    exe_path = sys.argv[0]
    shortcut_path = os.path.join(startup_folder, os.path.basename(exe_path) + '.lnk')

    if not os.path.exists(shortcut_path):
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = exe_path
            shortcut.working_directory = os.path.dirname(exe_path)
            shortcut.description = "Wallpaper Script"

def handle_existing_process():
    if os.path.exists(LOCK_FILE_PATH):
        with open(LOCK_FILE_PATH, 'r') as lock_file:
            old_pid = int(lock_file.read().strip())
            if psutil.pid_exists(old_pid):
                old_process = psutil.Process(old_pid)
                old_process.terminate()
                old_process.wait()
                print(f"Stopped process with PID {old_pid}")
    
    with open(LOCK_FILE_PATH, 'w') as lock_file:
        lock_file.write(str(os.getpid()))

def check_for_stop_file():
    return os.path.exists(STOP_FILE_PATH)


if __name__ == '__main__':
    handle_existing_process()
    add_to_startup()
    update_wallpaper()


schedule.every().hour.at(":00").do(update_wallpaper)


while True:
    if check_for_stop_file():
            os.remove(LOCK_FILE_PATH)
            print("Stop file detected. Exiting.")
            break
    schedule.run_pending()
    time.sleep(1)
