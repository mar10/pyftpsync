==============
pyftpsync.yaml
==============

Users can define sets of command line options as named *tasks* and store them
in the project folder. It can then be executed like so::

    $ pyftpsync run TASK

The file must be named `pyftpsync.yaml` and located in the root folder of the
project. |br|
When :bash:`pyftpsync run` is called, it looks for that file in the current
working directory and parent folders. |br|
When :bash:`pyftpsync run` was called from a sub-folder, it has to be
clarified if the synchronization should be done for the whole project
(i.e. the root folder where `pyftpsync.yaml` is located), or only for the
current sub branch.
This can be done by passing the :bash:`--root` or :bash:`--here` option.

`pyftpsync.yaml` defines a list of *tasks* that have a name and a set of
options. |br|
Options are named like the command line arguments, using
`YAML <http://yaml.org/spec/1.2/spec.html>`_ syntax, e.g.
:bash:`--force` becomes :code:`force: true`
and :bash:`--delete-unmatched` becomes :code:`delete_unmatched: true`.

The :code:`command` and :code:`remote` options are mandarory. |br|
A :code:`local` option must *not* be specified, since the local target path
is implicitly set to the folder location of `pyftpsync.yaml`.

Task settings can be overidden by command line args, e.g.::

    $ pyftpsync run deploy_force --dry-run -v
    $ pyftpsync run --here

Example:

.. literalinclude:: ../sample_pyftpsync.yaml
    :linenos:
    :language: yaml


For a start, copy
:download:`Annotated Sample Configuration <../sample_pyftpsync.yaml>`,
rename it to `pyftpsync.yaml` (note the leading dot),
and edit it to your needs.
