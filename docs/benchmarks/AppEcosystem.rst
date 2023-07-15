AppEcosystem Benchmarks
=======================

In the current implementation, applications written and using the AppEcosystem
so far in most cases will be authenticated at the beginning of each action.

*A future enhancement that can be implemented is the addition of a session cache.
This feature would eliminate the need for re-authorization for subsequent actions performed
by the same user within a certain time frame.
The implementation of this session cache would be seamless for developers and require no additional actions.*

It is important to note that the AppEcosystem authentication type is currently the fastest among available options.
Compared to traditional username/password authentication and app password authentication,
both of which are considerably slower, the AppEcosystem provides a significant advantage in terms of speed.

When considering data transfer speed, it is worth mentioning
that the AppEcosystem's upload speed may be slightly lower, around 6-8 percent, for large data transfers.
This decrease in speed is due to the authentication process, which involves hashing all data.
However, for loading any data, there is no slowdown compared to standard methods.

In cases of loading any data, there is no slowdown relative to standard methods.

While the transfer speed can be affected by the network speed between the application and the cloud,
this aspect is beyond the scope of the discussed issue.

Conclusion
----------

In summary, the AppEcosystem authentication offers fast and secure access to user data.
With the potential addition of a session cache in the future, the authentication process can become even more efficient
and seamless for users. The slight decrease in upload speed for large data transfers
is a trade-off for the enhanced security provided by the authentication process.

Overall, the AppEcosystem authentication proves to be a reliable and effective method for application authentication.

.. toctree::
   :maxdepth: 1

   AppEcosystem_results.rst
