"""Example of using File Comments API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if File Comments API is available
if nc.files.comments.available:
    # Get a file (or use file ID directly)
    files = nc.files.listdir("/")
    if files:
        test_file = files[0]
        print(f"Working with file: {test_file.name} (ID: {test_file.file_id})")

        # List comments for the file
        comments = nc.files.comments.get_list(test_file)
        print(f"\nFound {len(comments)} comments:")
        for comment in comments:
            print(f"  - [{comment.comment_id}] {comment.actor_id}: {comment.message[:50]}...")
            print(f"    Created: {comment.creation_datetime}")

        # Create a new comment
        print("\nCreating new comment...")
        new_comment = nc.files.comments.create(test_file, "This is a test comment from nc_py_api")
        print(f"Created comment: {new_comment.comment_id}")
        print(f"  Message: {new_comment.message}")
        print(f"  Actor: {new_comment.actor_id}")

        # List comments again
        comments = nc.files.comments.get_list(test_file)
        print(f"\nNow there are {len(comments)} comments")

        # Update the comment
        print(f"\nUpdating comment {new_comment.comment_id}...")
        nc.files.comments.update(test_file, new_comment.comment_id, "Updated comment message")
        print("Comment updated")

        # Delete the comment
        print(f"\nDeleting comment {new_comment.comment_id}...")
        nc.files.comments.delete(test_file, new_comment.comment_id)
        print("Comment deleted")

        # Final list
        comments = nc.files.comments.get_list(test_file)
        print(f"\nFinal count: {len(comments)} comments")

        # Example with pagination
        print("\nExample with pagination:")
        comments = nc.files.comments.get_list(test_file, limit=5, offset=0)
        print(f"Retrieved {len(comments)} comments (limit=5, offset=0)")
else:
    print("File Comments API is not available on this Nextcloud instance.")
