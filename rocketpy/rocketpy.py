# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# Copyright (c) 2015 MTSolutions S.A.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send slack messages when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:rocketpy]
# command=python rocketpy
# events=PROCESS_STATE,TICK_60

"""
Usage: rocketpy [-t token] [-c channel] [-n hostname] [-w webhook] [-a attachment]

Options:
  -h, --help            show this help message and exit
  -t TOKEN, --token=TOKEN
                        RocketChat Token
  -c CHANNEL, --channel=CHANNEL
                        RocketChat Channel
  -w WEBHOOK, --webhook=WEBHOOK
                        RocketChat WebHook URL
  -a ATTACHMENT, --attachment=ATTACHMENT
                        RocketChat Attachment text
  -n HOSTNAME, --hostname=HOSTNAME
                        System Hostname

  -k , --insecure
                        Skip server certificate verification.
"""

import copy
import os
import sys
import requests
from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils


class RocketPy(ProcessStateMonitor):
    """."""

    process_state_events = ['PROCESS_STATE_FATAL', 'PROCESS_STATE_RUNNING',
                            'PROCESS_STATE_EXITED', 'PROCESS_STATE_STOPPED',
                            'SUPERVISOR_STATE_CHANGE']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", help="RocketChat Token")
        parser.add_option("-c", "--channel", help="RocketChat Channel")
        parser.add_option("-w", "--webhook", help="RocketChat WebHook URL")
        parser.add_option("-a", "--attachment", help="RocketChat Attachment text")
        parser.add_option("-n", "--hostname", help="System Hostname")
        parser.add_option("-k", "--insecure", action="store_false", default=True, help="Skip server certificate verification")

        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        """."""
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        """."""
        parser = cls._get_opt_parser()
        if not options.token and not options.webhook:
            parser.print_help()
            sys.exit(1)
        if options.token and options.webhook:
            parser.print_help()
            sys.exit(1)
        if not options.channel:
            parser.print_help()
            sys.exit(1)
        if not options.hostname:
            import socket
            options.hostname = socket.gethostname()

        validated = copy.copy(options)
        return validated

    @classmethod
    def get_cmd_line_options(cls):
        """."""
        return cls.validate_cmd_line_options(cls.parse_cmd_line_options())

    @classmethod
    def create_from_cmd_line(cls):
        """."""
        options = cls.get_cmd_line_options()
        if 'SUPERVISOR_SERVER_URL' not in os.environ:
            sys.stderr.write('Must run as a supervisor event listener\n')
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        """."""
        ProcessStateMonitor.__init__(self, **kwargs)
        self.channel = kwargs['channel']
        self.token = kwargs.get('token', None)
        self.now = kwargs.get('now', None)
        self.hostname = kwargs.get('hostname', None)
        self.webhook = kwargs.get('webhook', None)
        self.attachment = kwargs.get('attachment', None)
        self.insecure = kwargs.get('insecure', False)

    def get_emoji(self, eventname):
        """Get emojis based on type of message."""
        emo_keys = {
            "EXITED": ":sob:",
            "STOPPED": ":sob:",
            "FATAL": ":sob:",
            "RUNNING": ":clap:",
            "DEFAULT": ":smile:"
        }
        for key in emo_keys:
            if key in eventname:
                return emo_keys[key]
        return emo_keys["DEFAULT"]

    def get_process_state_change_msg(self, headers, payload):
        """."""
        pheaders, pdata = childutils.eventdata(payload + '\n')
        to_state = headers['eventname']
        emoji = self.get_emoji(to_state)
        msg = ('```Host             : [{host}]\nProcess        : [{processname}]\nGroupname : [{groupname}]\n'
               'Status           : [{from_state}] => [{to_state}] ```{emoji}'
               .format(host=self.hostname, to_state=headers['eventname'], emoji=emoji, **pheaders)
               )
        return msg

    def send_batch_notification(self):
        """."""
        message = self.get_batch_message()
        if message:
            self.send_message(message)

    def get_batch_message(self):
        """."""
        return {
            'token': self.token,
            'webhook': self.webhook,
            'channel': self.channel,
            'attachment': self.attachment,
            'insecure': self.insecure,
            'messages': self.batchmsgs
        }

    def post_message(self, url, data, verify):
        """Send a post request to a given webhook url."""
        with requests.Session() as sess:
            sess.post(url=url, data=data, verify=verify)

    def send_message(self, message):
        """."""
        for msg in message['messages']:
            payload = {
                'channel': message['channel'],
                'text': msg,
                'username': 'rocketpy',
                'icon_emoji': ':sos:',
                'link_names': 1,
                'attachments': [{"text": message['attachment'], "color": "danger"}],
                'mrkdwn': True,
            }
            if message['webhook']:

                self.post_message(url=message['webhook'], data=payload, verify=False if message['insecure'] else True)
                self.write_stderr("Sent notification over webhook.")
            # if message['token']:
            #     slack = Slacker(token=message['token'])
            #     slack.chat.post_message(**payload)


def main():
    """."""
    rocketpy = RocketPy.create_from_cmd_line()
    rocketpy.run()


def fatalslack():
    """."""
    rocketpy = RocketPy.create_from_cmd_line()
    rocketpy.write_stderr('fatalslack is deprecated. Please use superslack instead\n')
    rocketpy.run()


if __name__ == '__main__':
    main()
