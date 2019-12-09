"""Operator used to update the Embark Addon."""


from distutils.version import StrictVersion
import json
from os import environ, listdir, path
from re import search
from shutil import copyfile
from socket import timeout
from tempfile import TemporaryDirectory
from urllib.error import ContentTooShortError, HTTPError, URLError
import urllib.request
import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty
from ..utils import get_current_version, get_preferences, reload_addon


BLENDER_TOOLS_UPDATE_PATH = "BLENDER_TOOLS_UPDATE_PATH"
VERSION = "version"
DOWNLOAD_URL = "download_url"


class CheckForUpdates(bpy.types.Operator):
    """Checks for available updates to the latest version, and prompts the user with the results."""

    bl_idname = "screen.embark_check_for_updates"
    bl_label = "Check for Updates..."
    bl_description = 'Updates the Embark Addon'
    bl_options = {'BLOCKING'}

    _repo = "https://api.github.com/repos/EmbarkStudios/blender-tools"
    _releases = "/releases"
    _timeout = 5            # HTTP timeout in seconds
    _silent = True          # Running silently, used for auto-update on startup
    _latest_release = None  # Cached latest release returned from HTTP request
    _stage = 0              # Stage of the dialog, used to change UI state
    _error_message = None   # Error message to display in the UI, if any

    install_update: BoolProperty(name="Install update")

    # FIXME: This seems broken in Blender 2.80?
    def check(self, context):  # pylint: disable=no-self-use
        """Always redraw the UI."""
        return True

    def draw(self, context):
        """Draw the check for updates popup."""
        row = self.layout.row()
        row.prop(self, "install_update")
        row.enabled = self._latest_is_newer()

        # Don't immediately check for updates, so we get the dialog on screen instead of waiting
        if self._stage == 0:
            self.layout.label(text="Please wait, checking for updates...")
            self._stage = 1
            return

        if self._stage == 1:
            current_version = get_current_version()
            if self._check_for_updates():
                if self._error_message:
                    self.layout.label(text=self._error_message)
                else:
                    new_version = self._latest_release[VERSION]
                    self.layout.label(text=f"Version {new_version} is available (currently on {current_version})")
            else:
                if self._error_message:
                    self.layout.label(text=self._error_message)
                else:
                    self.layout.label(text=f"You already have the latest version ({current_version})")

    def invoke(self, context, event):
        """Open the popup when the operator is invoked."""
        self._silent = False
        self.install_update = False
        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context):
        """Either cancel, or download & install the update if requested."""
        # If running in silent mode, just do the check first:
        if self._silent:
            if self._check_for_updates():
                return bpy.ops.screen.embark_check_for_updates('INVOKE_DEFAULT')
            return {'FINISHED'}

        if not self.install_update:
            return {'FINISHED'}

        with TemporaryDirectory() as temp_dir:
            download_url = self._latest_release[DOWNLOAD_URL]
            file_name = path.basename(download_url)
            temp_file = path.normpath(path.join(temp_dir, file_name))
            self._info(f"Beginning download: {file_name}...")
            try:
                if download_url.startswith("\\\\"):
                    copyfile(download_url, temp_file)
                else:
                    urllib.request.urlretrieve(download_url, temp_file)
                self._info(f"Downloaded file: {file_name}")
                bpy.ops.preferences.addon_install(
                    overwrite=True,
                    filepath=temp_file,
                    filter_folder=True,
                    filter_python=True,
                    filter_glob="*.py;*.zip"
                )
                reload_addon()
                self._info(f"Embark Addon updated to version {self._latest_release[VERSION]}! Please restart Blender.")
            except (URLError, HTTPError, ContentTooShortError) as err:
                self._warn(f"Failed to download: {err.reason}")
                return {'CANCELLED'}
        return {'FINISHED'}

    def _check_for_updates(self):
        """Check online for updated releases of the addon."""
        if self._latest_release is not None:  # This will not be None if we already checked, so just return
            return self._latest_is_newer()

        self._error_message = None

        if BLENDER_TOOLS_UPDATE_PATH in environ:
            self._latest_release = self._get_latest_internal_release()
        else:
            self._latest_release = self._get_latest_public_release()
        if not self._latest_release:
            return False

        current_version = get_current_version()
        if not self._latest_is_newer():
            self._info(f"Embark Addon is already up-to-date ({current_version})")
            return False

        self.install_update = True
        remote_version = self._latest_release[VERSION]
        self._info(f"Update available (current version: {current_version}, new version: {remote_version})")
        return True

    def _get_latest_public_release(self):
        """Checks Github repository for new Releases, and returns the latest one as a tuple, or None if not found."""
        try:
            url = f"{self._repo}{self._releases}"
            with urllib.request.urlopen(url, timeout=self._timeout) as response:
                json_response = json.loads(response.read())
                if not self._is_valid_response(json_response):
                    self._warn("Invalid response data!")
                    return None
                version = json_response[0].get("tag_name", None)
                if not version:
                    self._warn("First release had no valid tag name!")
                    return None
                download_url = self._get_download_url(json_response[0])
                if not download_url:
                    self._warn("No valid release found for download!")
                    return None
                return {VERSION: version, DOWNLOAD_URL: download_url}
        except (URLError, HTTPError) as err:
            self._error_message = f"Failed update query: Error {err.code}: {err.reason}: {url}"
        except timeout as err:
            self._error_message = "Update query timed out!"
        except:  # pylint: disable=bare-except
            self._error_message = "Something went wrong with the update!"
        self._warn(self._error_message)
        return None

    def _get_latest_internal_release(self):
        """Checks a network folder for newer releases, returning a newer version as a tuple, otherwise None."""
        if not environ[BLENDER_TOOLS_UPDATE_PATH]:
            self._warn(f"No value defined for environment variable '{BLENDER_TOOLS_UPDATE_PATH}'!")
            return None

        release_folder = environ[BLENDER_TOOLS_UPDATE_PATH]
        if not path.exists(release_folder):
            self._warn(f"Failed to open internal release folder: {release_folder}")
            return None

        releases = listdir(release_folder)
        version = get_current_version()
        download_url = None
        for release in releases:
            exp = r"([0-9]+\.[0-9]+\.[0-9]+)"
            semver_match = search(exp, release)  # File names must contain the version number in the format X.X.X
            if release.endswith(".zip") and semver_match:
                this_version = semver_match.group(0)
                if StrictVersion(this_version) > StrictVersion(version):
                    version = this_version
                    download_url = path.join(release_folder, release)

        return {VERSION: version, DOWNLOAD_URL: download_url}

    def _latest_is_newer(self):
        """Returns True if version is newer than the current version, other False."""
        if self._latest_release:
            return StrictVersion(self._latest_release[VERSION]) > StrictVersion(get_current_version())
        return False

    def _info(self, message):
        self.report({'INFO'}, f"Embark Addon Updater: {message}")

    def _warn(self, message):
        self.report({'WARNING'}, f"Embark Addon Updater: {message}")

    @staticmethod
    def _is_valid_response(response):
        if not response or not isinstance(response, list):
            return False
        release = response[0]
        if release.get("prerelease", False) or release.get("draft", False):
            return False
        return True

    @staticmethod
    def _get_download_url(release):
        assets = release.get("assets", None)
        if not assets or not isinstance(assets, list):
            return None
        for asset in assets:
            if asset.get("content_type", None) == "application/zip":
                return asset.get("browser_download_url", None)
        return None


@persistent
def _auto_update_handler(context):
    """Check for updates on first scene load."""
    bpy.ops.screen.embark_check_for_updates()
    bpy.app.handlers.load_post.remove(_auto_update_handler)  # Job done, so remove itself


def menu_draw(self, context):
    """Draw the menu item for Update."""
    self.layout.operator(CheckForUpdates.bl_idname, icon="FILE_REFRESH")


__classes__ = (
    CheckForUpdates,
)


def register():
    """Register the operator classes and hook up the auto-update check."""
    for cls in __classes__:
        bpy.utils.register_class(cls)

    # Add a scene load handler for the first time auto-update check, if needed
    if get_preferences().auto_update is True:
        bpy.app.handlers.load_post.append(_auto_update_handler)


def unregister():
    """Unregister the operator classes."""
    for cls in reversed(__classes__):
        bpy.utils.unregister_class(cls)
