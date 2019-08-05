Module Design
-------------

The MDF module is comprised of three main components:

    #. MDF-specific parsers
    #. Adapters from MatIO to MDF Formats
    #. Streamlined Interface

We detail the design goals for each of these features in this part of the documentation.

MDF-specific Parsers
++++++++++++++++++++

There is currently only one parser that is MDF specific, the JSON parser.
This parser just reads in JSON files from disk, which does not really fit
the other MaterialsIO parsers.

Adapters
++++++++

``mdf_matio`` defines many classes that provide logic for converting MaterialsIO-format data into an MDF-compatible format.
They all follow the :class:`materails_io.adapters.base.BaseAdapter` abstract class, and
come in several varieties.

The first are "one-off" adapters, such as :class:`mdf_matio.adapters.FileAdapter`, which
are unique compared to other adapters.

There are also "mappable" adapters which apply a mapping on JSON documents produced
by MaterialsIO to an MDF format.
These class can also take a MaterialsIO document that contains multiple sub-records
and expand them into a list of independent records.

The "Citrine" module contains logic that maps PIF-format data into an MDF format.

The :mod:`mdf_matio.adapter` module also contains a ``noop_parser`` list that
contains parsers whose output requires no modification.

Streamlined Interface
+++++++++++++++++++++

This library was built to provide a simple way for taking a directory of user data
and generate records for the MDF search engine.
There is a single function that provides this functionality::

    from mdf_matio import generate_search_index
    gen = generate_search_index('/path/to/data')
    print(f'Found {len(list(gen))} records')


The function first determines which parsers have an adapter defined or
already produce data in the MDF format.

Next, the function looks for directories with ``mdf.json`` files and
determines what configuration settings are requested by the user.

The class then runs a parser and adapter pair
on all files in the designated directory,
combines records in directories marked by ``mdf.json`` files,
and then combines records describing the same file.

Optionally, the function can validate the data against the
`latest version of MDF Data Schemas <https://github.com/materials-data-facility/data-schemas>`_.

The parsing functionality can also be configured using the ``index_option`` keyword
argument, which takes data in the same format as the `MDF Connect POST request <https://github.com/materials-data-facility/data-schemas/blob/master/schemas/connect_submission.json>`_.
