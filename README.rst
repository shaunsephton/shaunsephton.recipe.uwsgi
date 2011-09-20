shaunsephton.recipe.uwsgi
=========================
    
**Buildout recipe downloading, compiling and configuring uWSGI.**

Creates a ``bin/`` uWSGI_ executable and ``parts`` XML configuration file with which you can easily launch Buildout sandboxed uWSGI_ processes.

Usage
-----

Add a part to your ``buildout.cfg`` like so::

    [buildout]
    parts=uwsgi

    [uwsgi]
    recipe=shaunsephton.recipe.uwsgi

Running the buildout will download and compile uWSGI_ and add an executable with the same name as your part in the ``bin/`` directory. In this case ``bin/uwsgi``. It will also create a ``uwsgi.xml`` configuration file in a ``parts`` directory with the same name as your part. In this case ``bin/uwsgi/uwsgi.xml``.

This allows you to start a uWSGI_ process configured by the generated XML configuration file, i.e.::

    $ ./bin/uwsgi --xml parts/uwsgi/uwsgi.xml

The generated XML configuration includes ``pythonpath`` directives referencing the various Python eggs installed by Buildout and thus uWSGI_ can correctly utilize them.

.. _uWSGI: http://projects.unbit.it/uwsgi/wiki/Doc
