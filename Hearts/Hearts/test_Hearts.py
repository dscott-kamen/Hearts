from Hearts import Hearts
from Hand import Hand
import pytest


@pytest.fixture(scope='module')
def hearts():
    players = ['Al', 'Bob', 'Carol', 'Doug']
    hearts  = Hearts(players)
    hearts.preDealInitialization()
    return hearts

@pytest.fixture(scope='module')
def playOrder(hearts):
    return hearts.getPlayOrder(hearts.hands[0])

@pytest.fixture()
def intermediateRoundScore(hearts):
    hearts.roundScore = [2,4,6,8]
    hearts.roundPointsTaken = [0,0,0,0]

    return hearts.roundScore
    

# Test determineTrickWinner
def test_trick_winner_all_same_suit_1st_position(hearts, playOrder):
    board = Hand(inputString=("8H 6H 3H 7H"))
    assert hearts.determineTrickWinner(board, playOrder).getName() == 'Al'

def test_trick_winner_all_same_suit_4th_position(hearts, playOrder):
    board = Hand(inputString=("8H 9H 3H QH"))
    assert hearts.determineTrickWinner(board, playOrder).getName() == 'Doug'
    
def test_trick_winner_winner_lower_than_2sluffs(hearts, playOrder):
    board = Hand(inputString=("8H 9H QC KS"))
    assert hearts.determineTrickWinner(board, playOrder).getName() == 'Bob'
        
def test_trick_winner_winner_lower_than_3sluffs(hearts, playOrder):
    board = Hand(inputString=("4H 7C 8H QS"))
    assert hearts.determineTrickWinner(board, playOrder).getName() == 'Carol'
    

#Test Compute trick points
def test_compute_trick_points_no_hearts_qs(hearts):
    board = Hand(inputString=("6C 7C 4C QC"))
    assert hearts.computeTrickPoints(board) == 0

def test_compute_points_one_heart(hearts):
    board = Hand(inputString=("6C 7C 4H QC"))
    assert hearts.computeTrickPoints(board) == 1
    
def test_compute_points_four_hearts(hearts):
    board = Hand(inputString=("6H 7H 4H QH"))
    assert hearts.computeTrickPoints(board) == 4

def test_compute_trick_points_qs(hearts):
    board = Hand(inputString=("6C 7C QS QC"))
    assert hearts.computeTrickPoints(board) == 13
    
def test_compute_trick_points_jd(hearts):
    board = Hand(inputString=("6C JD 7C QC"))
    assert hearts.computeTrickPoints(board) == -10
    
def test_compute_trick_points_heart_qs_jd(hearts):
    board = Hand(inputString=("6H QS JD TH"))
    assert hearts.computeTrickPoints(board) == 5

#Test update round score 
def test_update_roundscore_score_0(hearts, intermediateRoundScore):
    hearts.updateRoundScore(hearts.hands[0], 0)
    assert hearts.roundScore == [2,4,6,8]
    assert hearts.roundPointsTaken == [0,0,0,0]
    
def test_update_roundscore_score_neg10_first_position(hearts, intermediateRoundScore):
    hearts.updateRoundScore(hearts.hands[0], -10)
    assert hearts.roundScore == [-8,4,6,8]
    assert hearts.roundPointsTaken == [0,0,0,0]

def test_update_roundscore_score_1_last_position(hearts, intermediateRoundScore):
    hearts.updateRoundScore(hearts.hands[3], 1)
    assert hearts.roundScore == [2,4,6,9]
    assert hearts.roundPointsTaken == [0,0,0,1]

def test_update_roundscore_score_neg9(hearts, intermediateRoundScore):
    hearts.updateRoundScore(hearts.hands[2], -9)
    assert hearts.roundScore == [2,4,-3,8]
    assert hearts.roundPointsTaken == [0,0,1,0]

#Test end round adjustments
def test_end_round_adjustments_multiple_score(hearts):
    hearts.roundScore = [3,5,3,5]
    hearts.roundPointsTaken = [1,1,1,1]
    hearts.updateRoundScoreWithEndRoundAdjustments()
    assert hearts.roundScore == [3,5,3,5]
    
def test_end_round_adjustment_shoot_with_jd(hearts):
    hearts.roundScore = [0,16,0,0]
    hearts.roundPointsTaken = [0,1,0,0]
    hearts.updateRoundScoreWithEndRoundAdjustments()
    assert hearts.roundScore == [26,-10,26,26]

def test_end_round_adjustment_shoot_without_jd(hearts):
    hearts.roundScore = [0,26,-10,0]
    hearts.roundPointsTaken = [0,1,0,0]
    hearts.updateRoundScoreWithEndRoundAdjustments()
    assert hearts.roundScore == [26,0,16,26]

#Test update game score
def test_update_game_score_multiple_scores(hearts):
    hearts.gameScore = [10,15,20,25]
    hearts.roundScore = [1,0,5,10]
    hearts.updateGameScore()
    assert hearts.gameScore == [11,15,25,35]
    
#Test get first player
def test_first_player_2C_in_first_hand(hearts):
    hearts.hands[0].addCardsFromString(inputString='2C 9C JC 2D 6D JD 5H 8H 9H TH QH 5S TS')
    hearts.hands[1].addCardsFromString(inputString='3C 4C TC 7D 8D 2H 3H 6H 7H 2S 7S JS QS')
    hearts.hands[2].addCardsFromString(inputString='5C 7C 3D 4D 5D TD QD KD AD 3S 4S 9S KS')
    hearts.hands[3].addCardsFromString(inputString='6C 8C QC KC AC 9D 4H JH KH AH 6S 8S AS')
    assert hearts.getFirstPlayer().getName() == 'Al'
    for hand in hearts.hands:
        hand.cards.clear()


def test_first_player_2C_in_3rd_hand(hearts):
    hearts.hands[0].addCardsFromString(inputString='5C 7C 3D 4D 5D TD QD KD AD 3S 4S 9S KS')
    hearts.hands[1].addCardsFromString(inputString='3C 4C TC 7D 8D 2H 3H 6H 7H 2S 7S JS QS')
    hearts.hands[2].addCardsFromString(inputString='2C 9C JC 2D 6D JD 5H 8H 9H TH QH 5S TS')
    hearts.hands[3].addCardsFromString(inputString='6C 8C QC KC AC 9D 4H JH KH AH 6S 8S AS')
    assert hearts.getFirstPlayer().getName() == 'Carol'
    for hand in hearts.hands:
        hand.cards.clear()
'''
Playable Cards
1) First play (13 cards) and have 2C => 2C
2) First play, no 2C should not have a heart, should not have QS
3) On lead and hearts not broken and at least one non heart, should not have heart
4) On lead and hearts not broken and all hearts, should have all cards
5) On lead and hearts broken, should have all cards
6) Not on lead and hearts not broken and has lead suit, should only have cards in suit
7) Not on lead and hearts not broken and does not have lead suit, all cards
8) Not on lead and hearts broken and has lead suit, only lead suit
9) Not on lead and hearts broken and does not have lead suit, all cards

PlayCard
1) Hearts broken, non-heart played (confirm card not in hand)
2) Hearts not broken, non-heart played (confirm flag)
3) Hearts not broken, heart played (confirm flag)

Deal
1) Confirm cards dealt

GetPlayers


getPlayOrder

initializeSeats

isGameComplete

isRoundComplete

setDealer
'''
