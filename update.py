import bpy
import urllib.request
import json
import zipfile
import os
import tempfile
import shutil
import importlib
import addon_utils

GITHUB_REPO = "Ether0p12348/Blender_GridIt"

def get_latest_release(channel: str):
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        with urllib.request.urlopen(api_url) as response:
            releases = json.loads(response.read().decode())
    except Exception as e:
        print(f"[GridIt] Failed to fetch releases: {e}")
        return None

    for release in releases:
        tag = release['tag_name']
        prerelease = release['prerelease']
        is_dev = tag.endswith('-dev')
        is_beta = tag.endswith('-beta')
        is_stable = not prerelease and not is_beta and not is_dev

        if (
            (channel == "dev" and is_dev) or
            (channel == "beta" and (is_beta or is_stable)) or
            (channel == "stable" and is_stable)
        ):
            return {
                "tag": tag,
                "zip_url": release['zipball_url'],
            }

    return None

def download_and_install_update(tag: str, zip_url: str):
    try:
        print(f"[GridIt] Downloading update {tag} from {zip_url}")
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "update.zip")

        urllib.request.urlretrieve(zip_url, zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if not extracted_dirs:
            raise Exception("Update archive is empty")

        addons_path = bpy.utils.user_resource('SCRIPTS', "addons")
        addon_name = "gridit"

        addon_path = os.path.join(addons_path, addon_name)
        if os.path.exists(addon_path):
            shutil.rmtree(addon_path)

        shutil.copytree(os.path.join(temp_dir, extracted_dirs[0]), addon_path)

        print(f"[GridIt] Update installed. Reloading addon...")

        bpy.app.timers.register(reload_addon, first_interval=1.0)
        return True

    except Exception as e:
        print(f"[GridIt] Update Failed: {e}")
        return False

def check_for_updates(force: bool = False):
    addon_name = "gridit"
    prefs = bpy.context.preferences.addons[addon_name].preferences
    channel = prefs.update_channel_sel
    print(f"[GridIt] Checking for updates on '{channel}' channel...")

    current_version = bpy.context.preferences.addons[addon_name].bl_info['version']
    current_version_str = ".".join(map(str, current_version))

    release = get_latest_release(channel)
    if release and release['tag'] != current_version_str:
        print(f"[GridIt] New update available: {release['tag']}")
        if force or bpy.context.preferences.addons[addon_name].preferences.auto_update:
            download_and_install_update(release['tag'], release['zip_url'])
    else:
        print("[GridIt] No updates available.")

    return 3600.0  # Check again in an hour

def reload_addon():
    addon_name = "gridit"

    if addon_name in bpy.context.preferences.addons:
        addon_module = bpy.context.preferences.addons[addon_name].module
        try:
            importlib.reload(addon_module)

            if hasattr(addon_module, "unregister"):
                addon_module.unregister()
            if hasattr(addon_module, "register"):
                addon_module.register()

            print(f"[GridIt] Reloaded add-on: {addon_name}")
        except Exception as e:
            print(f"[GridIt] Error reloading add-on: {e}")
    else:
        print("[GridIt] Add-on not found for reloading.")

def register():
    bpy.app.timers.register(check_for_updates, first_interval=5.0)

def unregister():
    pass