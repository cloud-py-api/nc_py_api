"""Example of using Contacts API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Contacts API is available
if nc.contacts.available:
    # Get all address books
    addressbooks = nc.contacts.get_addressbooks()
    print(f"Found {len(addressbooks)} address books:")
    for ab in addressbooks:
        print(f"  - {ab.name} (ID: {ab.addressbook_id}, URI: {ab.uri})")

    if addressbooks:
        # Use the first address book
        addressbook = addressbooks[0]

        # Get all contacts in the address book
        contacts = nc.contacts.get_contacts(addressbook)
        print(f"\nFound {len(contacts)} contacts in '{addressbook.name}':")
        for contact in contacts:
            print(f"  - {contact.full_name}")
            if contact.emails:
                print(f"    Email: {', '.join(contact.emails)}")
            if contact.phones:
                print(f"    Phone: {', '.join(contact.phones)}")
            if contact.organization:
                print(f"    Organization: {contact.organization}")

        # Create a new contact
        new_contact = nc.contacts.create_contact(
            addressbook_id=addressbook.addressbook_id,
            full_name="John Doe",
            first_name="John",
            last_name="Doe",
            emails=["john.doe@example.com"],
            phones=["+1234567890"],
            organization="Example Corp",
        )
        print(f"\nCreated contact: {new_contact.full_name} (ID: {new_contact.contact_id})")

        # Get updated contact list
        updated_contacts = nc.contacts.get_contacts(addressbook)
        print(f"\nNow have {len(updated_contacts)} contacts in '{addressbook.name}'")
else:
    print("Contacts API is not available on this Nextcloud instance.")
