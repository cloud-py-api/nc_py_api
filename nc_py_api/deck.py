"""Nextcloud API for working with Deck."""

import dataclasses
import datetime

from ._misc import check_capabilities, clear_from_params_empty, nc_iso_time_to_datetime, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class Board:
    """Class representing one board."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def board_id(self) -> int:
        """Unique identifier of the board."""
        return self._raw_data["id"]

    @property
    def title(self) -> str:
        """Title of the board."""
        return self._raw_data["title"]

    @property
    def color(self) -> str:
        """Color of the board (hexadecimal)."""
        return self._raw_data.get("color", "")

    @property
    def owner(self) -> str:
        """User ID of the board owner."""
        return self._raw_data["owner"]

    @property
    def archived(self) -> bool:
        """Whether the board is archived."""
        return self._raw_data.get("archived", False)

    @property
    def deleted_at(self) -> int:
        """Unix timestamp when the board was deleted (0 if not deleted)."""
        return self._raw_data.get("deletedAt", 0)

    @property
    def labels(self) -> list[dict]:
        """List of labels associated with the board."""
        return self._raw_data.get("labels", [])

    @property
    def stacks(self) -> list[dict]:
        """List of stacks in the board (only populated when details=True)."""
        return self._raw_data.get("stacks", [])

    @property
    def users(self) -> list[dict]:
        """List of users with access to the board."""
        return self._raw_data.get("users", [])

    @property
    def acl(self) -> list[dict]:
        """Access control list for the board."""
        return self._raw_data.get("acl", [])

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.board_id}, title={self.title}, owner={self.owner}>"


@dataclasses.dataclass
class Stack:
    """Class representing one stack."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def stack_id(self) -> int:
        """Unique identifier of the stack."""
        return self._raw_data["id"]

    @property
    def board_id(self) -> int:
        """ID of the board this stack belongs to."""
        return self._raw_data["boardId"]

    @property
    def title(self) -> str:
        """Title of the stack."""
        return self._raw_data["title"]

    @property
    def order(self) -> int:
        """Order of the stack within the board."""
        return self._raw_data.get("order", 0)

    @property
    def cards(self) -> list[dict]:
        """List of cards in the stack (only populated when details=True)."""
        return self._raw_data.get("cards", [])

    @property
    def deleted_at(self) -> int:
        """Unix timestamp when the stack was deleted (0 if not deleted)."""
        return self._raw_data.get("deletedAt", 0)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.stack_id}, title={self.title}, board_id={self.board_id}>"


@dataclasses.dataclass
class Card:
    """Class representing one card."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def card_id(self) -> int:
        """Unique identifier of the card."""
        return self._raw_data["id"]

    @property
    def board_id(self) -> int:
        """ID of the board this card belongs to."""
        return self._raw_data["boardId"]

    @property
    def stack_id(self) -> int:
        """ID of the stack this card belongs to."""
        return self._raw_data["stackId"]

    @property
    def title(self) -> str:
        """Title of the card."""
        return self._raw_data["title"]

    @property
    def description(self) -> str:
        """Description of the card."""
        return self._raw_data.get("description", "")

    @property
    def description_type(self) -> str:
        """Type of description content (e.g., 'plain', 'markdown')."""
        return self._raw_data.get("type", "plain")

    @property
    def owner(self) -> str:
        """User ID of the card owner."""
        return self._raw_data["owner"]

    @property
    def order(self) -> int:
        """Order of the card within the stack."""
        return self._raw_data.get("order", 0)

    @property
    def duedate(self) -> datetime.datetime | None:
        """Due date of the card."""
        duedate = self._raw_data.get("duedate")
        if duedate:
            return nc_iso_time_to_datetime(duedate)
        return None

    @property
    def archived(self) -> bool:
        """Whether the card is archived."""
        return self._raw_data.get("archived", False)

    @property
    def deleted_at(self) -> int:
        """Unix timestamp when the card was deleted (0 if not deleted)."""
        return self._raw_data.get("deletedAt", 0)

    @property
    def labels(self) -> list[int]:
        """List of label IDs associated with the card."""
        return self._raw_data.get("labels", [])

    @property
    def assigned_users(self) -> list[str]:
        """List of user IDs assigned to the card."""
        return self._raw_data.get("assignedUsers", [])

    @property
    def attachments(self) -> list[dict]:
        """List of attachments on the card."""
        return self._raw_data.get("attachments", [])

    @property
    def comments(self) -> list[dict]:
        """List of comments on the card."""
        return self._raw_data.get("comments", [])

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.card_id}, title={self.title}, board_id={self.board_id}, stack_id={self.stack_id}>"


class _DeckAPI:
    """Class providing the Deck API on the Nextcloud server."""

    _ep_base: str = "/apps/deck/api/v1.0"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("deck", self._session.capabilities)

    def get_boards(self, details: bool = False) -> list[Board]:
        """Returns a list of all boards accessible to the current user.

        :param details: If True, includes detailed information about labels, stacks, and users.
        """
        require_capabilities("deck", self._session.capabilities)
        params = {"details": "true"} if details else {}
        clear_from_params_empty(list(params.keys()), params)
        result = self._session.ocs("GET", f"{self._ep_base}/boards", params=params)
        return [Board(i) for i in result]

    def get_board(self, board_id: int) -> Board:
        """Returns a specific board by ID."""
        require_capabilities("deck", self._session.capabilities)
        return Board(self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}"))

    def create_board(self, title: str, color: str = "") -> Board:
        """Creates a new board.

        :param title: Title of the board.
        :param color: Hexadecimal color code for the board (e.g., '#ff0000').
        """
        require_capabilities("deck", self._session.capabilities)
        params = {"title": title}
        if color:
            params["color"] = color
        clear_from_params_empty(list(params.keys()), params)
        return Board(self._session.ocs("POST", f"{self._ep_base}/boards", json=params))

    def update_board(self, board_id: int, **kwargs) -> Board:
        """Updates a board.

        :param board_id: ID of the board to update.
        :param kwargs: Fields to update (title, color, archived, etc.).
        """
        require_capabilities("deck", self._session.capabilities)
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Board(self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}", json=kwargs))

    def delete_board(self, board_id: int) -> None:
        """Deletes a board."""
        require_capabilities("deck", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}")

    def get_stacks(self, board_id: int) -> list[Stack]:
        """Returns all stacks in a board."""
        require_capabilities("deck", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks")
        return [Stack(i) for i in result]

    def get_stack(self, board_id: int, stack_id: int) -> Stack:
        """Returns a specific stack by ID."""
        require_capabilities("deck", self._session.capabilities)
        return Stack(self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}"))

    def create_stack(self, board_id: int, title: str, order: int = 0) -> Stack:
        """Creates a new stack in a board.

        :param board_id: ID of the board.
        :param title: Title of the stack.
        :param order: Position of the stack within the board.
        """
        require_capabilities("deck", self._session.capabilities)
        params = {"title": title, "order": order}
        clear_from_params_empty(list(params.keys()), params)
        return Stack(self._session.ocs("POST", f"{self._ep_base}/boards/{board_id}/stacks", json=params))

    def update_stack(self, board_id: int, stack_id: int, **kwargs) -> Stack:
        """Updates a stack.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack to update.
        :param kwargs: Fields to update (title, order, etc.).
        """
        require_capabilities("deck", self._session.capabilities)
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Stack(self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}", json=kwargs))

    def delete_stack(self, board_id: int, stack_id: int) -> None:
        """Deletes a stack."""
        require_capabilities("deck", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}")

    def get_cards(self, board_id: int, stack_id: int) -> list[Card]:
        """Returns all cards in a stack."""
        require_capabilities("deck", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards")
        return [Card(i) for i in result]

    def get_card(self, board_id: int, stack_id: int, card_id: int) -> Card:
        """Returns a specific card by ID."""
        require_capabilities("deck", self._session.capabilities)
        return Card(self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}"))

    def create_card(
        self,
        board_id: int,
        stack_id: int,
        title: str,
        description: str = "",
        description_type: str = "plain",
        order: int = 0,
        duedate: datetime.datetime | None = None,
        owner: str | None = None,
    ) -> Card:
        """Creates a new card in a stack.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack.
        :param title: Title of the card.
        :param description: Description of the card.
        :param description_type: Type of description content ('plain' or 'markdown').
        :param order: Position of the card within the stack.
        :param duedate: Due date for the card.
        :param owner: User ID of the card owner (defaults to current user).
        """
        require_capabilities("deck", self._session.capabilities)
        params = {"title": title, "type": description_type, "order": order}
        if description:
            params["description"] = description
        if duedate:
            params["duedate"] = duedate.isoformat()
        if owner:
            params["owner"] = owner
        elif self._session.user:
            params["owner"] = self._session.user
        clear_from_params_empty(list(params.keys()), params)
        return Card(self._session.ocs("POST", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards", json=params))

    def update_card(self, board_id: int, stack_id: int, card_id: int, **kwargs) -> Card:
        """Updates a card.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack.
        :param card_id: ID of the card to update.
        :param kwargs: Fields to update (title, description, duedate, etc.).
        """
        require_capabilities("deck", self._session.capabilities)
        if "duedate" in kwargs and isinstance(kwargs["duedate"], datetime.datetime):
            kwargs["duedate"] = kwargs["duedate"].isoformat()
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Card(self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}", json=kwargs))

    def delete_card(self, board_id: int, stack_id: int, card_id: int) -> None:
        """Deletes a card."""
        require_capabilities("deck", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}")

    def reorder_card(self, card_id: int, stack_id: int, order: int) -> None:
        """Reorders a card within a stack.

        :param card_id: ID of the card to reorder.
        :param stack_id: ID of the target stack.
        :param order: New position of the card within the stack.
        """
        require_capabilities("deck", self._session.capabilities)
        self._session.ocs("PUT", f"{self._ep_base}/cards/{card_id}/reorder", json={"stackId": stack_id, "order": order})


class _AsyncDeckAPI:
    """Class provides async Deck API on the Nextcloud server."""

    _ep_base: str = "/apps/deck/api/v1.0"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("deck", await self._session.capabilities)

    async def get_boards(self, details: bool = False) -> list[Board]:
        """Returns a list of all boards accessible to the current user.

        :param details: If True, includes detailed information about labels, stacks, and users.
        """
        require_capabilities("deck", await self._session.capabilities)
        params = {"details": "true"} if details else {}
        clear_from_params_empty(list(params.keys()), params)
        result = await self._session.ocs("GET", f"{self._ep_base}/boards", params=params)
        return [Board(i) for i in result]

    async def get_board(self, board_id: int) -> Board:
        """Returns a specific board by ID."""
        require_capabilities("deck", await self._session.capabilities)
        return Board(await self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}"))

    async def create_board(self, title: str, color: str = "") -> Board:
        """Creates a new board.

        :param title: Title of the board.
        :param color: Hexadecimal color code for the board (e.g., '#ff0000').
        """
        require_capabilities("deck", await self._session.capabilities)
        params = {"title": title}
        if color:
            params["color"] = color
        clear_from_params_empty(list(params.keys()), params)
        return Board(await self._session.ocs("POST", f"{self._ep_base}/boards", json=params))

    async def update_board(self, board_id: int, **kwargs) -> Board:
        """Updates a board.

        :param board_id: ID of the board to update.
        :param kwargs: Fields to update (title, color, archived, etc.).
        """
        require_capabilities("deck", await self._session.capabilities)
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Board(await self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}", json=kwargs))

    async def delete_board(self, board_id: int) -> None:
        """Deletes a board."""
        require_capabilities("deck", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}")

    async def get_stacks(self, board_id: int) -> list[Stack]:
        """Returns all stacks in a board."""
        require_capabilities("deck", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks")
        return [Stack(i) for i in result]

    async def get_stack(self, board_id: int, stack_id: int) -> Stack:
        """Returns a specific stack by ID."""
        require_capabilities("deck", await self._session.capabilities)
        return Stack(await self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}"))

    async def create_stack(self, board_id: int, title: str, order: int = 0) -> Stack:
        """Creates a new stack in a board.

        :param board_id: ID of the board.
        :param title: Title of the stack.
        :param order: Position of the stack within the board.
        """
        require_capabilities("deck", await self._session.capabilities)
        params = {"title": title, "order": order}
        clear_from_params_empty(list(params.keys()), params)
        return Stack(await self._session.ocs("POST", f"{self._ep_base}/boards/{board_id}/stacks", json=params))

    async def update_stack(self, board_id: int, stack_id: int, **kwargs) -> Stack:
        """Updates a stack.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack to update.
        :param kwargs: Fields to update (title, order, etc.).
        """
        require_capabilities("deck", await self._session.capabilities)
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Stack(await self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}", json=kwargs))

    async def delete_stack(self, board_id: int, stack_id: int) -> None:
        """Deletes a stack."""
        require_capabilities("deck", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}")

    async def get_cards(self, board_id: int, stack_id: int) -> list[Card]:
        """Returns all cards in a stack."""
        require_capabilities("deck", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards")
        return [Card(i) for i in result]

    async def get_card(self, board_id: int, stack_id: int, card_id: int) -> Card:
        """Returns a specific card by ID."""
        require_capabilities("deck", await self._session.capabilities)
        return Card(await self._session.ocs("GET", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}"))

    async def create_card(
        self,
        board_id: int,
        stack_id: int,
        title: str,
        description: str = "",
        description_type: str = "plain",
        order: int = 0,
        duedate: datetime.datetime | None = None,
        owner: str | None = None,
    ) -> Card:
        """Creates a new card in a stack.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack.
        :param title: Title of the card.
        :param description: Description of the card.
        :param description_type: Type of description content ('plain' or 'markdown').
        :param order: Position of the card within the stack.
        :param duedate: Due date for the card.
        :param owner: User ID of the card owner (defaults to current user).
        """
        require_capabilities("deck", await self._session.capabilities)
        params = {"title": title, "type": description_type, "order": order}
        if description:
            params["description"] = description
        if duedate:
            params["duedate"] = duedate.isoformat()
        if owner:
            params["owner"] = owner
        elif await self._session.user:
            params["owner"] = await self._session.user
        clear_from_params_empty(list(params.keys()), params)
        return Card(await self._session.ocs("POST", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards", json=params))

    async def update_card(self, board_id: int, stack_id: int, card_id: int, **kwargs) -> Card:
        """Updates a card.

        :param board_id: ID of the board.
        :param stack_id: ID of the stack.
        :param card_id: ID of the card to update.
        :param kwargs: Fields to update (title, description, duedate, etc.).
        """
        require_capabilities("deck", await self._session.capabilities)
        if "duedate" in kwargs and isinstance(kwargs["duedate"], datetime.datetime):
            kwargs["duedate"] = kwargs["duedate"].isoformat()
        clear_from_params_empty(list(kwargs.keys()), kwargs)
        return Card(await self._session.ocs("PUT", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}", json=kwargs))

    async def delete_card(self, board_id: int, stack_id: int, card_id: int) -> None:
        """Deletes a card."""
        require_capabilities("deck", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}")

    async def reorder_card(self, card_id: int, stack_id: int, order: int) -> None:
        """Reorders a card within a stack.

        :param card_id: ID of the card to reorder.
        :param stack_id: ID of the target stack.
        :param order: New position of the card within the stack.
        """
        require_capabilities("deck", await self._session.capabilities)
        await self._session.ocs("PUT", f"{self._ep_base}/cards/{card_id}/reorder", json={"stackId": stack_id, "order": order})
