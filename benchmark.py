#!/usr/bin/env python3
"""
Benchmarks the EOS Async library by attempting to load :attr:`.BLOCK_COUNT` blocks using
:meth:`.Api.get_block_range`.


**Copyright**::

    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Privex EOS Python API                      |
    |        License: X11 / MIT                         |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+
    

"""
import asyncio
import time
from privex.helpers import env_int
from privex.loghelper import LogHelper

from privex.eos.lib import Api

BLOCK_COUNT = env_int('BLOCK_COUNT', 500)

LogHelper('privex.eos').add_console_handler()


async def main():
    api = Api()
    start_time = time.time()
    info = await api.get_info()
    head_block = info['head_block_num']
    res = await api.get_block_range(head_block - BLOCK_COUNT, head_block)
    end_time = time.time()
    completed_in = round(end_time - start_time, 3)
    blocks_loaded = len(res.keys())
    bps = blocks_loaded / completed_in
    print(f"Loaded {blocks_loaded} blocks in {completed_in} seconds.")
    print(f"Speed: {bps} blocks per second / {bps*60} blocks per minute / {bps * 60 * 60} blocks per hour.")


asyncio.run(main())

