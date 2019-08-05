Contribution Guide
------------------

This portion of the documentation outlines common development tasks for ``mdf_matio``.


Supporting a New Parser
=======================

Parsers that are introduced into MaterialsIO are not used in ``mdf_matio`` by defualt.
You first need to either specify that the parser already generates MDF-ready data
by adding it to the ``noop_parser`` list or creating a new adapter.

If creating a new adapter, first check whether any of hte existing adapter types
work for your problem.
For example, there is a specialized module for adapters that consist of mapping JSON documents
into the MDF format.

Once your adapter is complete, write unit tests and add the parser to the ``entry_point``
list in ``setup.py``.

The name of the adapter must be the same as its partnering parser.
If the names are the same and you reinstall the ``mdf_matio`` library,
then the new parser will be used automatically.
