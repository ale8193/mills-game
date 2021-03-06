from .. import MillsGame
from ..game_utils import *
from .delete_strategy import *

"""This file contains the heuristics of the game
For example:
Heuristic that looks at the number of pieces and the potential mills
that could be formed

This function (eval_fun) return a value that can be used by alpha beta algotithm
"""


def filter_phase1(state):
    """
    questa funzione prende in ingresso lo stato e restutuisce le mosse migliori per la fase 1
    (con punteggio più alto)
    :param state:
    :return:
    """

    adjacent_weight = 3
    couple = 2
    tris_weight = 20
    double_game = 8
    block_double_game = 10
    block_piece_weight = 1.5
    block_tris = 15
    mine_block_piece_weight = -1

    num_moves_to_return = 7

    player = state.to_move
    opponent = "B" if player == "W" else "W"

    # se nella fase 1 stiamo posizionando l'ultima pedina devo per forza fare tris se ne ho la possibilità
    if (player == 'W' and state.w_no_board == 1) or (player == 'B' and state.b_no_board == 1):
        tris_weight = 100

    moves = []

    if state.w_board == 0 and state.b_board == 0:
        return [tuple((-1, 4, -1))]

    possible_moves = state.moves

    for move in possible_moves:
        # inizialmente non ho vantaggi con questa mossa
        value = 0

        # qua calcoliamo quanti adiacenti liberi ha la mossa corrente
        adjacent = adjacent_locations(move)
        adjacent = remove_moves_occupied(state, adjacent)
        value += len(adjacent) * adjacent_weight

        # valutiamo se la mosse corrente ci porta a fare un tris
        if check_tris(state.board, -1, move, player):
            value += tris_weight

        # valuto se blocco un futuro tris dell'avversario
        if check_tris(state.board, -1, move, opponent):
            value += block_tris

        # valuto se facciamo un doppio gioco o coppia
        check_couples_num = check_couples(state, move, player)
        if check_couples_num == 2:
            if (opponent == 'W' and state.w_no_board > 1) or (opponent == 'B' and state.b_no_board > 1):
                value += check_couples_num * double_game
        else:
            value += check_couples_num * couple

        # valuto se blocchiamo un doppio gioco
        if check_double_game(state, move, opponent):
            value += block_double_game

        # valuto se blocco delle pedine avversarie
        pieces_blocked = block_pieces(state, move, player)
        value += pieces_blocked * block_piece_weight

        # valuto se blocco delle mie pedine (in questo caso la mossa sarà PENALIZZATA)
        mine_pieces_blocked = block_pieces(state, move, opponent)
        value += mine_pieces_blocked * mine_block_piece_weight

        # aggiungo la mossa alle mosse da restituire
        moves.append(tuple((move, value)))

    moves = sorted(moves, key=lambda x: (-x[1], x[0]))
    # print("Mosse calcolate in fase 1 " + str(moves))
    moves = moves[0:num_moves_to_return]

    moves_to_return = []
    for move in moves:
        has_to_delete = check_tris(state.board, -1, move[0], player)
        # print(has_to_delete)
        if has_to_delete:
            to_delete = delete_pieces_phase1(state, move[0])
            # print(has_to_delete, to_delete)

        moves_to_return.append(tuple((-1, move[0], to_delete[0] if has_to_delete else -1)))

    return moves_to_return if len(moves_to_return) > 0 else state.moves


def filter_phase2(state):
    """
    questa funzione prende in ingresso lo stato e restutuisce le mosse migliori per la fase 2
    ( con punteggio più alto)
    :param state:
    :return:
    """
    moves = []

    player_will_tris = 15
    player_tris_trick = 7
    player_couple = 2
    player_double_game = 5
    opponent_tris_will_unlock = -5

    num_moves_to_return = 3

    player = state.to_move
    opponent = "B" if player == "W" else "W"

    possible_moves = can_move(state, player)

    all_board_tris = all_tris_on_board(state)
    player_tris = all_board_tris[player]
    opponent_tris = all_board_tris[opponent]

    for move in possible_moves:
        # inizialmente non ho vantaggi con questa mossa
        value = 0

        # valuto se muovendomi faccio un tris
        if check_tris(state.board, move[0], move[1], player):
            value += player_will_tris

        # valutare se facendo questa mossa libero una tris bloccato avversario (punteggio negativo)
        if unlock_opponent_tris_trick(opponent_tris, move[0]):
            value += opponent_tris_will_unlock

        # valutare se muovendomi creo una coppia o un doppio gioco
        # LO VALUTA L'ALGORITMO fare coppia e basta non è sufficente in fase due, ha senso se facendo coppia, il turno dopo posso fare tris
        check_couples_num = check_couples_phase_two(state, move[0], move[1], player)
        if check_couples_num == 2:
            value += check_couples_num * player_double_game  # gli do un valore basso il doppio gioco è importante nella fase 1, meno nella 2
        else:
            value += check_couples_num * player_couple

        # se ho fatto un tris e posso fare il trick di fare tris ogni due mosse
        if move_in_player_tris(state.board, player_tris, move[0], opponent):
            value += player_tris_trick

        # aggiungo la mossa alla lista
        moves.append(tuple((move[0], move[1], value)))

    # alla fine ordinare le mosse sencondo il value in maniere decrescente e poi se il numero di mosse è sotto una
    # certa soglia le restituisco tutte altrimenti taglio solo ad N mosse

    moves = sorted(moves, key=lambda x: (-x[2], x[1], x[0]))
    if len(moves) > num_moves_to_return:
        moves = moves[0:num_moves_to_return]

    moves_to_return = []
    for move in moves:
        has_to_delete = check_tris(state.board, move[0], move[1], player)
        if has_to_delete:
            to_delete = delete_pieces_phase2(state, move)

        moves_to_return.append(tuple((move[0], move[1], to_delete[0] if has_to_delete else -1)))

    return moves_to_return if len(moves_to_return) > 0 else possible_moves


def filter_phase3(state):
    """
    questa funzione prende in ingresso lo stato e restutuisce le mosse migliori per la fase 3
    (con punteggio più alto)
    :param game:
    :param state:
    :return:
    """
    moves = []

    player_will_tris = 20
    player_couple_game = 2
    opponent_will_tris = 25
    piece_to_not_move = 15
    player_couple_game_possible_muvment = 5

    num_moves_to_return = 2

    player = state.to_move
    opponent = "B" if player == "W" else "W"

    possible_moves = state.moves
    p_pieces = player_pieces(state, player)

    # guardo quale delle mie pedine di partenza non devo muovere
    old_pieces = []
    for piece in p_pieces:
        value = 0

        # controllo se muovendo la pedina l'avversario farà tris
        if opponent == 'W' and state.w_board == 3:
            # W è in fase 3
            if check_tris(state.board, -1, piece, opponent):
                value += piece_to_not_move
        elif opponent == 'B' and state.b_board == 3:
            # B è in fase 3
            if check_tris(state.board, -1, piece, opponent):
                value += piece_to_not_move
        else:
            # il opponent è in fase 2
            if move_block_tris_phase_3(state, piece, opponent):
                value += piece_to_not_move

        # controllo se la pedina che voglio muovere fa coppia
        couples_with_piece = check_couples(state, piece, player, True)
        value += couples_with_piece * player_couple_game_possible_muvment

        old_pieces.append(tuple((piece, value)))

    for move in possible_moves:
        # inizialmente non ho vantaggi con questa mossa
        value = 0

        # valuto se muovendomi faccio un tris
        if check_tris(state.board, -1, move, player):
            value += player_will_tris

        # valutare se l'avversario sta per fare tris
        if opponent == 'W' and state.w_board == 3:
            # W è in fase 3
            if check_tris(state.board, -1, move, opponent):
                value += opponent_will_tris

        elif opponent == 'B' and state.b_board == 3:
            # B è in fase 3
            if check_tris(state.board, -1, move, opponent):
                value += opponent_will_tris

        else:
            # L'opponent è in fase 2
            if move_block_tris_phase_3(state, move, opponent):
                value += opponent_will_tris

        # valutare se muovendomi creo un doppio gioco
        check_couples_num = check_couples(state, move, player)
        value += check_couples_num * player_couple_game

        # aggiungo la mossa alla lista
        moves.append(tuple((-1, move, value)))

    # alla fine ordinare le mosse sencondo il value in maniere decrescente e poi se il numero di mosse è sotto una
    # certa soglia le restituisco tutte altrimenti taglio solo ad N mosse

    moves = sorted(moves, key=lambda x: (-x[2], x[1], x[0]))

    if len(moves) > num_moves_to_return:
        moves = moves[0:num_moves_to_return]

    new_moves = []
    for old_position in old_pieces:
        for move in moves:
            new_moves.append(tuple((old_position[0], move[1], move[2] - old_position[1])))

    new_moves = sorted(new_moves, key=lambda x: (-x[2], x[1], x[0]))

    moves_to_return = []
    for move in new_moves:
        has_to_delete = check_tris(state.board, move[0], move[1], player)
        if has_to_delete:
            to_delete = delete_pieces_phase3(state)

        moves_to_return.append(tuple((move[0], move[1], to_delete[0] if has_to_delete else -1)))

    return moves_to_return if len(moves_to_return) > 0 else possible_moves
