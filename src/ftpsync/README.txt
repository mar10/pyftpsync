pyftpsync
=========

command line syntax
-------------------

--delete
    Delete files from target, if they do not exits in source
--dry-run
    Only print results
--force
    Override files, even if newer
--local
    Define local folder (default: current working directory)

$pyftpsync upload REMOTE --force

$pyftpsync download REMOTE --force

$pyftpsync sync REMOTE --force
