# -*- coding: utf-8  -*-
#
# Copyright (C) 2009-2012 by Ben Kurtovic <ben.kurtovic@verizon.net>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
EarwigBot's Main Module

The core is essentially responsible for starting the various bot components
(irc, scheduler, etc) and making sure they are all happy. An explanation of the
different components follows:

EarwigBot has three components that can run independently of each other: an IRC
front-end, an IRC watcher, and a wiki scheduler.
* The IRC front-end runs on a normal IRC server and expects users to interact
  with it/give it commands.
* The IRC watcher runs on a wiki recent-changes server and listens for edits.
  Users cannot interact with this part of the bot.
* The wiki scheduler runs wiki-editing bot tasks in separate threads at
  user-defined times through a cron-like interface.

There is a "priority" system here:
1. If the IRC frontend is enabled, it will run on the main thread, and the IRC
   watcher and wiki scheduler (if enabled) will run on separate threads.
2. If the wiki scheduler is enabled, it will run on the main thread, and the
   IRC watcher (if enabled) will run on a separate thread.
3. If the IRC watcher is enabled, it will run on the main (and only) thread.
Else, the bot will stop, as no components are enabled.
"""

import logging
import threading
import time

from earwigbot import frontend
from earwigbot import tasks
from earwigbot import watcher
from earwigbot.config import config

logger = logging.getLogger("earwigbot")
f_conn = None
w_conn = None

def irc_watcher(f_conn=None):
    """Function to handle the IRC watcher as another thread (if frontend and/or
    scheduler is enabled), otherwise run as the main thread."""
    global w_conn
    while 1:  # restart the watcher component if it breaks (and nothing else)
        w_conn = watcher.get_connection()
        w_conn.connect()
        try:
            watcher.main(w_conn, f_conn)
        except:
            logger.exception("Watcher had an error")
        time.sleep(5)  # sleep a bit before restarting watcher
        logger.warn("Watcher has stopped; restarting component")

def wiki_scheduler():
    """Function to handle the wiki scheduler as another thread, or as the
    primary thread if the IRC frontend is not enabled."""
    while 1:
        time_start = time.time()
        now = time.gmtime(time_start)

        tasks.schedule(now)

        time_end = time.time()
        time_diff = time_start - time_end
        if time_diff < 60:  # sleep until the next minute
            time.sleep(60 - time_diff)

def irc_frontend():
    """If the IRC frontend is enabled, make it run on our primary thread, and
    enable the wiki scheduler and IRC watcher on new threads if they are
    enabled."""
    global f_conn
    logger.info("Starting IRC frontend")
    f_conn = frontend.get_connection()
    frontend.startup(f_conn)

    if "wiki_schedule" in config.components:
        logger.info("Starting wiki scheduler")
        tasks.load()
        t_scheduler = threading.Thread(target=wiki_scheduler)
        t_scheduler.name = "wiki-scheduler"
        t_scheduler.daemon = True
        t_scheduler.start()

    if "irc_watcher" in config.components:
        logger.info("Starting IRC watcher")
        t_watcher = threading.Thread(target=irc_watcher, args=(f_conn,))
        t_watcher.name = "irc-watcher"
        t_watcher.daemon = True
        t_watcher.start()

    frontend.main()

    if "irc_watcher" in config.components:
        w_conn.close()
    f_conn.close()

def main():
    if "irc_frontend" in config.components:
        # Make the frontend run on our primary thread if enabled, and enable
        # additional components through that function
        irc_frontend()

    elif "wiki_schedule" in config.components:
        # Run the scheduler on the main thread, but also run the IRC watcher on
        # another thread iff it is enabled
        logger.info("Starting wiki scheduler")
        tasks.load()
        if "irc_watcher" in enabled:
            logger.info("Starting IRC watcher")
            t_watcher = threading.Thread(target=irc_watcher)
            t_watcher.name = "irc-watcher"
            t_watcher.daemon = True
            t_watcher.start()
        wiki_scheduler()

    elif "irc_watcher" in config.components:
        # The IRC watcher is our only enabled component, so run its function
        # only and don't worry about anything else:
        logger.info("Starting IRC watcher")
        irc_watcher()

    else:  # Nothing is enabled!
        logger.critical("No bot parts are enabled; stopping")
        exit(1)
