Changelog
=========

0.3 (unreleased)
----------------

- Issue #5: Redirect subprocess stdout/err to files and log those as debug
  logging messages when a node is stopped.

- Expand documentation.

0.2 (2013-03-11)
----------------

- Allow configuration of ip instead of hardcoding `127.0.0.1`.

- Add `isolated.isolated` context manager.

- Add basic API documentation for all public modules.

- Allow explicit configuration of all cluster ports.

- Add an `urls` property to the cluster, to expose a list of client urls for
  all cluster nodes.

0.1 (2013-03-06)
----------------

- Initial version based on code from Mozilla monolith and on ideas and code
  from kazoo.
