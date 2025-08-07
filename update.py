import bpy
import os
import json
import zipfile
import shutil
import tempfile
import urllib.request
import importlib
import addon_utils

from .manifest import manifest
from .enums import UpdateChannel

GITHUB_REPO = "Ether0p12348/Blender_GridIt"

def get_latest_release(channel: UpdateChannel) -> dict | None:
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        with urllib.request.urlopen(api_url) as response:
            releases = json.loads(response.read().decode())
    except Exception as e:
        print(f"[{manifest.name}] Failed to fetch releases: {e}")
        return None

    for release in releases:
        tag = release['tag_name']
        is_prerelease = release['prerelease']
        is_dev = tag.endswith('-dev')
        is_beta = tag.endswith('-beta')
        is_stable = not is_prerelease and not is_beta and not is_dev

        if (
            channel == UpdateChannel.DEV and is_dev or
            channel == UpdateChannel.BETA and (is_beta or is_stable) or
            channel == UpdateChannel.STABLE and is_stable
        ):
            return {
                "tag": tag,
                "zip_url": release['zipball_url'],
            }

    return None

def download_and_install_update(tag: str, zip_url: str) -> bool:
    try:
        print(f"[{manifest.name}] Downloading update {tag} from {zip_url}")
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "update.zip")

        urllib.request.urlretrieve(zip_url, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if not extracted_dirs:
            raise Exception("Update archive is empty")

        addons_path = bpy.utils.user_resource("SCRIPTS", "addons")
        addon_name = manifest.id
        addon_path = os.path.join(addons_path, addon_name)

        if os.path.exists(addon_path):
            shutil.rmtree(addon_path)

        shutil.copytree(os.path.join(temp_dir, extracted_dirs[0]), addon_path) # addon_path may become a problem

        print(f"[{manifest.name}] Update installed. Reloading add-on...")
        bpy.app.timers.register(reload_addon, first_interval=1.0)
        return True

    except Exception as e:
        print(f"[{manifest.name}] Update Failed: {e}")
        return False

def check_for_updates(force: bool = False) -> float:
    print("[GridIt] check_for_updates function ENTERED")
    try:
        wm = bpy.context.window_manager
        channel_str = getattr(wm, "gridit_update_channel_sel", UpdateChannel.STABLE.value)
        auto_update = getattr(wm, "gridit_auto_update", True)
        channel = UpdateChannel(channel_str)
    except Exception as e:
        print(f"[{manifest.name}] Could not load preferences: {e}")
        return 3600.0

    print(f"[{manifest.name}] Checking for updates on '{channel}' channel...")
    current_version = manifest.version

    release = get_latest_release(channel)
    if release and release["tag"] != current_version:
        print(f"[{manifest.name}] New update available: {release['tag']}")
        if force or auto_update:
            download_and_install_update(release["tag"], release["zip_url"])

    else:
        print(f"[{manifest.name}] No updates available.")

    return 3600.0

def reload_addon():
    print("[GridIt] reload_addon function ENTERED")
    addon_name = manifest.id

    if addon_name in bpy.context.preferences.addons:
        module = bpy.context.preferences.addons[addon_name].module
        try:
            if hasattr(module, "unregister"):
                module.unregister()

            importlib.reload(module)

            if hasattr(module, "register"):
                module.register()

            print(f"[{manifest.name}] Reloaded add-on: {addon_name}")
        except Exception as e:
            print(f"[{manifest.name}] Error reloading add-on: {e}")
    else:
        print(f"[{manifest.name}] Add-on not found for reloading.")

def register():
    bpy.app.timers.register(lambda: check_for_updates(force=False), first_interval=10.0)

def unregister():
    pass