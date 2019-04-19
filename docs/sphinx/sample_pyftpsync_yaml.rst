===============
.pyftpsync.yaml
===============

The configuration file uses `YAML <http://yaml.org/spec/1.2/spec.html>`_ syntax.

  * The file must be named `.pyftpsync.yaml` and located in the root
    folder of the project.
  * When :bash:`pyftpsync run` is called, it looks for that file in the current
    working directory and parent folders.
  * When :bash:`pyftpsync run` was called from a sub-folder, it has to be
    clarified if the synchronisation should be done for the whole project
    (i.e. the root folder where `.pyftpsync.yaml` is located), or only for the
    current sub branch. |br|
    This can be done by passing the :bash:`--root` or :bash:`--here` option.

After storing it in your project's root folder, it can be executed like so::

    $ pyftpsync run

Default settings can be overidden by command line args::

    $ pyftpsync run TASK
    $ pyftpsync run --dry-run
    $ pyftpsync run --here

The configuration file defines one or more `TASKS`:

.. literalinclude:: ../sample_pyftpsync.yaml
    :linenos:
    :language: yaml

For a start, copy
:download:`Annotated Sample Configuration <../sample_pyftpsync.yaml>`,
rename it to `.pyftpsync.yaml` (note the leading dot),
and edit it to your needs.
