from components.cards.MsgCard import MsgCard


class TestMsgCard:
    def test_msg_card_init(self):
        card = MsgCard('Example message')

        assert card.label_description.text() == 'Example message'
        assert card.layout is not None
