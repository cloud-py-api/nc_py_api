"""Example of using Circles API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Circles API is available
if nc.circles.available:
    # Get all circles
    circles = nc.circles.get_list()
    print(f"Found {len(circles)} circles:")
    for circle in circles:
        print(f"  - {circle.display_name} (ID: {circle.circle_id}, Type: {circle.circle_type})")

    # Create a new circle
    new_circle = nc.circles.create(name="project-team", display_name="Project Team")
    print(f"\nCreated circle: {new_circle.display_name} (ID: {new_circle.circle_id})")

    # Get circle details
    circle_details = nc.circles.get(new_circle.circle_id)
    print(f"Circle owner: {circle_details.owner}")

    # Get members
    members = nc.circles.get_members(new_circle.circle_id)
    print(f"\nCircle has {len(members)} members")

    # Add a member (user)
    member = nc.circles.add_member(circle_id=new_circle.circle_id, member_id="user1", member_type=1)  # 1 = User
    print(f"Added member: {member.display_name} (ID: {member.member_id})")

    # Bulk add members
    new_members = nc.circles.bulk_add_members(
        circle_id=new_circle.circle_id,
        members=[
            {"id": "user2", "type": 1},  # User
            {"id": "group1", "type": 2},  # Group
        ],
    )
    print(f"\nBulk added {len(new_members)} members")

    # Get updated member list
    updated_members = nc.circles.get_members(new_circle.circle_id)
    print(f"Circle now has {len(updated_members)} members")

    # Remove a member
    nc.circles.remove_member(circle_id=new_circle.circle_id, member_id="user1")
    print(f"\nRemoved member 'user1'")

    # Get final member list
    final_members = nc.circles.get_members(new_circle.circle_id)
    print(f"Circle now has {len(final_members)} members")

    # Note: Deleting circles managed elsewhere will raise an exception
    # try:
    #     nc.circles.delete(new_circle.circle_id)
    # except NextcloudException as e:
    #     print(f"Cannot delete circle: {e}")
else:
    print("Circles API is not available on this Nextcloud instance.")
