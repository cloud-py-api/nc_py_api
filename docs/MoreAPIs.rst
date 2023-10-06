.. _more-apis:

More APIs
=========

All provided APIs can be accessed using instance of `Nextcloud` or `NextcloudApp` class.

For example, let's print all Talk conversations for the current user:

.. code-block:: python

    from nc_py_api import Nextcloud


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    all_conversations = nc.talk.get_user_conversations()
    for conversation in all_conversations:
        print(conversation.conversation_type.name + ": " + conversation.display_name)

Or let's find only your favorite conversations and send them a sweet message containing only heart emoticons: "❤️❤️❤️"


.. code-block:: python

    from nc_py_api import Nextcloud


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    all_conversations = nc.talk.get_user_conversations()
    for conversation in all_conversations:
        if conversation.is_favorite:
            print(conversation.conversation_type.name + ": " + conversation.display_name)
            nc.talk.send_message("❤️❤️❤️️", conversation)
