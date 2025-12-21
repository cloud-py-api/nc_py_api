"""Example of using Deck API with comprehensive card support testing."""

import datetime
import os

from nc_py_api import Nextcloud

# Initialize Nextcloud client
# Use environment variable or default to localhost:8081 for Docker setup
# Default credentials: admin/admin (for test instance only)
nextcloud_url = os.environ.get("NEXTCLOUD_URL", "http://localhost:8081")
nc_auth_user = os.environ.get("NC_AUTH_USER", "admin")
nc_auth_pass = os.environ.get("NC_AUTH_PASS", "admin")

nc = Nextcloud(nextcloud_url=nextcloud_url, nc_auth_user=nc_auth_user, nc_auth_pass=nc_auth_pass)

# Check if Deck API is available
if not nc.deck.available:
    print("Deck API is not available on this Nextcloud instance.")
    print("Please install the Deck app from the Nextcloud app store.")
    exit(1)

print("=" * 60)
print("Deck API Card Support Test")
print("=" * 60)

# Get all boards
boards = nc.deck.get_boards()
print(f"\nFound {len(boards)} existing boards")

# Create a test board
test_board = nc.deck.create_board(title="Card Test Board", color="#3498db")
print(f"\n✓ Created test board: {test_board.title} (ID: {test_board.board_id})")

try:
    # Create stacks for testing
    todo_stack = nc.deck.create_stack(board_id=test_board.board_id, title="To Do", order=0)
    print(f"✓ Created stack: {todo_stack.title} (ID: {todo_stack.stack_id})")
    
    in_progress_stack = nc.deck.create_stack(board_id=test_board.board_id, title="In Progress", order=1)
    print(f"✓ Created stack: {in_progress_stack.title} (ID: {in_progress_stack.stack_id})")
    
    done_stack = nc.deck.create_stack(board_id=test_board.board_id, title="Done", order=2)
    print(f"✓ Created stack: {done_stack.title} (ID: {done_stack.stack_id})")
    
    print("\n" + "=" * 60)
    print("Testing Card Operations")
    print("=" * 60)
    
    # Test 1: Create a card with all properties
    print("\n[Test 1] Creating card with due date and description...")
    future_date = datetime.datetime.now() + datetime.timedelta(days=7)
    card1 = nc.deck.create_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        title="Test Card 1: Implement feature",
        description="This is a **markdown** description with *formatting*",
        description_type="markdown",
        order=0,
        duedate=future_date
    )
    print(f"✓ Created card: {card1.title}")
    print(f"  - Card ID: {card1.card_id}")
    print(f"  - Board ID: {card1.board_id}")
    print(f"  - Stack ID: {card1.stack_id}")
    print(f"  - Owner: {card1.owner}")
    print(f"  - Order: {card1.order}")
    print(f"  - Due Date: {card1.duedate}")
    print(f"  - Description Type: {card1.description_type}")
    print(f"  - Archived: {card1.archived}")
    print(f"  - Labels: {card1.labels}")
    print(f"  - Assigned Users: {card1.assigned_users}")
    
    # Test 2: Create a simple card (minimal properties)
    print("\n[Test 2] Creating simple card (minimal properties)...")
    card2 = nc.deck.create_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        title="Test Card 2: Simple task",
        order=1
    )
    print(f"✓ Created card: {card2.title} (ID: {card2.card_id})")
    
    # Test 3: Get all cards in a stack
    print("\n[Test 3] Getting all cards in stack...")
    cards = nc.deck.get_cards(test_board.board_id, todo_stack.stack_id)
    print(f"✓ Found {len(cards)} cards in '{todo_stack.title}' stack:")
    for card in cards:
        print(f"  - {card.title} (ID: {card.card_id}, Order: {card.order})")
    
    # Test 4: Get a specific card by ID
    print("\n[Test 4] Getting specific card by ID...")
    retrieved_card = nc.deck.get_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        card_id=card1.card_id
    )
    print(f"✓ Retrieved card: {retrieved_card.title}")
    print(f"  - Description: {retrieved_card.description[:50]}...")
    assert retrieved_card.card_id == card1.card_id, "Card IDs should match"
    
    # Test 5: Update card properties
    print("\n[Test 5] Updating card properties...")
    new_due_date = datetime.datetime.now() + datetime.timedelta(days=14)
    updated_card = nc.deck.update_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        card_id=card1.card_id,
        title="Test Card 1: Updated title",
        description="Updated description with more details",
        duedate=new_due_date
    )
    print(f"✓ Updated card: {updated_card.title}")
    print(f"  - New due date: {updated_card.duedate}")
    assert updated_card.title == "Test Card 1: Updated title", "Title should be updated"
    
    # Test 6: Reorder card within same stack
    print("\n[Test 6] Reordering card within same stack...")
    nc.deck.reorder_card(card_id=card1.card_id, stack_id=todo_stack.stack_id, order=2)
    cards_after_reorder = nc.deck.get_cards(test_board.board_id, todo_stack.stack_id)
    card1_after = next(c for c in cards_after_reorder if c.card_id == card1.card_id)
    print(f"✓ Card reordered to position {card1_after.order}")
    assert card1_after.order == 2, "Card should be at order 2"
    
    # Test 7: Move card to another stack (reorder to different stack)
    print("\n[Test 7] Moving card to another stack...")
    nc.deck.reorder_card(card_id=card1.card_id, stack_id=in_progress_stack.stack_id, order=0)
    cards_in_progress = nc.deck.get_cards(test_board.board_id, in_progress_stack.stack_id)
    print(f"✓ Card moved to '{in_progress_stack.title}' stack")
    print(f"  - Cards in '{in_progress_stack.title}': {len(cards_in_progress)}")
    assert any(c.card_id == card1.card_id for c in cards_in_progress), "Card should be in new stack"
    
    # Test 8: Create multiple cards and verify ordering
    print("\n[Test 8] Creating multiple cards and testing order...")
    card3 = nc.deck.create_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        title="Test Card 3: Third task",
        order=0
    )
    card4 = nc.deck.create_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        title="Test Card 4: Fourth task",
        order=1
    )
    all_cards = nc.deck.get_cards(test_board.board_id, todo_stack.stack_id)
    print(f"✓ Created 2 more cards. Total cards in stack: {len(all_cards)}")
    for card in sorted(all_cards, key=lambda c: c.order):
        print(f"  - Order {card.order}: {card.title}")
    
    # Test 9: Delete a card
    print("\n[Test 9] Deleting a card...")
    nc.deck.delete_card(
        board_id=test_board.board_id,
        stack_id=todo_stack.stack_id,
        card_id=card2.card_id
    )
    remaining_cards = nc.deck.get_cards(test_board.board_id, todo_stack.stack_id)
    print(f"✓ Card deleted. Remaining cards: {len(remaining_cards)}")
    assert not any(c.card_id == card2.card_id for c in remaining_cards), "Card should be deleted"
    
    # Test 10: Get board with details (includes cards)
    print("\n[Test 10] Getting board with full details...")
    board_details = nc.deck.get_board(test_board.board_id)
    print(f"✓ Board: {board_details.title}")
    print(f"  - Stacks: {len(board_details.stacks)}")
    for stack in board_details.stacks:
        if stack.cards:
            print(f"  - Stack '{stack.title}': {len(stack.cards)} cards")
    
    print("\n" + "=" * 60)
    print("All Card Tests Passed! ✓")
    print("=" * 60)
    
finally:
    # Cleanup: Delete the test board (this will also delete all cards and stacks)
    print("\n[Cleanup] Deleting test board...")
    nc.deck.delete_board(test_board.board_id)
    print(f"✓ Test board '{test_board.title}' deleted")
    print("\nTest completed successfully!")
