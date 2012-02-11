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

from urllib import quote_plus

from earwigbot.classes import BaseCommand
from earwigbot import wiki

class Command(BaseCommand):
    """Return a user's edit count."""
    name = "editcount"

    def check(self, data):
        commands = ["ec", "editcount"]
        if data.is_command and data.command in commands:
            return True
        return False

    def process(self, data):
        if not data.args:
            name = data.nick
        else:
            name = ' '.join(data.args)

        site = wiki.get_site()
        site._maxlag = None
        user = site.get_user(name)

        try:
            count = user.editcount()
        except wiki.UserNotFoundError:
            msg = "the user \x0302{0}\x0301 does not exist."
            self.connection.reply(data, msg.format(name))
            return

        safe = quote_plus(user.name())
        url = "http://toolserver.org/~soxred93/pcount/index.php?name={0}&lang=en&wiki=wikipedia"
        msg = "\x0302{0}\x0301 has {1} edits ({2})."
        self.connection.reply(data, msg.format(name, count, url.format(safe)))