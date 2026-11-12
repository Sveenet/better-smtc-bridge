# Versioning
APP_VERSION = "1.0.0"
UPSTREAM_VERSION = "1.0.1"
# Better SMTC Bridge additions by Sveenet. Original SMTC Bridge code by nutty.
# See LICENSE, LICENSE-MIT and docs/provenance.md for licensing boundaries.
DEVELOPER = "nutty"



###############
### IMPORTS ###
###############

import datetime
import traceback
import asyncio
import json
import base64
import threading
import os
import sys
import psutil
import tempfile
import atexit
import pystray
import webbrowser
import configparser
import time
import platform
import socket
import hashlib
from PIL import Image
from flask import Flask, jsonify
from flask_cors import CORS
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SMTC
from winrt.windows.storage.streams import DataReader
from plyer import notification
import winrt.runtime as winrt
import winrt.windows.foundation
import winrt.windows.foundation.collections
import winrt.windows.media
from artwork import ArtworkCache
from prefs import Preferences
import html
from collections import OrderedDict



# IMPORTANT SHIT STARTS HERE

def log_crash(e):
    # 1. Ensure the 'logs' folder exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 2. Create timestamped filename: yyyy-MM-dd hh-mm-ss
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = os.path.join(log_dir, f"crash_{timestamp}.txt")
    
    # 3. Write the error log
    with open(filename, "w", encoding="utf-8") as f:
        f.write("--- CRASH DETECTED ---\n")
        f.write(f"Time: {timestamp}\n")
        f.write(str(e) + "\n\n")
        f.write(traceback.format_exc())

    # 4. Keep only the 10 most recent logs
    # Get all .txt files in the log directory
    files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".txt")]
    
    # Sort by modification time (oldest first)
    files.sort(key=os.path.getmtime)
    
    # If we have more than 10, delete the oldest
    while len(files) > 10:
        oldest_file = files.pop(0)
        try:
            os.remove(oldest_file)
        except OSError:
            pass # Ignore errors if file is locked or already gone

try:
    #############################
    ### SINGLE INSTANCE CHECK ###
    #############################

    def is_already_running():
        import ctypes
        mutex_name = "Local\\BetterSMTCBridge"
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        
        # Store handle globally or in a way that prevents garbage collection
        is_already_running.h_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        
        # ERROR_ALREADY_EXISTS = 183
        if kernel32.GetLastError() == 183:
            if is_already_running.h_mutex:
                kernel32.CloseHandle(is_already_running.h_mutex)
            return True
        return False

    if __name__ == "__main__" and is_already_running():
        print("Another instance is already running. Exiting...")
        log_crash("Another instance is already running. Exiting...")
        sys.exit()



    ######################
    ### INITIALIZATION ###
    ######################

    def get_resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def load_settings():
        config = configparser.ConfigParser()
        config['SERVER'] = {'Host': '127.0.0.1', 'Port': '5000'}
        
        # Ensure settings.ini is looked for in the executable's directory
        exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        ini_path = os.path.join(exe_dir, 'settings.ini')
        
        if os.path.exists(ini_path):
            config.read(ini_path)
        return config

    settings = load_settings()
    HOST = "127.0.0.1"  # Better SMTC Bridge serves only this computer.
    PORT = 5000  # Shared metadata and audio port; unchanged from SMTC Bridge.

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    DISPLAY_HOST = get_local_ip() if HOST == "0.0.0.0" else HOST

    app = Flask(__name__)
    CORS(app)

    # Create a local temp directory for thumbnails
    THUMB_DIR = os.path.join(tempfile.gettempdir(), 'smtc_bridge_thumbs')
    # Legacy artwork route retained; modern artwork stays in memory only.



    ######################
    ### CORE FUNCTIONS ###
    ######################

    # Cache variables for the SMTC manager and rate limiting
    smtc_manager = None
    last_execution_time = 0.0
    last_payload = None
    
    # Thumbnail cache to avoid reprocessing the same artwork repeatedly
    MAX_CACHE_SIZE = 50               # Maximum number of unique thumbnails to cache
    thumb_cache = OrderedDict()
    track_artwork = ArtworkCache()

    async def get_all_media_info():            
        try:
            # We will cache the last execution time and payload to avoid redundant parsing if requests flood in faster than 0.5 seconds.
            current_time = time.time()
            global smtc_manager, last_execution_time, last_payload, thumb_cache

            # If requests flood in faster than 0.5 seconds, return the cached result 
            # to completely spare the CPU from redundant parsing.
            if (current_time - last_execution_time) < 0.5 and last_payload:
                # print("Using cached media info.")
                return last_payload
            # else:
            #     print("Fetching fresh media info.")
            
            last_execution_time = current_time

            # Instantiate the SMTC manager -> This allows use to "talk" to the Windows Media API
            # Reuse the manager if we already have it, otherwise request it once
            if not smtc_manager:
                print("Instantiating new SMTC manager...")
                smtc_manager = await SMTC.request_async()

            manager = smtc_manager
            
            # If it returns null, then no media is playing, or something fucked up and I have no
            # idea what to do, so just return an empty session list
            if not manager:
                return {"current_session_id": None, "sessions": []}

            # current_focused:  This is the session for the current media player -> Whatever Windows deems is "in focus"
            #                   will be the current session.
            # all_sessions:     We will also get all sessions, not just the current session.
            #                   This will provide the client with all the necessary info if they want to target just one application.
            # We will store the SourceAppUserModelId, which we all add to the final payload.
            # For all available properties/methods/events, see the official docs:
            # https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-28000
            
            # Try to pull sessions using the cached manager
            try:
                current_focused = manager.get_current_session()
                all_sessions = manager.get_sessions()
            except Exception:
                # If the COM context dropped or invalidated, reset it and retry once
                print("Instantiating new SMTC manager...")
                smtc_manager = await SMTC.request_async()
                manager = smtc_manager
                if not manager:
                    return {"current_session_id": None, "sessions": []}
                current_focused = manager.get_current_session()
                all_sessions = manager.get_sessions()

            current_session_id = current_focused.source_app_user_model_id if current_focused else None

            # We will store all the session info in a list of dictionaries, which we will return as JSON
            sessions_list = []

            # We will not iterate over all the sessions, and grab all the available info
            for session in all_sessions:
                # Get all the available info for each session object:
                # For all available properties/methods/events, see the official docs:
                # https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-28000
                app_id = session.source_app_user_model_id
                raw_playback = session.get_playback_info()
                raw_timeline = session.get_timeline_properties()
                raw_media = await session.try_get_media_properties_async()

                # Playback info
                # https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionplaybackinfo?view=winrt-28000
                playback_data = {
                    # AutoRepeatMode: Specifies the repeat mode of the session.
                    "AutoRepeatMode": raw_playback.auto_repeat_mode.value if (raw_playback and raw_playback.auto_repeat_mode) else 0,
                    
                    # IsShuffleActive: Specifies whether the session is currently playing content in a shuffled order.
                    "IsShuffleActive": raw_playback.is_shuffle_active if raw_playback else False,
                    
                    # PlaybackRate: The rate at which playback is happening (e.g., 1.0 is normal speed).
                    "PlaybackRate": raw_playback.playback_rate if raw_playback else 1.0,
                    
                    # PlaybackStatus: The current playback state of the session (e.g., Playing, Paused).
                    "PlaybackStatus": raw_playback.playback_status.value if (raw_playback and raw_playback.playback_status) else 0,
                    
                    # PlaybackType: Specifies what type of content the session has (e.g., Music, Video).
                    "PlaybackType": raw_playback.playback_type.value if (raw_playback and raw_playback.playback_type) else 0
                }

                # Timeline properties
                # https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessiontimelineproperties?view=winrt-28000
                timeline_data = {
                    # EndTime: The end timestamp of the current media item.
                    "EndTime": int(raw_timeline.end_time.total_seconds() * 1000) if raw_timeline.end_time else 0,
                    
                    # LastUpdatedTime: The UTC time at which the timeline properties were last updated.
                    "LastUpdatedTime": str(raw_timeline.last_updated_time) if raw_timeline.last_updated_time else None,
                    
                    # MaxSeekTime: The furthest timestamp at which the content can currently seek to.
                    "MaxSeekTime": int(raw_timeline.max_seek_time.total_seconds() * 1000) if raw_timeline.max_seek_time else 0,
                    
                    # MinSeekTime: The earliest timestamp at which the current media item can currently seek to.
                    "MinSeekTime": int(raw_timeline.min_seek_time.total_seconds() * 1000) if raw_timeline.min_seek_time else 0,
                    
                    # Position: The playback position, current as of LastUpdatedTime.
                    "Position": int(raw_timeline.position.total_seconds() * 1000) if raw_timeline.position else 0,
                    
                    # StartTime: The starting timestamp of the current media item.
                    "StartTime": int(raw_timeline.start_time.total_seconds() * 1000) if raw_timeline.start_time else 0,
                }

                # Media properties
                # https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmediaproperties?view=winrt-28000
                media_data = {
                    # Title: The title of the track.
                    "Title": raw_media.title if raw_media else "Unknown",
                    
                    # Artist: The name of the artist.
                    "Artist": raw_media.artist if raw_media else "Unknown",
                    
                    # AlbumTitle: The title of the album.
                    "AlbumTitle": raw_media.album_title if raw_media else "Unknown",
                    
                    # AlbumArtist: The artist associated with the album.
                    "AlbumArtist": raw_media.album_artist if raw_media else "Unknown",
                    
                    # TrackNumber: The track number within the album.
                    "TrackNumber": raw_media.track_number if raw_media else 0,
                    
                    # AlbumTrackCount: The total number of tracks on the album.
                    "AlbumTrackCount": raw_media.album_track_count if raw_media else 0,
                    
                    # Genres: The list of genres associated with the track.
                    "Genres": list(raw_media.genres) if raw_media else [],
                    
                    # Subtitle: Any subtitle information (common in podcasts/videos).
                    "Subtitle": raw_media.subtitle if raw_media else "",
                    
                    # Thumbnail: Our cached thumbnail representation.
                    "Thumbnail": None 
                }

                # Better SMTC Bridge: retain in-memory data URLs with a bounded,
                # expiring track cache; never log song names or write artwork files.
                thumb_url = await track_artwork.get(app_id, raw_media) if raw_media else None

                # Add the Base64 data string to the payload

                media_data["Thumbnail"] = thumb_url

                # Finally, assemble all the data into a session object, and add it to the session list
                sessions_list.append({
                    "source_app_id": app_id,
                    "playback_info": playback_data,
                    "timeline_properties": timeline_data,
                    "media_properties": media_data
                })
            
            # Build the final payload
            payload = {
                "app_version": APP_VERSION,
                "os": f"{platform.system()} {platform.release()}",
                "current_session_id": current_session_id, 
                "sessions": sessions_list
            }
            
            # Save to global payload cache
            last_payload = payload
            return payload

        except Exception as e:
            return {"current_session_id": None, "sessions": [], "error": str(e)}



    ########################
    ### STARTUP SHORTCUT ###
    ########################

    def get_startup_shortcut_path():
        # Gets the path to the current user's Startup folder
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        return os.path.join(startup_dir, 'BetterSMTCBridge.lnk')

    def is_start_with_windows():
        return os.path.exists(get_startup_shortcut_path())

    def set_start_with_windows(enable: bool):
        shortcut_path = get_startup_shortcut_path()
        
        if enable:
            # Determine the correct path (handles both raw script and PyInstaller .exe)
            if getattr(sys, 'frozen', False):
                target_path = sys.executable
                working_dir = os.path.dirname(sys.executable)
            else:
                target_path = sys.executable  # python.exe
                working_dir = os.path.dirname(os.path.abspath(__file__))
                # If running as script, you might want to point to the script instead, 
                # but usually this feature is intended for the built .exe
                
            # Use a quick PowerShell command to create a proper Windows .lnk shortcut
            # This avoids needing external libraries like winshell
            script_args = """
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($env:BETTER_BRIDGE_SHORTCUT)
            $Shortcut.TargetPath = $env:BETTER_BRIDGE_TARGET
            $Shortcut.WorkingDirectory = $env:BETTER_BRIDGE_WORKDIR
            $Shortcut.Arguments = $env:BETTER_BRIDGE_ARGUMENTS
            $Shortcut.Save()
            """
            import subprocess
            shortcut_environment = os.environ.copy()
            shortcut_environment.update({
                "BETTER_BRIDGE_SHORTCUT": shortcut_path,
                "BETTER_BRIDGE_TARGET": target_path,
                "BETTER_BRIDGE_WORKDIR": working_dir,
                "BETTER_BRIDGE_ARGUMENTS": "" if getattr(sys, 'frozen', False) else '"' + os.path.join(working_dir, 'bridge.py') + '"'
            })
            subprocess.run(["powershell", "-NoProfile", "-Command", script_args], env=shortcut_environment, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
        else:
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                except OSError:
                    pass
    
    def toggle_startup(icon, item):
        current_state = is_start_with_windows()
        set_start_with_windows(not current_state)


    #################
    ### ENDPOINTS ###
    #################

    @app.route('/artwork/<app_identifier>')
    def serve_artwork(app_identifier):
        from flask import send_from_directory
        # Serve the cached thumbnail directly from the temp directory
        return send_from_directory(THUMB_DIR, f"{app_identifier}.jpg")

    @app.route('/now-playing')
    def now_playing():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return jsonify(loop.run_until_complete(get_all_media_info()))
        finally:
            loop.close()

    @app.route('/sessions', methods=['GET'])
    def get_sessions():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch():
            manager = await SMTC.request_async()
            if not manager: return []
            return list(set([s.source_app_user_model_id for s in manager.get_sessions()]))
        
        try:
            sessions = loop.run_until_complete(fetch())
            
            # Wrapped in a <body> tag with a dark background and some padding
            html_list = """
            <body style='background-color: #121212; color: white; font-family: sans-serif; padding: 20px;'>
                <h3 style='margin-top: 0;'>Active Audio Sources:</h3>
                <ul>
            """
            
            if not sessions:
                html_list += "<li style='color: #888;'>No active audio sources found.</li>"
            else:
                for s in sessions:
                    html_list += f"<li style='margin-bottom: 8px; font-size: 1.1em;'>{html.escape(s)}</li>"
            
            html_list += "</ul></body>"
            return html_list
            
        except Exception as e:
            return f"<body style='background-color: #121212; color: #ff5555;'>Error: {str(e)}</body>"
        finally:
            loop.close()



    ###########################
    ### SYSTEM TRAY CONTROL ###
    ###########################

    # "Quit" menu item
    def on_quit(icon, item):
        icon.stop()
        if service_loop and service_bridge:
            service_loop.call_soon_threadsafe(service_bridge.stopped.set)

    # Setup the tray icon
    def setup_tray():
        global service_tray
        # Set the icon
        image = Image.open(get_resource_path("smtc-bridge.ico"))
        
        # Add the menu items
        menu = pystray.Menu(
            pystray.MenuItem(f"Better SMTC Bridge v{APP_VERSION}", None, enabled=False),
            pystray.MenuItem(f"Based on SMTC Bridge by {DEVELOPER}", None, enabled=False),
            pystray.MenuItem("Audio Controls", lambda: webbrowser.open(f"http://{DISPLAY_HOST}:{PORT}/"), default=True),
            pystray.Menu.SEPARATOR,            
            pystray.MenuItem("View Data (JSON)", lambda: webbrowser.open(f"http://{DISPLAY_HOST}:{PORT}/now-playing")),
            pystray.MenuItem("View Active Sessions", lambda: webbrowser.open(f"http://{DISPLAY_HOST}:{PORT}/sessions")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("★ Customize Overlay", lambda: webbrowser.open(f"https://creator-suite-amv.pages.dev/universal-music/settings/")),
            pystray.MenuItem("★ Try my stream widgets!", lambda: webbrowser.open(f"https://creator-suite-amv.pages.dev/")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start with Windows", 
                toggle_startup, 
                checked=lambda item: is_start_with_windows()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit)
        )
        
        # Put it all together
        icon = pystray.Icon("BetterSMTCBridge", image, "Better SMTC Bridge", menu=menu)
        service_tray = icon
        icon.run()



    #################
    ### KICK OFF! ###
    #################

    # Better SMTC Bridge serves original metadata and the new audio stream on one
    # loopback listener. The legacy Flask route functions above remain available.
    service_loop = None
    service_bridge = None
    service_ready = threading.Event()
    service_error = None
    service_tray = None
    PREFERENCES_PATH = None

    def stop_tray():
        if service_tray:
            service_tray.stop()

    def run_flask():
        from server import Bridge
        global service_loop, service_bridge, service_error
        async def run():
            global service_loop, service_bridge
            service_loop = asyncio.get_running_loop()
            service_bridge = Bridge(port=PORT, metadata_reader=get_all_media_info, on_stop=stop_tray, preferences=Preferences(PREFERENCES_PATH))
            task = asyncio.create_task(service_bridge.run())
            while not service_bridge.started and not task.done():
                await asyncio.sleep(.05)
            if service_bridge.started:
                service_ready.set()
            await task
        try:
            asyncio.run(run())
        except Exception as error:
            service_error = str(error)
            service_ready.set()
        finally:
            if service_tray:
                service_tray.stop()

    def main():
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        service_ready.wait()
        if service_error or not service_bridge or not service_bridge.started:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, service_error or "The local bridge could not start.", "Better SMTC Bridge", 0x10)
            return
        # Show setup only until the user has chosen an output. Later launches
        # restore the saved choice quietly; controls remain available in the tray.
        if not service_bridge.preferences.configured:
            webbrowser.open(f"http://{DISPLAY_HOST}:{PORT}/")
        setup_tray()
        if service_loop and service_loop.is_running():
            service_loop.call_soon_threadsafe(service_bridge.stopped.set)
        flask_thread.join(timeout=5)
        # Preserve upstream's final process exit after bounded, graceful cleanup.
        # Native COM or tray threads must not keep this app alive after Quit.
        os._exit(0)

    if __name__ == '__main__':
        main()

except Exception as e:
    log_crash(e)
    sys.exit(1)
