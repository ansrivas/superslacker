# Superslacker

Superslacker is a supervisor "event listener" that sends events from processes that run under [supervisor](http://supervisord.org) to [Slack](https://slack.com). When `rocketpy` receives an event, it sends a message notification to a configured `Slack` channel.

`rocketpy` uses [Slacker](https://github.com/os/slacker) full-featured Python interface for the Slack API.

## Installation

```
pip install rocketpy
```

## Command-Line Syntax

```bash
$ rocketpy [-t token] [-c channel] [-n hostname] [-w webhook] [-a attachment]
```

### Options

```-t TOKEN, --token=TOKEN```

Post a message to Slack using Slack Web API. In order to be able to send messages to Slack, you need to generate your `token` by registering your application. More info can be found [here](https://api.slack.com/web)

```-c CHANNEL, --channel=CHANNEL```

`#channel` to fill with your crash messages.

```-n HOSTNAME, --hostname=HOSTNAME```

Name or identificator of the machine where the events are been generated. This goes in the event message.

```-w WEBHOOK, --webhook=WEBHOOK```

Post a message to Slack using Slack Incoming WebHook. In order to be able to send messages to Slack, you need to configure an `Incoming WebHook` for your Slack account. More info can be found [here](https://api.slack.com/incoming-webhooks)

```-a ATTACHMENT, --attachment=ATTACHMENT```

Add text attachment to message. Attachment will have red color border along the left side.


## Notes

:ghost: gonna be used as an icon for the message and `rocketpy` as a username.


## Configuration
An `[eventlistener:x]` section must be placed in `supervisord.conf` in order for `rocketpy` to do its work. See the “Events” chapter in the Supervisor manual for more information about event listeners.

The following example assume that `rocketpy` is on your system `PATH`.


```
[eventlistener:rocketpy]
command=rocketpy --token="slacktoken-slacktoken-slacktoken" --channel="#notifications" --hostname="HOST"
events=PROCESS_STATE,TICK_60
```

If using webhook:
```
[eventlistener:rocketpy]
command=rocketpy --webhook="https://complete-webhook-string/" --channel="#notifications"
events=PROCESS_STATE,TICK_60
```
