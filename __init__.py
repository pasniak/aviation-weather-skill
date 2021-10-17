from mycroft import MycroftSkill, intent_file_handler


class FeedTheCorgi(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('corgi.the.feed.intent')
    def handle_corgi_the_feed(self, message):
        self.speak_dialog('corgi.the.feed')


def create_skill():
    return FeedTheCorgi()

