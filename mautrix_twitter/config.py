# mautrix-twitter - A Matrix-Twitter DM puppeting bridge
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Any, Dict, List, NamedTuple
from ruamel.yaml.comments import CommentedMap
import os

from mautrix.types import UserID
from mautrix.client import Client
from mautrix.bridge.config import (BaseBridgeConfig, ConfigUpdateHelper, ForbiddenKey,
                                   ForbiddenDefault)

Permissions = NamedTuple("Permissions", relaybot=bool, user=bool, puppeting=bool,
                         matrix_puppeting=bool, admin=bool, level=str)


class Config(BaseBridgeConfig):
    def __getitem__(self, key: str) -> Any:
        try:
            return os.environ[f"MAUTRIX_TWITTER_{key.replace('.', '_').upper()}"]
        except KeyError:
            return super().__getitem__(key)

    @property
    def forbidden_defaults(self) -> List[ForbiddenDefault]:
        return [
            *super().forbidden_defaults,
            ForbiddenDefault("bridge.permissions", ForbiddenKey("example.com")),
        ]

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        super().do_update(helper)
        copy, copy_dict, base = helper

        copy("appservice.provisioning.enabled")
        copy("appservice.provisioning.prefix")
        copy("appservice.provisioning.shared_secret")
        if base["appservice.provisioning.shared_secret"] == "generate":
            base["appservice.provisioning.shared_secret"] = self._new_token()

        copy("appservice.community_id")

        copy("bridge.username_template")
        copy("bridge.displayname_template")

        copy("bridge.displayname_max_length")

        copy("bridge.sync_conversation_limit")
        copy("bridge.sync_with_custom_puppets")
        copy("bridge.login_shared_secret")
        copy("bridge.federate_rooms")
        copy("bridge.encryption.allow")
        copy("bridge.encryption.default")
        copy("bridge.private_chat_portal_meta")
        copy("bridge.delivery_receipts")
        copy("bridge.delivery_error_reports")
        copy("bridge.resend_bridge_info")

        copy("bridge.command_prefix")

        copy_dict("bridge.permissions")

        if "bridge.relaybot" not in self:
            copy("bridge.authless_relaybot_portals", "bridge.relaybot.authless_portals")
        else:
            copy("bridge.relaybot.private_chat.invite")
            copy("bridge.relaybot.private_chat.state_changes")
            copy("bridge.relaybot.private_chat.message")
            copy("bridge.relaybot.group_chat_invite")
            copy("bridge.relaybot.ignore_unbridged_group_chat")
            copy("bridge.relaybot.authless_portals")
            copy("bridge.relaybot.whitelist_group_admins")
            copy("bridge.relaybot.whitelist")
            copy("bridge.relaybot.ignore_own_incoming_events")

    def _get_permissions(self, key: str) -> Permissions:
        level = self["bridge.permissions"].get(key, "")
        admin = level == "admin"
        matrix_puppeting = level == "full" or admin
        puppeting = level == "puppeting" or matrix_puppeting
        user = level == "user" or puppeting
        relaybot = level == "relaybot" or user
        return Permissions(relaybot, user, puppeting, matrix_puppeting, admin, level)

    def get_permissions(self, mxid: UserID) -> Permissions:
        permissions = self["bridge.permissions"]
        if mxid in permissions:
            return self._get_permissions(mxid)

        _, homeserver = Client.parse_user_id(mxid)
        if homeserver in permissions:
            return self._get_permissions(homeserver)

        return self._get_permissions("*")
