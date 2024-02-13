"""Nextcloud API for declaring UI for settings."""

import dataclasses
import enum
import typing

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp


class SettingsFieldType(enum.Enum):  # StrEnum
    """Declarative Settings Field Type."""

    TEXT = "text"
    """NcInputField type text"""
    PASSWORD = "password"  # noqa
    """NcInputField type password"""
    EMAIL = "email"
    """NcInputField type email"""
    TEL = "tel"
    """NcInputField type tel"""
    URL = "url"
    """NcInputField type url"""
    NUMBER = "number"
    """NcInputField type number"""
    CHECKBOX = "checkbox"
    """NcCheckboxRadioSwitch type checkbox"""
    MULTI_CHECKBOX = "multi-checkbox"
    """Multiple NcCheckboxRadioSwitch type checkbox representing a one config value (saved as JSON object)"""
    RADIO = "radio"
    """NcCheckboxRadioSwitch type radio"""
    SELECT = "select"
    """NcSelect"""
    MULTI_SELECT = "multi-select"
    """Multiple NcSelect representing a one config value (saved as JSON array)"""


@dataclasses.dataclass
class SettingsField:
    """Section field."""

    id: str
    title: str
    type: SettingsFieldType
    default: bool | int | float | str | list[bool | int | float | str] | dict[str, typing.Any]
    options: dict | list = dataclasses.field(default_factory=dict)
    description: str = ""
    placeholder: str = ""
    label: str = ""
    notify = False  # to be supported in future

    @classmethod
    def from_dict(cls, data: dict) -> "SettingsField":
        """Creates instance of class from dict, ignoring unknown keys."""
        filtered_data = {
            k: SettingsFieldType(v) if k == "type" else v for k, v in data.items() if k in cls.__annotations__
        }
        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """Returns data in format that is accepted by AppAPI."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "default": self.default,
            "description": self.description,
            "options": (
                [{"name": key, "value": value} for key, value in self.options.items()]
                if isinstance(self.options, dict)
                else self.options
            ),
            "placeholder": self.placeholder,
            "label": self.label,
            "notify": self.notify,
        }


@dataclasses.dataclass
class SettingsForm:
    """Settings Form and Section."""

    id: str
    section_id: str
    title: str
    fields: list[SettingsField] = dataclasses.field(default_factory=list)
    description: str = ""
    priority: int = 50
    doc_url: str = ""
    section_type: str = "personal"

    @classmethod
    def from_dict(cls, data: dict) -> "SettingsForm":
        """Creates instance of class from dict, ignoring unknown keys."""
        filtered_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        filtered_data["fields"] = [SettingsField.from_dict(i) for i in filtered_data.get("fields", [])]
        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """Returns data in format that is accepted by AppAPI."""
        return {
            "id": self.id,
            "priority": self.priority,
            "section_type": self.section_type,
            "section_id": self.section_id,
            "title": self.title,
            "description": self.description,
            "doc_url": self.doc_url,
            "fields": [i.to_dict() for i in self.fields],
        }


_EP_SUFFIX: str = "ui/settings"


class _DeclarativeSettingsAPI:
    """Class providing API for creating UI for the ExApp settings, avalaible as **nc.ui.settings.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register_form(self, form_schema: SettingsForm | dict[str, typing.Any]) -> None:
        """Registers or edit the Settings UI Form."""
        require_capabilities("app_api", self._session.capabilities)
        param = {"formScheme": form_schema.to_dict() if isinstance(form_schema, SettingsForm) else form_schema}
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=param)

    def unregister_form(self, form_id: str, not_fail=True) -> None:
        """Removes Settings UI Form."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"formId": form_id})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, form_id: str) -> SettingsForm | None:
        """Get information of the Settings UI Form."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return SettingsForm.from_dict(
                self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"formId": form_id})
            )
        except NextcloudExceptionNotFound:
            return None


class _AsyncDeclarativeSettingsAPI:
    """Class providing async API for creating UI for the ExApp settings."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register_form(self, form_schema: SettingsForm | dict[str, typing.Any]) -> None:
        """Registers or edit the Settings UI Form."""
        require_capabilities("app_api", await self._session.capabilities)
        param = {"formScheme": form_schema.to_dict() if isinstance(form_schema, SettingsForm) else form_schema}
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=param)

    async def unregister_form(self, form_id: str, not_fail=True) -> None:
        """Removes Settings UI Form."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"formId": form_id})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, form_id: str) -> SettingsForm | None:
        """Get information of the Settings UI Form."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return SettingsForm.from_dict(
                await self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"formId": form_id})
            )
        except NextcloudExceptionNotFound:
            return None
