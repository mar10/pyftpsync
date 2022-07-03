=======================
Run from pyftpsync.yaml
=======================

Users can define sets of command line options as named *tasks* and store them
in the project folder. It can then be executed like so::

    $ pyftpsync run TASK


**File Discovery**

The file must be named :code:`pyftpsync.yaml` and located in the root folder of 
the project. |br|
When :bash:`pyftpsync run` is called, it looks for that file in the current
working directory and its parent folders.

When :bash:`pyftpsync run` was called from a subdirectory of the project, 
it has to be clarified if the synchronization should be done for the whole 
project (i.e. the root folder where `pyftpsync.yaml` is located), or only for the
current sub branch.
This can be done by passing the :bash:`--root` or :bash:`--here` option.


**File Format**

`pyftpsync.yaml` defines a list of *tasks* that have a name and a set of
options. |br|
Options are named like the command line arguments, using
`YAML <http://yaml.org/spec/1.2/spec.html>`_ syntax.

Main sections are 

:code:`default_task: TASK_NAME` (str)
     Name of a task that is run when not explicitly specified, i.e. running
     like :bash:`pyftpsync run`.

:code:`common_config` (dict)
    Contains settings that are shared/inherited by all concrete task 
    definitions. |br|
    Same syntax as described in :code:`tasks.TASK_NAME`.

:code:`tasks` (dict)
    contains one dict per task name

:code:`tasks.TASK_NAME` (dict)
    Contains optins that are passed to the CLI command.

    Values are inherited from the :code:`common_config` section, but can be
    overridden here.

    Typical values include:

    :code:`command: COMMAND_NAME` (str, mandatory)
        Command that should be run with the defined options, 
        must be one of 'upload', 'dowlnload', 'sync', 'tree'.

    :code:`remote: URL` (str, mandatory)
        Remote target URL and protocol, e.g. :code:`sftp://example.com/my_project`.

    :code:`local: REL_PATH` (str, default: :code:`.` or current folder)
        Local target path, relative to the location of the yaml file. |br|
        See also `root` option.

    :code:`dry_run: FLAG` (bool, default: :code:`false`)
        If true, the task will run in dry-run mode. |br|
        A caller can override :code:`dry_run: true` by passing :bash:`--execute` 
        (or :bash:`--no-dry-run`). |br|
        A caller can override :code:`dry_run: false` by passing :bash:`--dry-run` 
        (or :bash:`-n`).

    :code:`root: FLAG` (bool, default: `undefined`)
        When :bash:`pyftpsync run` was called from a subdirectory, it has to be
        clarified if the synchronization should be done for the whole project
        (i.e. the root folder where `pyftpsync.yaml` is located), or only for the
        current sub branch. |br|
        When :code:`here` is set, the remote target URL is adjusted relative to 
        the depth.|br|
        When neither :code:`root: true` nor :code:`here: true` are set, the
        command will prompt the user.

    :code:`here: FLAG` (str, default: `undefined`)
        See :code:`root` option.

    :code:`<any>` (str, optional)
        Most availble command line options can also be added, hovever
        leading :code:`--` must be removed and :code:`-` replaced with :code:`_`. |br|
        For example 
        :bash:`--force` becomes :code:`force: true`
        and :bash:`--delete-unmatched` becomes :code:`delete_unmatched: true`.


**File Execution**

A task is started like :bash:`pyftpsync run TASK`, where `TASK` must be an 
existing entry in the yaml file. |br|
When :bash:`pyftpsync run` is called without a `TASK`, it defaults to the
task name defined in :code:`default_task: TASK`.

Task settings can be overidden by command line args, for example::

    $ pyftpsync run deploy --execute --force -v

would overide task definition entries in the yaml file: :code:`dry_run: false`,
:code:`verbose: 4`, and :code:`force: true`.


.. note::
    If the credentials are already stored in the keyring or `.netrc` file, a
    simple ``pyftpsync run`` should synchronize the current project without
    further prompting. |br|
    When `SFTP` is used, also make sure that the remote host's public key is
    stored in `~/.ssh/known_hosts`.

Example:

.. literalinclude:: ../sample_pyftpsync.yaml
    :linenos:
    :language: yaml


For a start, copy
:download:`Annotated Sample Configuration <../sample_pyftpsync.yaml>`,
rename it to ``pyftpsync.yaml``, and edit it to your needs.
