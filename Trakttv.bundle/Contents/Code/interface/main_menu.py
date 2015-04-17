from core.cache import CacheManager
from core.helpers import pad_title, get_pref
from core.plugin import ART, NAME, ICON
from interface.sync_menu import AccountsMenu, ControlsMenu

from plugin.core.constants import PLUGIN_PREFIX, PLUGIN_VERSION
from plugin.managers import AccountManager


@handler(PLUGIN_PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    if not get_pref('valid'):
        oc.add(DirectoryObject(
            key=PLUGIN_PREFIX,
            title=L("Error: Authentication failed"),
        ))

    num_accounts = AccountManager.get.all().count()

    if num_accounts > 1:
        Log.Debug('AccountsMenu')
        oc.add(PopupDirectoryObject(
            key=Callback(AccountsMenu),
            title=L("Sync"),
            summary=L("Sync the Plex library with trakt.tv")
        ))
    else:
        oc.add(DirectoryObject(
            key=Callback(ControlsMenu),
            title=L("Sync"),
            summary=L("Sync the Plex library with trakt.tv")
        ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=L("About")
    ))

    oc.add(PrefsObject(
        title="Preferences",
        summary="Configure how to connect to Trakt.tv",
        thumb=R("icon-preferences.png")
    ))

    return oc


@route(PLUGIN_PREFIX + '/about')
def AboutMenu():
    oc = ObjectContainer(title2="About")

    oc.add(DirectoryObject(
        key=Callback(CacheStatisticsMenu),
        title=pad_title("Cache Statistics")
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title("Version: %s" % PLUGIN_VERSION)
    ))

    return oc


@route(PLUGIN_PREFIX + '/about/cache')
def CacheStatisticsMenu():
    oc = ObjectContainer(title2="Cache Statistics")

    for item in CacheManager.statistics():
        oc.add(DirectoryObject(
            key='',
            title=pad_title("[%s] Cache Size: %s, Store Size: %s" % item)
        ))

    return oc
