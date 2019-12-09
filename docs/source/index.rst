.. _Privex EOS Python documentation:

Privex EOS Python documentation
=================================================

.. image:: https://www.privex.io/static/assets/svg/brand_text_nofont.svg
   :target: https://www.privex.io/
   :width: 400px
   :height: 400px
   :alt: Privex Logo
   :align: center


Welcome to the documentation for `Privex's EOS Python Library`_ - an open source Python 3 library designed
for interacting with the `EOS`_ and potentially the `Telos`_ network.

This documentation is automatically kept up to date by ReadTheDocs, as it is automatically re-built each time
a new commit is pushed to the `Github Project`_

.. _Privex's EOS Python Library: https://github.com/Privex/eos-python
.. _Github Project: https://github.com/Privex/eos-python
.. _Telos: https://www.telosfoundation.io/
.. _EOS: https://eos.io

QuickStart
==========

To install ``eos-python`` - simply download it using ``pip``, just like any other package :)

.. code-block:: bash

    pip3 install eos-python

For alternative installation methods, see :ref:`Installation`

Below are some common examples for using the library:

.. code-block:: python

    from privex.eos import Api

    eos = Api()

    ###
    # Get account information + balances
    ###

    acc = await eos.get_account('someguy123')
    print(acc.account_name)
    # 'someguy123'

    print('Balance:', acc.core_liquid_balance)
    # Balance: 123.4567 EOS

    ###
    # Get blocks
    ###

    block = await eos.get_block(94000000)
    print(block.block_num)
    # 94000000
    print(block.id)
    # 059a5380852aef1ee27a0cd75953f76bb334ad402b4e0360dada1a17ee486357
    print(block.producer)
    # eoshuobipool

    # You can also get a range of blocks at once, returned as an ordered dictionary, with each block number
    # mapped to an EOSBlock object
    blocks = await eos.get_block_range(94000000, 94001000)
    print(blocks[94000412])

    blocks[94000412].timestamp
    # '2019-12-08T23:23:23.000'
    blocks[94000412].producer
    # 'zbeosbp11111'



Contents
=========

.. toctree::
   :maxdepth: 8
   :caption: Main:

   self
   install


.. toctree::
   :maxdepth: 8
   :caption: Code Documentation:

   code/index
   code/tests



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
