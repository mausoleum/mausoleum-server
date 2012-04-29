mausoleum-server
================

The server for the Mausoleum secure file-sync program.


TODO
=============

* Store IVs and sequence numbers on the server and make them accessible
* Key management
    * Adding other people's keys
    * Getting your key for a given file
    * Deleting keys (same as uploading new keys for everybody but that person?)
* Reject invalid metadata uploads/deletes.
* New user registration
* Move off of sqlite
* Malicious option
* More tests
