shaunsephton.recipe.uwsgi
=========================
    
**Buildout recipe downloading, compiling and configuring uWSGI_.**

Creates a ``bin/`` uWSGI_ executable and ``parts`` XML configuration file with which you can easily launch Buildout sandboxed uWSGI_ processes.

Usage
-----

Add a part to your ``buildout.cfg`` likes so::

    [buildout]
    parts=uwsgi

    [uwsgi]
    recipe=shaunsephton.recipe.uwsgi

Running the buildout will download and compile uWSGI_ and add an executable with the same name as your part in the ``bin/`` directory. In this case ``bin/uwsgi``. It will also create a ``uwsgi.xml`` configuration file in a ``parts`` directory with the same name as your part. In this case ``bin/uwsgi/uwsgi.xml``.

.. _uWSGI: http://projects.unbit.it/uwsgi/wiki/Doc
