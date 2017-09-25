import curses
import sys
import tweepy
from tweepy import Stream
from tweepy.streaming import StreamListener
from textblob import TextBlob
import locale
import time
import datetime
import pandas as pd
locale.setlocale(locale.LC_ALL, '')

"""
Code is based on the tutorial by Siraj Raval
Tutorial: https://www.youtube.com/watch?v=o_OZdbCzHUA
"""

consumer_key = ' your key '
consumer_secret = ' your secret '

access_token = ' your token '
access_token_secret = ' your token secret '

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

stdscr = curses.initscr()
curses.curs_set(0)
curses.echo()
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, 196, -1)  # RED
curses.init_pair(2, 35, -1)  # GREEN
stdscr.refresh()

key_word = sys.argv[1].replace("'", "")
log_file = key_word + '_' + str(time.strftime("%Y%m%d_%H%M%S")) + '.CSV'
tweets_per_period = 500


class MyListener(StreamListener):
    pos_count = 0
    neg_count = 0
    neu_count = 0

    header = ['keyword', 'overall', 'duration', 'tweets_per_sec_tps', 'negative', 'negative_per',
              'positive', 'positive_per', 'neutral', 'neutral_per']
    index = datetime.datetime.now()
    df = pd.DataFrame(index=[index], columns=header)

    height, width = stdscr.getmaxyx()
    bar = curses.newwin(4, width, 0, 0)
    bar.addstr(0, 2, 'Keyword: ' + key_word)
    bar.refresh()

    message_win = curses.newwin(height - 4, width, 4, 0)
    message_win.refresh()

    time_start = time.time()

    def clear_message_win(self):
        height, width = stdscr.getmaxyx()
        for i in range(height - 4 - 1):
            self.message_win.addstr(i, 0, ' '*(width - 1))

    def on_error(self, status):
        print(status)
        return True

    def on_status(self, status):
        analysis = TextBlob(status.text)
        height, width = stdscr.getmaxyx()

        if analysis.polarity > 0:
            self.pos_count += 1
            self.message_win.addstr(0, 0, str(status.author.screen_name.encode("utf-8")), curses.color_pair(2))
            self.message_win.addstr(0, 1, str(analysis.sentiment.__str__().encode("utf-8")), curses.color_pair(2))
            self.message_win.addstr(0, 2, str(status.text.encode("utf-8")), curses.color_pair(2))

        elif analysis.polarity < 0:
            self.neg_count += 1
            self.message_win.addstr(0, 0, str(status.author.screen_name.encode("utf-8")), curses.color_pair(1))
            self.message_win.addstr(0, 1, str(analysis.sentiment.__str__().encode("utf-8")), curses.color_pair(1))
            self.message_win.addstr(0, 2, str(status.text.encode("utf-8")), curses.color_pair(1))

        else:
            self.neu_count += 1
            self.message_win.addstr(0, 0, str(status.author.screen_name.encode("utf-8")))
            self.message_win.addstr(0, 1, str(analysis.sentiment.__str__().encode("utf-8")))
            self.message_win.addstr(0, 2, str(status.text.encode("utf-8")))

        overall = self.pos_count + self.neg_count + self.neu_count
        duration = (time.time() - self.time_start)

        neg_percent = (float(self.neg_count) / overall) * 100
        pos_percent = (float(self.pos_count) / overall) * 100
        neu_percent = (float(self.neu_count) / overall) * 100

        # monitoring
        self.bar.addstr(1, 0, ' ' * (width - 1))
        self.bar.addstr(2, 0, ' ' * (width - 1))
        self.bar.addstr(1, 2, 'Neg:' + str(self.neg_count) + ' (' + str(neg_percent)[:6] + '%)')
        self.bar.addstr(1, 25, 'Pos:' + str(self.pos_count) + ' (' + str(pos_percent)[:6] + '%)')
        self.bar.addstr(1, 48, 'Neu:' + str(self.neu_count) + ' (' + str(neu_percent)[:6] + '%)')
        self.bar.addstr(2, 2, 'Overall:' + str(overall))
        self.bar.addstr(2, 25, 'Duration:' + str(duration/60)[:10])
        self.bar.addstr(2, 48, 'tps:' + str(overall/duration))
        self.bar.addstr(4 - 1, 0, '_' * (width - 1))

        self.bar.refresh()
        self.message_win.refresh()
        self.clear_message_win()

        # store in csv
        if overall % tweets_per_period == 0: self.index = datetime.datetime.now()

        self.df.set_value(self.index, self.header[0], key_word)
        self.df.set_value(self.index, self.header[1], overall)
        self.df.set_value(self.index, self.header[2], duration/60)
        self.df.set_value(self.index, self.header[3], overall/duration)
        self.df.set_value(self.index, self.header[4], self.neg_count)
        self.df.set_value(self.index, self.header[5], neg_percent)
        self.df.set_value(self.index, self.header[6], self.pos_count)
        self.df.set_value(self.index, self.header[7], pos_percent)
        self.df.set_value(self.index, self.header[8], self.neu_count)
        self.df.set_value(self.index, self.header[9], neu_percent)

        self.df.to_csv(log_file)

        return True

try:
    twitter_stream = Stream(auth, MyListener())
    twitter_stream.filter(track=[key_word])
except KeyboardInterrupt as i:
    curses.endwin()
except Exception as e:
    print('Exeption: ' + str(e))
