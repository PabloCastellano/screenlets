# pavpanchekha
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class KeyRing(object):
    def __init__(self):
        import keyring
        self.keyring = keyring
        if not self.keyring.is_available():
            raise KeyRingError
        keyring_list = self.keyring.list_keyring_names_sync()
        if len(keyring_list) == 0:
            raise KeyRingError
        self.ring = self.keyring.get_default_keyring_sync()

    def new(self, name=None, pwd=None, attrs={}, type="generic"):
        k = self.Key(self.keyring)
        if name and pwd:
            k.set(name, pwd, attrs, type)
        return k

    class Key(object):
        def __init__(self, keyring, token=0):
            self.keyring = keyring
            self.token = token

        def set(self, name, pwd, attrs={}, type="generic"):
            if type == "network":
                type = self.keyring.ITEM_NETWORK_PASSWORD
            elif type == "note":
                type = self.keyring.ITEM_NOTE
            else: # Generic included
                type = self.keyring.ITEM_GENERIC_SECRET

            self.token = self.keyring.item_create_sync(None, type, name, attrs, pwd, True)

        def get(self):
            return self.keyring.item_get_info_sync(None, self.token)

        def getAttrs(self):
            return keyring.item_get_attributes_sync(None, self.token)

        def setAttrs(self, a):
            return keyring.item_set_attributes_sync(None, self.token, a)

        def getName(self):
            return self.get().get_display_name()

        def setName(self, name):
            self.get().set_display_name(name)

        def getPass(self):
            return self.get().get_secret()

        def setPass(self, passwd):
            self.get().set_secret(passwd)

        def delete(self):
            self.keyring.item_delete_sync(None, self.token)

        attrs = property(getAttrs, setAttrs)
        name = property(getName, setName)
        password = property(getPass, setPass)
