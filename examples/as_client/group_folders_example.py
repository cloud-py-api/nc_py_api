"""Example of using Group Folders API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Group Folders API is available
if nc.group_folders.available:
    # Get all group folders
    folders = nc.group_folders.get_list()
    print(f"Found {len(folders)} group folders:")
    for folder in folders:
        quota_str = "Unlimited" if folder.quota == -3 else f"{folder.quota / (1024**3):.2f} GB"
        print(f"  - {folder.mount_point} (ID: {folder.folder_id}, Quota: {quota_str})")
        print(f"    Groups: {list(folder.groups.keys())}")
    
    # Create a new group folder
    new_folder = nc.group_folders.create(mount_point="Shared Documents")
    print(f"\nCreated group folder: {new_folder.mount_point} (ID: {new_folder.folder_id})")
    
    # Set quota (in bytes, -3 for unlimited)
    # Example: 10 GB = 10 * 1024 * 1024 * 1024 bytes
    quota_10gb = 10 * 1024 * 1024 * 1024
    nc.group_folders.set_quota(folder_id=new_folder.folder_id, quota=quota_10gb)
    print(f"Set quota to 10 GB")
    
    # Set permissions for a group
    # Permission bitmasks: 1=Read, 2=Write, 4=Create, 8=Delete, 16=Share, 31=All
    READ_WRITE = 1 | 2  # Read + Write
    FULL_ACCESS = 31  # All permissions
    
    nc.group_folders.set_permissions(
        folder_id=new_folder.folder_id,
        group_id="developers",
        permissions=FULL_ACCESS
    )
    print(f"Set full access for 'developers' group")
    
    nc.group_folders.set_permissions(
        folder_id=new_folder.folder_id,
        group_id="viewers",
        permissions=READ_WRITE
    )
    print(f"Set read/write access for 'viewers' group")
    
    # Enable Advanced Permissions (ACL)
    nc.group_folders.set_acl(folder_id=new_folder.folder_id, acl=True)
    print(f"Enabled Advanced Permissions (ACL)")
    
    # Set ACL permission for a specific user
    nc.group_folders.set_acl_permission(
        folder_id=new_folder.folder_id,
        mapping_id="admin",
        mapping_type="user",
        permissions=FULL_ACCESS
    )
    print(f"Set full ACL access for user 'admin'")
    
    # Get updated folder details
    updated_folder = nc.group_folders.get(new_folder.folder_id)
    print(f"\nFolder details:")
    print(f"  Mount point: {updated_folder.mount_point}")
    print(f"  Quota: {updated_folder.quota}")
    print(f"  ACL enabled: {updated_folder.acl}")
    print(f"  Groups: {list(updated_folder.groups.keys())}")
    
    # Remove a group from the folder
    nc.group_folders.remove_group(folder_id=new_folder.folder_id, group_id="viewers")
    print(f"\nRemoved 'viewers' group from folder")
    
    # Remove ACL permission
    nc.group_folders.remove_acl_permission(
        folder_id=new_folder.folder_id,
        mapping_id="admin",
        mapping_type="user"
    )
    print(f"Removed ACL permission for user 'admin'")
    
    # Disable ACL
    nc.group_folders.set_acl(folder_id=new_folder.folder_id, acl=False)
    print(f"Disabled Advanced Permissions (ACL)")
    
    # Note: Uncomment to delete the folder
    # nc.group_folders.delete(new_folder.folder_id)
    # print(f"Deleted folder")
else:
    print("Group Folders API is not available on this Nextcloud instance.")
