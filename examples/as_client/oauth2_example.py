"""Example of using OAuth2 Client Management API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client (requires admin privileges)
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if OAuth2 API is available
if nc.oauth2.available:
    # List all OAuth2 clients
    clients = nc.oauth2.get_list()
    print(f"Found {len(clients)} OAuth2 clients:")
    for client in clients:
        print(f"  - {client.name} (ID: {client.client_id}, Redirect URI: {client.redirect_uri})")

    # Create a new OAuth2 client
    print("\nCreating new OAuth2 client...")
    new_client = nc.oauth2.create(name="My Test Application", redirect_uri="http://localhost:8080/callback")
    print(f"Created client:")
    print(f"  - Name: {new_client.name}")
    print(f"  - Client ID: {new_client.client_id}")
    print(f"  - Client Secret: {new_client.client_secret}")
    print(f"  - Redirect URI: {new_client.redirect_uri}")

    # List clients again to verify
    clients = nc.oauth2.get_list()
    print(f"\nNow there are {len(clients)} OAuth2 clients")

    # Delete the client we just created
    print(f"\nDeleting client {new_client.client_id}...")
    nc.oauth2.delete(new_client.client_id)
    print("Client deleted successfully")

    # Final list
    clients = nc.oauth2.get_list()
    print(f"\nFinal count: {len(clients)} OAuth2 clients")
else:
    print("OAuth2 API is not available on this Nextcloud instance.")
    print("Note: OAuth2 Client Management requires admin privileges and the OAuth2 app to be installed.")
