# Privex's EOS Python Library

[![Documentation Status](https://readthedocs.org/projects/privex-eos/badge/?version=latest)](https://privex-eos.readthedocs.io/en/latest/?badge=latest) 
[![Build Status](https://travis-ci.com/Privex/eos-python.svg?branch=master)](https://travis-ci.com/Privex/eos-python) 
[![Codecov](https://img.shields.io/codecov/c/github/Privex/eos-python)](https://codecov.io/gh/Privex/eos-python)  
[![PyPi Version](https://img.shields.io/pypi/v/privex-eos.svg)](https://pypi.org/project/privex-eos/)
![License Button](https://img.shields.io/pypi/l/privex-eos) 
![PyPI - Downloads](https://img.shields.io/pypi/dm/privex-eos)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/privex-eos) 
![GitHub last commit](https://img.shields.io/github/last-commit/Privex/privex-eos)

This is an asynchronous Python 3 library designed for EOS (may work with other EOS forks) developed and published by
[Privex Inc.](https://www.privex.io/)


```
    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Originally Developed by Privex Inc.        |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+
```

# Install

### Download and install from PyPi using pip (recommended)

```sh
pip3 install privex-eos
```

### (Alternative) Manual install from Git

**Option 1 - Use pip to install straight from Github**

```sh
pip3 install git+https://github.com/Privex/eos-python
```

**Option 2 - Clone and install manually**

```bash
# Clone the repository from Github
git clone https://github.com/Privex/eos-python
cd eos-python

# RECOMMENDED MANUAL INSTALL METHOD
# Use pip to install the source code
pip3 install .

# ALTERNATIVE MANUAL INSTALL METHOD
# If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
python3 setup.py install
```


# License

This Python module was created by [Privex Inc. of Belize City](https://www.privex.io), and licensed under the X11/MIT License.
See the file [LICENSE](https://github.com/Privex/golos-python/blob/master/LICENSE) for the license text.

**TL;DR; license:**

We offer no warranty. You can copy it, modify it, use it in projects with a different license, and even in commercial (paid for) software.

The most important rule is - you **MUST** keep the original license text visible (see `LICENSE`) in any copies.

# Example uses

```python
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

```
# Contributing

We're happy to accept pull requests, no matter how small.

Please make sure any changes you make meet these basic requirements:

 - Any code taken from other projects should be compatible with the MIT License
 - This is a new project, and as such, supporting Python versions prior to 3.4 is very low priority.
 - However, we're happy to accept PRs to improve compatibility with older versions of Python, as long as it doesn't:
   - drastically increase the complexity of the code
   - OR cause problems for those on newer versions of Python.

**Legal Disclaimer for Contributions**

Nobody wants to read a long document filled with legal text, so we've summed up the important parts here.

If you contribute content that you've created/own to projects that are created/owned by Privex, such as code or 
documentation, then you might automatically grant us unrestricted usage of your content, regardless of the open source 
license that applies to our project.

If you don't want to grant us unlimited usage of your content, you should make sure to place your content
in a separate file, making sure that the license of your content is clearly displayed at the start of the file 
(e.g. code comments), or inside of it's containing folder (e.g. a file named LICENSE). 

You should let us know in your pull request or issue that you've included files which are licensed
separately, so that we can make sure there's no license conflicts that might stop us being able
to accept your contribution.

If you'd rather read the whole legal text, it should be included as `privex_contribution_agreement.txt`.


# Thanks for reading!

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io) -** 
**prices start at as little as US$8/mo (we take cryptocurrency!)**
