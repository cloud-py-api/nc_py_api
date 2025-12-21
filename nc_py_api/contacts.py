"""Nextcloud API for working with Contacts."""

import dataclasses
import datetime
import re
from typing import Any

from ._misc import check_capabilities, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class AddressBook:
    """Class representing one address book."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def addressbook_id(self) -> int:
        """Unique identifier of the address book."""
        return self._raw_data["id"]

    @property
    def name(self) -> str:
        """Name of the address book."""
        return self._raw_data["name"]

    @property
    def display_name(self) -> str:
        """Display name of the address book."""
        return self._raw_data.get("displayname", self.name)

    @property
    def uri(self) -> str:
        """URI of the address book."""
        return self._raw_data["uri"]

    @property
    def description(self) -> str:
        """Description of the address book."""
        return self._raw_data.get("description", "")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.addressbook_id}, name={self.name}>"


@dataclasses.dataclass
class Contact:
    """Class representing one contact."""

    def __init__(self, raw_data: dict | str):
        if isinstance(raw_data, str):
            self._vcard_data = raw_data
            self._parsed_data = self._parse_vcard(raw_data)
        else:
            self._vcard_data = raw_data.get("vcard", "")
            self._parsed_data = raw_data

    def _parse_vcard(self, vcard: str) -> dict:
        """Parse vCard data into a dictionary."""
        parsed: dict[str, Any] = {}
        lines = vcard.split("\n")
        current_key = None
        current_value = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("BEGIN:VCARD") or line.startswith("END:VCARD"):
                continue
            if ":" in line:
                if current_key:
                    parsed[current_key] = "".join(current_value)
                    current_value = []
                parts = line.split(":", 1)
                current_key = parts[0].split(";")[0].replace("item", "").lower()
                if len(parts) > 1:
                    current_value.append(parts[1])
            elif current_key:
                current_value.append(line)

        if current_key:
            parsed[current_key] = "".join(current_value)

        return parsed

    @property
    def contact_id(self) -> str:
        """Unique identifier of the contact."""
        return self._parsed_data.get("uid", "")

    @property
    def full_name(self) -> str:
        """Full name of the contact."""
        fn = self._parsed_data.get("fn", "")
        if not fn:
            n = self._parsed_data.get("n", "").split(";")
            fn = " ".join([n for n in n if n]).strip()
        return fn or ""

    @property
    def first_name(self) -> str:
        """First name of the contact."""
        n = self._parsed_data.get("n", "").split(";")
        return n[1] if len(n) > 1 else ""

    @property
    def last_name(self) -> str:
        """Last name of the contact."""
        n = self._parsed_data.get("n", "").split(";")
        return n[0] if len(n) > 0 else ""

    @property
    def emails(self) -> list[str]:
        """List of email addresses."""
        emails = []
        for key, value in self._parsed_data.items():
            if "email" in key.lower() and value:
                emails.append(value)
        if not emails and "email" in self._parsed_data:
            emails.append(self._parsed_data["email"])
        return emails

    @property
    def phones(self) -> list[str]:
        """List of phone numbers."""
        phones = []
        for key, value in self._parsed_data.items():
            if "tel" in key.lower() and value:
                phones.append(value)
        if not phones and "tel" in self._parsed_data:
            phones.append(self._parsed_data["tel"])
        return phones

    @property
    def organization(self) -> str:
        """Organization of the contact."""
        return self._parsed_data.get("org", "")

    @property
    def vcard(self) -> str:
        """Raw vCard data."""
        return self._vcard_data

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.contact_id}, name={self.full_name}>"


class _ContactsAPI:
    """Class providing the Contacts API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/dav/api/v1/addressbooks"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("dav", self._session.capabilities)

    def get_addressbooks(self) -> list[AddressBook]:
        """Returns a list of all address books for the current user."""
        require_capabilities("dav", self._session.capabilities)
        user = self._session.user
        if not user:
            raise ValueError("User not available in session.")
        result = self._session.ocs("GET", f"{self._ep_base}/{user}")
        return [AddressBook(i) for i in result]

    def get_contacts(self, addressbook_id: int | str | AddressBook) -> list[Contact]:
        """Returns all contacts in an address book.

        :param addressbook_id: ID, URI, or AddressBook object of the address book.
        """
        require_capabilities("dav", self._session.capabilities)
        user = self._session.user
        if not user:
            raise ValueError("User not available in session.")

        if isinstance(addressbook_id, AddressBook):
            addressbook_uri = addressbook_id.uri
        elif isinstance(addressbook_id, str):
            addressbook_uri = addressbook_id
        else:
            addressbooks = self.get_addressbooks()
            matching = [ab for ab in addressbooks if ab.addressbook_id == addressbook_id]
            if not matching:
                raise ValueError(f"Address book with ID {addressbook_id} not found.")
            addressbook_uri = matching[0].uri

        dav_path = f"/remote.php/dav/addressbooks/users/{user}/{addressbook_uri}/"
        response = self._session.adapter_dav.request("PROPFIND", dav_path, headers={"Depth": "1"})
        contacts = []
        if response.status_code == 207:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
            for response_elem in root.findall(".//{DAV:}response"):
                href_elem = response_elem.find("{DAV:}href")
                if href_elem is not None and href_elem.text and href_elem.text.endswith(".vcf"):
                    contact_path = href_elem.text
                    contact_response = self._session.adapter_dav.request("GET", contact_path)
                    if contact_response.status_code == 200:
                        contacts.append(Contact(contact_response.text))
        return contacts

    def create_contact(
        self,
        addressbook_id: int | str | AddressBook,
        full_name: str,
        first_name: str = "",
        last_name: str = "",
        emails: list[str] | None = None,
        phones: list[str] | None = None,
        organization: str = "",
    ) -> Contact:
        """Creates a new contact in an address book.

        :param addressbook_id: ID, URI, or AddressBook object of the address book.
        :param full_name: Full name of the contact.
        :param first_name: First name of the contact.
        :param last_name: Last name of the contact.
        :param emails: List of email addresses.
        :param phones: List of phone numbers.
        :param organization: Organization name.
        """
        require_capabilities("dav", self._session.capabilities)
        user = self._session.user
        if not user:
            raise ValueError("User not available in session.")

        if isinstance(addressbook_id, AddressBook):
            addressbook_uri = addressbook_id.uri
        elif isinstance(addressbook_id, str):
            addressbook_uri = addressbook_id
        else:
            addressbooks = self.get_addressbooks()
            matching = [ab for ab in addressbooks if ab.addressbook_id == addressbook_id]
            if not matching:
                raise ValueError(f"Address book with ID {addressbook_id} not found.")
            addressbook_uri = matching[0].uri

        contact_id = f"{full_name.replace(' ', '_')}_{datetime.datetime.now().timestamp()}".replace(".", "")
        vcard = self._generate_vcard(
            contact_id, full_name, first_name, last_name, emails or [], phones or [], organization
        )

        dav_path = f"/remote.php/dav/addressbooks/users/{user}/{addressbook_uri}/{contact_id}.vcf"
        response = self._session.adapter_dav.request("PUT", dav_path, data=vcard.encode("utf-8"))
        if response.status_code not in (200, 201, 204):
            raise ValueError(f"Failed to create contact: {response.status_code}")

        return Contact(vcard)

    def _generate_vcard(
        self,
        contact_id: str,
        full_name: str,
        first_name: str,
        last_name: str,
        emails: list[str],
        phones: list[str],
        organization: str,
    ) -> str:
        """Generate vCard format string."""
        vcard_lines = ["BEGIN:VCARD", "VERSION:3.0", f"UID:{contact_id}"]
        if full_name:
            vcard_lines.append(f"FN:{full_name}")
        if first_name or last_name:
            vcard_lines.append(f"N:{last_name};{first_name};;;")
        if organization:
            vcard_lines.append(f"ORG:{organization}")
        for email in emails:
            vcard_lines.append(f"EMAIL;TYPE=INTERNET:{email}")
        for phone in phones:
            vcard_lines.append(f"TEL;TYPE=CELL:{phone}")
        vcard_lines.append("END:VCARD")
        return "\r\n".join(vcard_lines)


class _AsyncContactsAPI:
    """Class provides async Contacts API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/dav/api/v1/addressbooks"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("dav", await self._session.capabilities)

    async def get_addressbooks(self) -> list[AddressBook]:
        """Returns a list of all address books for the current user."""
        require_capabilities("dav", await self._session.capabilities)
        user = await self._session.user
        if not user:
            raise ValueError("User not available in session.")
        result = await self._session.ocs("GET", f"{self._ep_base}/{user}")
        return [AddressBook(i) for i in result]

    async def get_contacts(self, addressbook_id: int | str | AddressBook) -> list[Contact]:
        """Returns all contacts in an address book.

        :param addressbook_id: ID, URI, or AddressBook object of the address book.
        """
        require_capabilities("dav", await self._session.capabilities)
        user = await self._session.user
        if not user:
            raise ValueError("User not available in session.")

        if isinstance(addressbook_id, AddressBook):
            addressbook_uri = addressbook_id.uri
        elif isinstance(addressbook_id, str):
            addressbook_uri = addressbook_id
        else:
            addressbooks = await self.get_addressbooks()
            matching = [ab for ab in addressbooks if ab.addressbook_id == addressbook_id]
            if not matching:
                raise ValueError(f"Address book with ID {addressbook_id} not found.")
            addressbook_uri = matching[0].uri

        dav_path = f"/remote.php/dav/addressbooks/users/{user}/{addressbook_uri}/"
        response = await self._session.adapter_dav.request("PROPFIND", dav_path, headers={"Depth": "1"})
        contacts = []
        if response.status_code == 207:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
            for response_elem in root.findall(".//{DAV:}response"):
                href_elem = response_elem.find("{DAV:}href")
                if href_elem is not None and href_elem.text and href_elem.text.endswith(".vcf"):
                    contact_path = href_elem.text
                    contact_response = await self._session.adapter_dav.request("GET", contact_path)
                    if contact_response.status_code == 200:
                        contacts.append(Contact(contact_response.text))
        return contacts

    async def create_contact(
        self,
        addressbook_id: int | str | AddressBook,
        full_name: str,
        first_name: str = "",
        last_name: str = "",
        emails: list[str] | None = None,
        phones: list[str] | None = None,
        organization: str = "",
    ) -> Contact:
        """Creates a new contact in an address book.

        :param addressbook_id: ID, URI, or AddressBook object of the address book.
        :param full_name: Full name of the contact.
        :param first_name: First name of the contact.
        :param last_name: Last name of the contact.
        :param emails: List of email addresses.
        :param phones: List of phone numbers.
        :param organization: Organization name.
        """
        require_capabilities("dav", await self._session.capabilities)
        user = await self._session.user
        if not user:
            raise ValueError("User not available in session.")

        if isinstance(addressbook_id, AddressBook):
            addressbook_uri = addressbook_id.uri
        elif isinstance(addressbook_id, str):
            addressbook_uri = addressbook_id
        else:
            addressbooks = await self.get_addressbooks()
            matching = [ab for ab in addressbooks if ab.addressbook_id == addressbook_id]
            if not matching:
                raise ValueError(f"Address book with ID {addressbook_id} not found.")
            addressbook_uri = matching[0].uri

        contact_id = f"{full_name.replace(' ', '_')}_{datetime.datetime.now().timestamp()}".replace(".", "")
        vcard = self._generate_vcard(
            contact_id, full_name, first_name, last_name, emails or [], phones or [], organization
        )

        dav_path = f"/remote.php/dav/addressbooks/users/{user}/{addressbook_uri}/{contact_id}.vcf"
        response = await self._session.adapter_dav.request("PUT", dav_path, data=vcard.encode("utf-8"))
        if response.status_code not in (200, 201, 204):
            raise ValueError(f"Failed to create contact: {response.status_code}")

        return Contact(vcard)

    def _generate_vcard(
        self,
        contact_id: str,
        full_name: str,
        first_name: str,
        last_name: str,
        emails: list[str],
        phones: list[str],
        organization: str,
    ) -> str:
        """Generate vCard format string."""
        vcard_lines = ["BEGIN:VCARD", "VERSION:3.0", f"UID:{contact_id}"]
        if full_name:
            vcard_lines.append(f"FN:{full_name}")
        if first_name or last_name:
            vcard_lines.append(f"N:{last_name};{first_name};;;")
        if organization:
            vcard_lines.append(f"ORG:{organization}")
        for email in emails:
            vcard_lines.append(f"EMAIL;TYPE=INTERNET:{email}")
        for phone in phones:
            vcard_lines.append(f"TEL;TYPE=CELL:{phone}")
        vcard_lines.append("END:VCARD")
        return "\r\n".join(vcard_lines)
