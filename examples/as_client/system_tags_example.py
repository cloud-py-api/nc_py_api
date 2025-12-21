"""Example of using System Tags API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if System Tags API is available
if nc.system_tags.available:
    # List all system tags
    tags = nc.system_tags.get_list()
    print(f"Found {len(tags)} system tags:")
    for tag in tags:
        print(f"  - {tag.display_name} (ID: {tag.tag_id})")
        print(f"    Visible: {tag.user_visible}, Assignable: {tag.user_assignable}")

    # Create a new system tag
    print("\nCreating new system tag...")
    new_tag = nc.system_tags.create(name="Important", user_visible=True, user_assignable=True)
    print(f"Created tag: {new_tag.display_name} (ID: {new_tag.tag_id})")

    # Get tag by name
    print("\nRetrieving tag by name...")
    tag = nc.system_tags.get_by_name("Important")
    print(f"Found tag: {tag.display_name} (ID: {tag.tag_id})")

    # Update the tag
    print("\nUpdating tag...")
    nc.system_tags.update(tag_id=tag.tag_id, user_visible=False)
    print("Tag updated")

    # List tags again to verify
    tags = nc.system_tags.get_list()
    print(f"\nNow there are {len(tags)} system tags")

    # Delete the tag we created
    print(f"\nDeleting tag {tag.tag_id}...")
    nc.system_tags.delete(tag.tag_id)
    print("Tag deleted successfully")

    # Final list
    tags = nc.system_tags.get_list()
    print(f"\nFinal count: {len(tags)} system tags")

    # Example: Assign tag to a file (using Files API)
    # Note: File-level tag operations remain in Files API
    # nc.files.assign_tag(file_id=123, tag_id=tag.tag_id)
else:
    print("System Tags API is not available on this Nextcloud instance.")
