"""Nextcloud API for working with Forms."""

import dataclasses
import datetime

from ._misc import check_capabilities, clear_from_params_empty, nc_iso_time_to_datetime, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class Form:
    """Class representing one form."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def form_id(self) -> int:
        """Unique identifier of the form."""
        return self._raw_data["id"]

    @property
    def hash(self) -> str:
        """Hash identifier of the form."""
        return self._raw_data["hash"]

    @property
    def title(self) -> str:
        """Title of the form."""
        return self._raw_data["title"]

    @property
    def description(self) -> str:
        """Description of the form."""
        return self._raw_data.get("description", "")

    @property
    def owner(self) -> str:
        """User ID of the form owner."""
        return self._raw_data["owner"]

    @property
    def access(self) -> dict:
        """Access permissions for the form."""
        return self._raw_data.get("access", {})

    @property
    def is_anonymous(self) -> bool:
        """Whether submissions are anonymous."""
        return self._raw_data.get("isAnonymous", False)

    @property
    def submit_multiple(self) -> bool:
        """Whether multiple submissions are allowed."""
        return self._raw_data.get("submitMultiple", False)

    @property
    def expires(self) -> datetime.datetime | None:
        """Expiration date/time of the form."""
        expires = self._raw_data.get("expires")
        if expires:
            return nc_iso_time_to_datetime(expires)
        return None

    @property
    def created(self) -> datetime.datetime:
        """Creation date/time of the form."""
        return nc_iso_time_to_datetime(self._raw_data["created"])

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.form_id}, title={self.title}, owner={self.owner}>"


@dataclasses.dataclass
class Question:
    """Class representing one question in a form."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def question_id(self) -> int:
        """Unique identifier of the question."""
        return self._raw_data["id"]

    @property
    def form_id(self) -> int:
        """ID of the form this question belongs to."""
        return self._raw_data["formId"]

    @property
    def question_type(self) -> str:
        """Type of the question (e.g., 'short', 'long', 'multiple_choice', etc.)."""
        return self._raw_data["type"]

    @property
    def text(self) -> str:
        """Question text."""
        return self._raw_data["text"]

    @property
    def description(self) -> str:
        """Question description."""
        return self._raw_data.get("description", "")

    @property
    def is_required(self) -> bool:
        """Whether the question is required."""
        return self._raw_data.get("isRequired", False)

    @property
    def order(self) -> int:
        """Order of the question in the form."""
        return self._raw_data.get("order", 0)

    @property
    def options(self) -> list[str]:
        """Options for multiple choice questions."""
        return self._raw_data.get("options", [])

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.question_id}, type={self.question_type}, form_id={self.form_id}>"


@dataclasses.dataclass
class Submission:
    """Class representing one form submission."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def submission_id(self) -> int:
        """Unique identifier of the submission."""
        return self._raw_data["id"]

    @property
    def form_id(self) -> int:
        """ID of the form this submission belongs to."""
        return self._raw_data["formId"]

    @property
    def user_id(self) -> str:
        """User ID of the submitter (empty if anonymous)."""
        return self._raw_data.get("userId", "")

    @property
    def answers(self) -> list[dict]:
        """List of answers submitted."""
        return self._raw_data.get("answers", [])

    @property
    def submitted(self) -> datetime.datetime:
        """Submission date/time."""
        return nc_iso_time_to_datetime(self._raw_data["submitted"])

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.submission_id}, form_id={self.form_id},"
            f" user_id={self.user_id}, submitted={self.submitted}>"
        )


class _FormsAPI:
    """Class providing the Forms API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/forms/api/v3"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("forms", self._session.capabilities)

    def get_list(self) -> list[Form]:
        """Returns a list of all forms accessible to the current user."""
        require_capabilities("forms", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/forms")
        return [Form(i) for i in result]

    def get(self, form_id: int) -> Form:
        """Returns a specific form by ID."""
        require_capabilities("forms", self._session.capabilities)
        return Form(self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}"))

    def create(
        self,
        title: str,
        description: str = "",
        is_anonymous: bool = False,
        submit_multiple: bool = False,
        expires: datetime.datetime | None = None,
    ) -> Form:
        """Creates a new form.

        :param title: Title of the form.
        :param description: Description of the form.
        :param is_anonymous: Whether submissions should be anonymous.
        :param submit_multiple: Whether multiple submissions are allowed.
        :param expires: Expiration date/time for the form.
        """
        require_capabilities("forms", self._session.capabilities)
        params = {
            "title": title,
            "description": description,
            "isAnonymous": is_anonymous,
            "submitMultiple": submit_multiple,
        }
        if expires:
            params["expires"] = expires.isoformat()
        clear_from_params_empty(list(params.keys()), params)
        return Form(self._session.ocs("POST", f"{self._ep_base}/forms", json=params))

    def delete(self, form_id: int) -> None:
        """Deletes a form."""
        require_capabilities("forms", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/forms/{form_id}")

    def get_questions(self, form_id: int) -> list[Question]:
        """Returns all questions for a specific form."""
        require_capabilities("forms", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}/questions")
        return [Question(i) for i in result]

    def create_question(
        self,
        form_id: int,
        question_type: str,
        text: str,
        description: str = "",
        is_required: bool = False,
        order: int = 0,
        options: list[str] | None = None,
    ) -> Question:
        """Creates a new question for a form.

        :param form_id: ID of the form.
        :param question_type: Type of question (e.g., 'short', 'long', 'multiple_choice', etc.).
        :param text: Question text.
        :param description: Question description.
        :param is_required: Whether the question is required.
        :param order: Order of the question in the form.
        :param options: Options for multiple choice questions.
        """
        require_capabilities("forms", self._session.capabilities)
        params = {
            "type": question_type,
            "text": text,
            "description": description,
            "isRequired": is_required,
            "order": order,
        }
        if options:
            params["options"] = options
        clear_from_params_empty(list(params.keys()), params)
        return Question(self._session.ocs("POST", f"{self._ep_base}/forms/{form_id}/questions", json=params))

    def delete_question(self, form_id: int, question_id: int) -> None:
        """Deletes a question from a form."""
        require_capabilities("forms", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/forms/{form_id}/questions/{question_id}")

    def get_submissions(self, form_id: int) -> list[Submission]:
        """Returns all submissions for a specific form."""
        require_capabilities("forms", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}/submissions")
        return [Submission(i) for i in result]

    def create_submission(self, form_id: int, answers: list[dict]) -> Submission:
        """Creates a new submission for a form.

        :param form_id: ID of the form.
        :param answers: List of answer dictionaries, each containing 'questionId' and 'text' keys.
        """
        require_capabilities("forms", self._session.capabilities)
        return Submission(self._session.ocs("POST", f"{self._ep_base}/forms/{form_id}/submissions", json={"answers": answers}))


class _AsyncFormsAPI:
    """Class provides async Forms API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/forms/api/v3"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("forms", await self._session.capabilities)

    async def get_list(self) -> list[Form]:
        """Returns a list of all forms accessible to the current user."""
        require_capabilities("forms", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/forms")
        return [Form(i) for i in result]

    async def get(self, form_id: int) -> Form:
        """Returns a specific form by ID."""
        require_capabilities("forms", await self._session.capabilities)
        return Form(await self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}"))

    async def create(
        self,
        title: str,
        description: str = "",
        is_anonymous: bool = False,
        submit_multiple: bool = False,
        expires: datetime.datetime | None = None,
    ) -> Form:
        """Creates a new form.

        :param title: Title of the form.
        :param description: Description of the form.
        :param is_anonymous: Whether submissions should be anonymous.
        :param submit_multiple: Whether multiple submissions are allowed.
        :param expires: Expiration date/time for the form.
        """
        require_capabilities("forms", await self._session.capabilities)
        params = {
            "title": title,
            "description": description,
            "isAnonymous": is_anonymous,
            "submitMultiple": submit_multiple,
        }
        if expires:
            params["expires"] = expires.isoformat()
        clear_from_params_empty(list(params.keys()), params)
        return Form(await self._session.ocs("POST", f"{self._ep_base}/forms", json=params))

    async def delete(self, form_id: int) -> None:
        """Deletes a form."""
        require_capabilities("forms", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/forms/{form_id}")

    async def get_questions(self, form_id: int) -> list[Question]:
        """Returns all questions for a specific form."""
        require_capabilities("forms", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}/questions")
        return [Question(i) for i in result]

    async def create_question(
        self,
        form_id: int,
        question_type: str,
        text: str,
        description: str = "",
        is_required: bool = False,
        order: int = 0,
        options: list[str] | None = None,
    ) -> Question:
        """Creates a new question for a form.

        :param form_id: ID of the form.
        :param question_type: Type of question (e.g., 'short', 'long', 'multiple_choice', etc.).
        :param text: Question text.
        :param description: Question description.
        :param is_required: Whether the question is required.
        :param order: Order of the question in the form.
        :param options: Options for multiple choice questions.
        """
        require_capabilities("forms", await self._session.capabilities)
        params = {
            "type": question_type,
            "text": text,
            "description": description,
            "isRequired": is_required,
            "order": order,
        }
        if options:
            params["options"] = options
        clear_from_params_empty(list(params.keys()), params)
        return Question(await self._session.ocs("POST", f"{self._ep_base}/forms/{form_id}/questions", json=params))

    async def delete_question(self, form_id: int, question_id: int) -> None:
        """Deletes a question from a form."""
        require_capabilities("forms", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/forms/{form_id}/questions/{question_id}")

    async def get_submissions(self, form_id: int) -> list[Submission]:
        """Returns all submissions for a specific form."""
        require_capabilities("forms", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/forms/{form_id}/submissions")
        return [Submission(i) for i in result]

    async def create_submission(self, form_id: int, answers: list[dict]) -> Submission:
        """Creates a new submission for a form.

        :param form_id: ID of the form.
        :param answers: List of answer dictionaries, each containing 'questionId' and 'text' keys.
        """
        require_capabilities("forms", await self._session.capabilities)
        return Submission(await self._session.ocs("POST", f"{self._ep_base}/forms/{form_id}/submissions", json={"answers": answers}))
