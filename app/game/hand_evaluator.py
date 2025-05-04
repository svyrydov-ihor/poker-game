from abc import ABC, abstractmethod
from typing import List
from app.game.game_schema import EvaluatedHand, HandValue
from app.game.models import Card

class AbsHandEvaluator(ABC):
    """
    Chain of responsibility pattern for hand evaluation
    """
    def __init__(self):
        self.next_evaluator = None

    @abstractmethod
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        pass

    def group_by_suits(self, total_cards: List[Card]):
        cards = [c for c in total_cards]
        cards.sort(key=lambda c: c.suit)
        suit_groups = []
        suit_groups.append([])
        prev_suit = cards[0].suit
        i = 0
        for c in cards:
            if c.suit == prev_suit:
                suit_groups[i].append(c)
            else:
                suit_groups.append([c])
                prev_suit = c.suit
                i += 1
        return suit_groups

    def group_by_rank(self, total_cards: List[Card]):
        """
        Groups cards by rank, from highest to lowest
        """
        cards = [c for c in total_cards]
        cards.sort(key=lambda c: c.value, reverse=True)
        print(cards)
        rank_groups = []
        rank_groups.append([])
        prev_rank = cards[0].value
        i = 0
        for c in cards:
            if c.value == prev_rank:
                rank_groups[i].append(c)
            else:
                rank_groups.append([c])
                prev_rank = c.value
                i += 1
        return rank_groups

class RoyalFlushEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        suit_groups = self.group_by_suits(total_cards)

        with_5_suit_groups = [group for group in suit_groups if len(group) >= 5]

        if len(with_5_suit_groups) == 0:
            self.next_evaluator = FourOfAKindEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        with_5_suit = with_5_suit_groups[0]
        with_5_suit.sort(key=lambda c: c.value)

        if with_5_suit[-1].value == 14:
            if [c.value for c in with_5_suit] == [10, 11, 12, 13, 14]:
                highest_in_hand_value = 14
                if pocket_cards[0].value >= pocket_cards[1].value:
                    kicker_value = pocket_cards[0].value
                else:
                    kicker_value = pocket_cards[1].value
                return EvaluatedHand(
                    hand_value=HandValue.ROYAL_FLUSH,
                    highest_in_hand_value=highest_in_hand_value,
                    kicker_value=kicker_value)

        self.next_evaluator = StraightFlushEvaluator()
        return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

class StraightFlushEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        suit_groups = self.group_by_suits(total_cards)

        with_5_suit_groups = [group for group in suit_groups if len(group) >= 5]

        if len(with_5_suit_groups) == 0:
            self.next_evaluator = FourOfAKindEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        with_5_suit = with_5_suit_groups[0]
        with_5_suit.sort(key=lambda c: c.value)
        for i in range(1, len(with_5_suit)):
            if with_5_suit[i].value - with_5_suit[i-1].value != 1:
                self.next_evaluator = FourOfAKindEvaluator()
                return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.STRAIGHT_FLUSH,
            highest_in_hand_value=with_5_suit[-1].value,
            kicker_value=kicker_value)

class FourOfAKindEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        rank_groups = self.group_by_rank(total_cards)

        with_4_ranks = [group for group in rank_groups if len(group) >= 4]

        if len(with_4_ranks) == 0:
            self.next_evaluator = FullHouseEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.FOUR_OF_A_KIND,
            highest_in_hand_value=with_4_ranks[0][0].value,
            kicker_value=kicker_value)

class FullHouseEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        rank_groups = self.group_by_rank(total_cards)

        has_3_ranks = False
        has_2_ranks = False
        with_3_ranks = []
        with_2_ranks = []
        for same_rank in rank_groups:
            if len(same_rank) >= 3 and not has_3_ranks:
                with_3_ranks = same_rank
                has_3_ranks = True
                continue
            if len(same_rank) >= 2 and not has_2_ranks:
                with_2_ranks = same_rank
                has_2_ranks = True
                break

        if not has_3_ranks or not has_2_ranks:
            self.next_evaluator = FlushEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.FULL_HOUSE,
            highest_in_hand_value=with_3_ranks[0].value,
            highest_in_hand_value_2=with_2_ranks[0].value,
            kicker_value=kicker_value)

class FlushEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        suit_groups = self.group_by_suits(total_cards)

        with_5_suit = [group for group in suit_groups if len(group) >= 5]

        if len(with_5_suit) == 0:
            self.next_evaluator = StraightEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        with_5_suit[0].sort(key=lambda c: c.value, reverse=True)
        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.FLUSH,
            highest_in_hand_value=with_5_suit[0][0].value,
            kicker_value=kicker_value)

class StraightEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        total_cards.sort(key=lambda c: c.value, reverse=True)

        straight_cards = []
        straight_cards.append(total_cards[0])
        for i in range(1, len(total_cards)):
            if total_cards[i].value - total_cards[i-1].value == -1:
                straight_cards.append(total_cards[i])
            else:
                straight_cards.clear()
                straight_cards.append(total_cards[i])

        if len(straight_cards) < 5:
            self.next_evaluator = ThreeOfAKindEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.STRAIGHT,
            highest_in_hand_value=straight_cards[0].value,
            kicker_value=kicker_value)

class ThreeOfAKindEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        rank_groups = self.group_by_rank(total_cards)

        three_of_a_kind_cards = [group for group in rank_groups if len(group) == 3]

        if len(three_of_a_kind_cards) == 0:
            self.next_evaluator = TwoPairsEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.THREE_OF_A_KIND,
            highest_in_hand_value=three_of_a_kind_cards[0][0].value,
            kicker_value=kicker_value)

class TwoPairsEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        rank_groups = self.group_by_rank(total_cards)

        two_pairs_cards = [group for group in rank_groups if len(group) == 2]

        if len(two_pairs_cards) < 2:
            self.next_evaluator = OnePairEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.TWO_PAIRS,
            highest_in_hand_value=two_pairs_cards[0][0].value,
            highest_in_hand_value_2=two_pairs_cards[1][0].value,
            kicker_value=kicker_value)

class OnePairEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        rank_groups = self.group_by_rank(total_cards)

        pair_cards = [group for group in rank_groups if len(group) == 2]

        if len(pair_cards) == 0:
            self.next_evaluator = HighCardEvaluator()
            return self.next_evaluator.evaluate_hand(community_cards, pocket_cards)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.ONE_PAIR,
            highest_in_hand_value=pair_cards[0][0].value,
            kicker_value=kicker_value)

class HighCardEvaluator(AbsHandEvaluator):
    def evaluate_hand(self, community_cards: List[Card], pocket_cards: List[Card]) -> EvaluatedHand:
        total_cards = community_cards + pocket_cards
        total_cards.sort(key=lambda c: c.value, reverse=True)

        if pocket_cards[0].value >= pocket_cards[1].value:
            kicker_value = pocket_cards[0].value
        else:
            kicker_value = pocket_cards[1].value
        return EvaluatedHand(
            hand_value=HandValue.HIGH_CARD,
            highest_in_hand_value=total_cards[0].value,
            kicker_value=kicker_value)