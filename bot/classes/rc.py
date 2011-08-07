# -*- coding: utf-8  -*-

import re

class RC(object):
    """A class to store data on an event received from our IRC watcher."""
    re_color = re.compile("\x03([0-9]{1,2}(,[0-9]{1,2})?)?")
    re_edit = re.compile("\A\[\[(.*?)\]\]\s(.*?)\s(http://.*?)\s\*\s(.*?)\s\*\s(.*?)\Z")
    re_log = re.compile("\A\[\[(.*?)\]\]\s(.*?)\s\*\s(.*?)\s\*\s(.*?)\Z")

    def __init__(self, msg):
        self.msg = msg

    def parse(self):
        """Parse a recent change event into some variables."""
        # Strip IRC color codes; we don't want or need 'em:
        self.msg = self.re_color.sub("", self.msg).strip()
        msg = self.msg
        self.is_edit = True

        # Flags: 'M' for minor edit, 'B' for bot edit, 'create' for a user
        # creation log entry, etc:
        try:
            page, self.flags, url, user, comment = self.re_edit.findall(msg)[0]
        except IndexError:
            # We're probably missing the http:// part, because it's a log
            # entry, which lacks a URL:
            page, flags, user, comment = self.re_log.findall(msg)[0]
            url = "".join(("http://en.wikipedia.org/wiki/", page))

            self.is_edit = False  # This is a log entry, not edit

            # Flags tends to have extra whitespace at the end when they're
            # log entries:
            self.flags = flags.strip()

        self.page, self.url, self.user, self.comment = page, url, user, comment

    def prettify(self):
        """Make a nice, colorful message to send back to the IRC front-end."""
        flags = self.flags
        # "New <event>:" if we don't know exactly what happened:
        event_type = flags
        if "N" in flags:
            event_type = "page"  # "New page:"
        elif flags == "delete":
            event_type = "deletion"  # "New deletion:"
        elif flags == "protect":
            event_type = "protection"  # "New protection:"
        elif flags == "create":
            event_type = "user"  # "New user:"
        if self.page == "Special:Log/move":
            event_type = "move"  # New move:
        else:
            event_type = "edit"  # "New edit:"
            if "B" in flags:
                # "New bot edit:"
                event_type = "bot {}".format(event_type)
            if "M" in flags:
                # "New minor edit:" OR "New minor bot edit:"
                event_type = "minor {}".format(event_type)

        # Example formatting:
        # New edit: [[Page title]] * User name * http://en... * edit summary
        if self.is_edit:
            return "".join(("\x02New ", event_type, "\x0F: \x0314[[\x0307",
                            self.page, "\x0314]]\x0306 *\x0303 ", self.user,
                            "\x0306 *\x0302 ", self.url, "\x0306 *\x0310 ",
                            self.comment))

        return "".join(("\x02New ", event_type, "\x0F: \x0303", self.user,
                        "\x0306 *\x0302 ", self.url, "\x0306 *\x0310 ",
                        self.comment))
