.. _Installation:

Installation
============

Download and install from PyPi using pip (recommended)
-------------------------------------------------------

.. code-block:: bash
    
    pip3 install privex-eos


(Alternative) Manual install from Git
--------------------------------------

**Option 1 - Use pip to install straight from Github**

.. code-block:: bash

    pip3 install git+https://github.com/Privex/eos-python


**Option 2 - Clone and install manually**

.. code-block:: bash

    # Clone the repository from Github
    git clone https://github.com/Privex/eos-python
    cd eos-python

    # RECOMMENDED MANUAL INSTALL METHOD
    # Use pip to install the source code
    pip3 install .

    # ALTERNATIVE MANUAL INSTALL METHOD
    # If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
    python3 setup.py install
