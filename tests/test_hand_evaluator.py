from app.game.hand_evaluator import *

def test_royal_flush_1():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '10'), Card('♥️', 'J'), Card('♥️', 'Q'),
                  Card('♦️', '7'), Card('♥️', 'A')]
    pocket_cards = [Card('♥️', 'K'), Card('♣️', '7')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.ROYAL_FLUSH,
        highest_in_hand_value=14,
        kicker_value=7)

def test_royal_flush_2():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '10'), Card('♥️', 'J'), Card('♥️', 'Q'),
                  Card('♥️', 'A'), Card('♥️', 'K')]
    pocket_cards = [Card('♣️', '8'), Card('♣️', '7')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.ROYAL_FLUSH,
        highest_in_hand_value=14,
        kicker_value=8)

def test_straight_flush1():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '10'), Card('♥️', 'J'), Card('♥️', 'Q'),
                  Card('♣️', '2'), Card('♥️', 'K')]
    pocket_cards = [Card('♣️', '8'), Card('♥️', '9')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.STRAIGHT_FLUSH,
        highest_in_hand_value=13,
        kicker_value=8)

def test_four_of_a_kind():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '10'), Card('♣️', '10'), Card('♠️', '10'),
                  Card('♣️', '2'), Card('♥️', '2')]
    pocket_cards = [Card('♦️', '10'), Card('♥️', 'K')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.FOUR_OF_A_KIND,
        highest_in_hand_value=10,
        kicker_value=13)

def test_full_house():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'A'), Card('♣️', 'A'), Card('♠️', 'A'),
                  Card('♣️', '2'), Card('♥️', '3')]
    pocket_cards = [Card('♦️', '2'), Card('♥️', 'K')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.FULL_HOUSE,
        highest_in_hand_value=14,
        highest_in_hand_value_2=2,
        kicker_value=13)

def test_flush():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'J'), Card('♥️', '2'), Card('♥️', '8'),
                  Card('♣️', '4'), Card('♥️', '3')]
    pocket_cards = [Card('♣️', '2'), Card('♥️', '10')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.FLUSH,
        highest_in_hand_value=11,
        kicker_value=2)

def test_straight_1():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'K'), Card('♣️', '9'), Card('♥️', '8'),
                  Card('♣️', '6'), Card('♥️', '7')]
    pocket_cards = [Card('♣️', 'Q'), Card('♥️', '10')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.STRAIGHT,
        highest_in_hand_value=10,
        kicker_value=12)

def test_straight_2():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '2'), Card('♣️', '6'), Card('♥️', '7'),
                  Card('♣️', '8'), Card('♥️', '9')]
    pocket_cards = [Card('♣️', '4'), Card('♥️', '10')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.STRAIGHT,
        highest_in_hand_value=10,
        kicker_value=4)

def test_three_of_a_kind():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'A'), Card('♣️', 'K'), Card('♥️', 'K'),
                  Card('♣️', '6'), Card('♥️', '7')]
    pocket_cards = [Card('♦️', 'K'), Card('♥️', '10')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.THREE_OF_A_KIND,
        highest_in_hand_value=13,
        kicker_value=10)

def test_two_pairs():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', '2'), Card('♣️', '4'), Card('♥️', '6'),
                  Card('♣️', '8'), Card('♥️', '4')]
    pocket_cards = [Card('♦️', '8'), Card('♥️', '3')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.TWO_PAIRS,
        highest_in_hand_value=8,
        highest_in_hand_value_2=4,
        kicker_value=3)

def test_one_pair():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'K'), Card('♣️', '8'), Card('♥️', 'Q'),
                  Card('♣️', '2'), Card('♥️', '7')]
    pocket_cards = [Card('♦️', 'K'), Card('♥️', '3')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.ONE_PAIR,
        highest_in_hand_value=13,
        kicker_value=3)

def test_high_card():
    evaluator = RoyalFlushEvaluator()
    comm_cards = [Card('♥️', 'K'), Card('♣️', '8'), Card('♥️', 'Q'),
                  Card('♣️', '2'), Card('♥️', '7')]
    pocket_cards = [Card('♦️', '4'), Card('♥️', '3')]
    res = evaluator.evaluate_hand(comm_cards, pocket_cards)
    assert res == EvaluatedHand(
        hand_value=HandValue.HIGH_CARD,
        highest_in_hand_value=13,
        kicker_value=4)