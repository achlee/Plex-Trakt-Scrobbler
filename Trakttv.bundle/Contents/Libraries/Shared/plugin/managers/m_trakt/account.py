from plugin.managers.core.base import Manager, Update
from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager
from plugin.models import TraktAccount, TraktOAuthCredential

from trakt import Trakt
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    def from_pin(self, account, pin):
        if not pin:
            log.debug('"pin" parameter is empty, ignoring account authorization update')
            return account

        # Retrieve current account `OAuthCredential`
        oauth = account.oauth_credentials.first()

        if oauth and oauth.code == pin:
            log.debug("PIN hasn't changed, ignoring account authorization update")
            return account

        if not oauth:
            # Create new `OAuthCredential` for the account
            oauth = TraktOAuthCredential(
                account=account
            )

        # Update `OAuthCredential`
        if not TraktOAuthCredentialManager.update.from_pin(oauth, pin, save=False):
            log.warn("Unable to update OAuthCredential (token exchange failed, hasn't changed, etc..)")
            return None

        # Validate the account authorization
        with account.oauth_authorization(oauth):
            settings = Trakt['users/settings'].get()

        if not settings:
            log.warn('Unable to retrieve account details for authorization')
            return None

        username = settings.get('user', {}).get('username')

        if not username:
            log.warn('Unable to retrieve username for authorization')
            return None

        self(account, {'username': username}, save=False)

        # Save `OAuthCredential` and `Account`
        oauth.save()
        account.save()

        log.info('Updated account authorization for %r', account)
        return account


class TraktAccountManager(Manager):
    update = UpdateAccount

    model = TraktAccount
