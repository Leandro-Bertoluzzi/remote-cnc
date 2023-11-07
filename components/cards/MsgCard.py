from components.cards.Card import Card

class MsgCard(Card):
    def __init__(self, text, parent=None):
        super(MsgCard, self).__init__(parent)
        self.setDescription(text)
