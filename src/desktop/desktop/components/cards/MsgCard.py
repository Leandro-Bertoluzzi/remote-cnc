from desktop.components.cards.Card import Card


class MsgCard(Card):
    def __init__(self, text: str, parent=None):
        super(MsgCard, self).__init__(parent)
        self.setDescription(text)
