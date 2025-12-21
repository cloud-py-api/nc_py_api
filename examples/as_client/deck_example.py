"""Example of using Deck API."""

import datetime

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Deck API is available
if nc.deck.available:
    # Get all boards
    boards = nc.deck.get_boards()
    print(f"Found {len(boards)} boards:")
    for board in boards:
        print(f"  - {board.title} (ID: {board.board_id}, Owner: {board.owner})")
    
    # Create a new board
    new_board = nc.deck.create_board(title="Project Management", color="#3498db")
    print(f"\nCreated board: {new_board.title} (ID: {new_board.board_id})")
    
    # Get stacks in the board
    stacks = nc.deck.get_stacks(new_board.board_id)
    print(f"\nBoard has {len(stacks)} stacks")
    
    # Create a new stack
    new_stack = nc.deck.create_stack(board_id=new_board.board_id, title="To Do", order=0)
    print(f"Created stack: {new_stack.title} (ID: {new_stack.stack_id})")
    
    # Create another stack
    in_progress_stack = nc.deck.create_stack(board_id=new_board.board_id, title="In Progress", order=1)
    print(f"Created stack: {in_progress_stack.title} (ID: {in_progress_stack.stack_id})")
    
    # Create a card
    card = nc.deck.create_card(
        board_id=new_board.board_id,
        stack_id=new_stack.stack_id,
        title="Implement new feature",
        description="This is a detailed description of the task",
        description_type="markdown",
        order=0,
        duedate=datetime.datetime.now() + datetime.timedelta(days=7)
    )
    print(f"\nCreated card: {card.title} (ID: {card.card_id})")
    
    # Get all cards in the stack
    cards = nc.deck.get_cards(new_board.board_id, new_stack.stack_id)
    print(f"\nStack '{new_stack.title}' has {len(cards)} cards")
    
    # Update the card
    updated_card = nc.deck.update_card(
        board_id=new_board.board_id,
        stack_id=new_stack.stack_id,
        card_id=card.card_id,
        description="Updated description with more details"
    )
    print(f"\nUpdated card: {updated_card.title}")
    
    # Move card to another stack (reorder)
    nc.deck.reorder_card(card_id=card.card_id, stack_id=in_progress_stack.stack_id, order=0)
    print(f"Moved card to '{in_progress_stack.title}' stack")
    
    # Get board details with full information
    board_details = nc.deck.get_board(new_board.board_id)
    print(f"\nBoard details: {board_details.title} - {len(board_details.stacks)} stacks")
    
    # Get all boards with details
    boards_with_details = nc.deck.get_boards(details=True)
    print(f"\nFound {len(boards_with_details)} boards with full details")
else:
    print("Deck API is not available on this Nextcloud instance.")
