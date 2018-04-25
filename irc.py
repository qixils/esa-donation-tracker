# IRC related functionality

import ssl

import irc.bot
import irc.connection


class TwitchAnnouncer(irc.bot.SingleServerIRCBot):
    """Class to announce messages to a Twitch channel."""

    def __init__(self, username, token, channel):
        self.token = token
        self.channel = '#' + channel

        # Create IRC bot connection
        ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        server = 'irc.chat.twitch.tv'
        port = 443
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:' + token)], username, username,
                                            connect_factory=ssl_factory)

    def send_message(self, message):
        """Send a message or list of messages to the channel.

        :param message:
        :return:
        """
        self._connect()
        self.connection.join(self.channel)

        if isinstance(message, (list, tuple)):
            for m in message:
                self.connection.privmsg(self.channel, m)
        else:
            self.connection.privmsg(self.channel, message)

        self.connection.disconnect()
