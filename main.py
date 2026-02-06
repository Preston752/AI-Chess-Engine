# /// script
# dependencies = [
#   "chess",
# ]
# ///

import asyncio
import pygame
import chess
import random
import os

async def main():

    pygame.init()
    #pygame.mixer.init()

    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)


    WIDTH = 480
    HEIGHT = 480
    SQUARE = WIDTH // 8
    PALETTE_HEIGHT = 100
    TOTAL_HEIGHT = HEIGHT + PALETTE_HEIGHT

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("0rion | Press \"i\" for more info")

    board = chess.Board()
    clock = pygame.time.Clock()
    play_sound = False
    computer_thinking = False
    computer_move_time = 0
    COMPUTER_DELAY = 500  # milliseconds
    player_is_white = True
    show_info = False
    disable_show_info = False
    disable_switch = False
    pending_sound = False
    global debug_messages
    debug_messages = []
    
    # Debug mode variables
    debug_mode = False
    dragging_piece = None
    dragging_symbol = None

    # Promotion variables
    promotion_pending = False
    promotion_from = None
    promotion_to = None
    promotion_color = None



    # Load sound
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    move_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sounds", "move.ogg"))
    move_sound.set_volume(1.0)  # Set to full volume

    # Load piece images
    pieces = {}
    symbols = {
        "P": "wP", "N": "wN", "B": "wB", "R": "wR", "Q": "wQ", "K": "wK",
        "p": "bP", "n": "bN", "b": "bB", "r": "bR", "q": "bQ", "k": "bK",
    }

    for symbol, name in symbols.items():
        img = pygame.image.load(os.path.join(BASE_DIR, "images", f"{name}.png"))
        img = pygame.transform.scale(img, (SQUARE, SQUARE))
        pieces[symbol] = img

    selected_square = None

    def draw_board():
        colors = [(240, 217, 181), (181, 136, 99)]

        for rank in range(8):
            for file in range(8):

                draw_rank = rank
                draw_file = file

                if player_is_white is False:
                    draw_rank = 7 - rank
                    draw_file = 7 - file
                else:
                    draw_rank = rank
                    draw_file = file

                color = colors[(rank + file) % 2]

                pygame.draw.rect(
                    screen,
                    color,
                    pygame.Rect(
                        draw_file * SQUARE,
                        draw_rank * SQUARE,
                        SQUARE,
                        SQUARE
                    )
                )

    def draw_pieces():
        for square, piece in board.piece_map().items():
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            if player_is_white is False:
                draw_file = 7 - file
                draw_rank = rank
            else:
                draw_file = file
                draw_rank = 7 - rank

            screen.blit(
                pieces[piece.symbol()],
                (draw_file * SQUARE, draw_rank * SQUARE)
            )

    def mouse_to_square(pos):
        if pos[1] >= HEIGHT:  # Click is in palette area
            return None
            
        file = pos[0] // SQUARE
        rank = pos[1] // SQUARE

        if player_is_white is False:
            file = 7 - file
            rank = 7 - rank

        return chess.square(file, 7 - rank)


    def draw_info_text():
        font = pygame.font.SysFont(None, 28)

        lines = [
            'Press "b" to play as Black',
            'Press "d" to enter Debug Mode'
        ]

        total_height = len(lines) * 40
        start_y = HEIGHT // 2 - total_height // 2

        for i, line in enumerate(lines):
            text = font.render(line, True, (0, 0, 0))
            x = WIDTH // 2 - text.get_width() // 2
            y = start_y + i * 40
            screen.blit(text, (x, y))

    def draw_promotion_menu(color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pieces_order = ["Q", "R", "B", "N"]
        if color == chess.BLACK:
            pieces_order = [p.lower() for p in pieces_order]

        start_x = WIDTH // 2 - (2 * SQUARE)
        y = HEIGHT // 2 - SQUARE // 2

        for i, p in enumerate(pieces_order):
            screen.blit(
                pieces[p],
                (start_x + i * SQUARE, y)
            )

    def draw_game_over(result):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        if result == "win":
            title = "You Won!"
            color = (0, 255, 0)
        elif result == "loss":
            title = "You Lost."
            color = (255, 0, 0)
        else:
            title = "Draw"
            color = (255, 255, 0)
        
        title_font = pygame.font.SysFont(None, 72)
        title_text = title_font.render(title, True, color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(title_text, title_rect)
        
        instruction_font = pygame.font.SysFont(None, 36)
        instruction_text = instruction_font.render('Press "r" to play again', True, (255, 255, 255))
        instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        screen.blit(instruction_text, instruction_rect)

    def draw_piece_palette():
        """Draw the piece selection palette at the bottom"""
        # Background
        pygame.draw.rect(screen, (100, 100, 100), pygame.Rect(0, HEIGHT, WIDTH, PALETTE_HEIGHT))
        
        # Draw all piece types
        piece_order = ["K", "Q", "R", "B", "N", "P", "k", "q", "r", "b", "n", "p"]
        piece_size = SQUARE // 2
        padding = 10
        
        for i, symbol in enumerate(piece_order):
            x = padding + i * (piece_size + padding)
            y = HEIGHT + (PALETTE_HEIGHT - piece_size) // 2
            
            # Draw piece
            scaled_piece = pygame.transform.scale(pieces[symbol], (piece_size, piece_size))
            screen.blit(scaled_piece, (x, y))
        
        # Draw control buttons
        font = pygame.font.SysFont(None, 24)
        
        # Clear board button
        clear_rect = pygame.Rect(WIDTH - 180, HEIGHT + 10, 80, 35)
        pygame.draw.rect(screen, (200, 50, 50), clear_rect)
        clear_text = font.render("Clear", True, (255, 255, 255))
        screen.blit(clear_text, (clear_rect.x + 15, clear_rect.y + 8))
        
        # Done button
        done_rect = pygame.Rect(WIDTH - 90, HEIGHT + 10, 80, 35)
        pygame.draw.rect(screen, (50, 200, 50), done_rect)
        done_text = font.render("Done", True, (255, 255, 255))
        screen.blit(done_text, (done_rect.x + 15, done_rect.y + 8))
        
        # Toggle turn button
        turn_rect = pygame.Rect(WIDTH - 180, HEIGHT + 55, 170, 35)
        turn_color = (255, 255, 255) if board.turn == chess.WHITE else (50, 50, 50)
        pygame.draw.rect(screen, turn_color, turn_rect)
        turn_text_color = (0, 0, 0) if board.turn == chess.WHITE else (255, 255, 255)
        turn_label = font.render(f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}", True, turn_text_color)
        screen.blit(turn_label, (turn_rect.x + 25, turn_rect.y + 8))
        
        return clear_rect, done_rect, turn_rect
    
    def get_palette_piece(pos):
        """Get which piece was clicked in the palette"""
        if pos[1] < HEIGHT:
            return None
            
        piece_order = ["K", "Q", "R", "B", "N", "P", "k", "q", "r", "b", "n", "p"]
        piece_size = SQUARE // 2
        padding = 10
        
        for i, symbol in enumerate(piece_order):
            x = padding + i * (piece_size + padding)
            y = HEIGHT + (PALETTE_HEIGHT - piece_size) // 2
            
            rect = pygame.Rect(x, y, piece_size, piece_size)
            if rect.collidepoint(pos):
                return symbol
        
        return None

    def is_higher_value_piece_attacked(board):
        """Check if any of our pieces is attacked by a lower-value piece"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        computer_color = board.turn
        
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            
            # Check if it's our piece
            if piece and piece.color == computer_color:
                if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    piece_value = piece_values.get(piece.piece_type, 0)
                    
                    # Check if opponent is attacking this square
                    attackers = list(board.attackers(not computer_color, square))
                    
                    if attackers:
                        
                        # Check if any attacker is lower value
                        for attacker_sq in attackers:
                            attacker_piece = board.piece_at(attacker_sq)
                            if attacker_piece:
                                attacker_value = piece_values.get(attacker_piece.piece_type, 0)
                                
                                
                                # If attacked by lower value piece, need to move
                                if attacker_value < piece_value:
                                    return square
        
        return None

    def find_safe_square_for_piece(board, piece_square):
        """Find a safe square to move an attacked piece"""
            
        for move in board.legal_moves:
            if move.from_square == piece_square:
                # Try this move
                board.push(move)
                
                # Is the piece still under attack here?
                # After push, turn has changed, so opponent is "board.turn" now
                still_attacked = len(list(board.attackers(board.turn, move.to_square))) > 0
                
                allows_fork = False
                if not still_attacked:
                    board.pop()
                    allows_fork = would_allow_fork(board, move)
                    board.push(move)

                board.pop()
                
                
                # If not under attack, this is a safe square
                if not still_attacked:
                    return move
        
        return None
    
    def can_capture_attacking_piece(board, our_piece_square):
        """Check if we can capture the piece that's attacking our piece"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        computer_color = board.turn
        our_piece = board.piece_at(our_piece_square)
        our_value = piece_values.get(our_piece.piece_type, 0) if our_piece else 0
        
        # Find who is attacking our piece
        attackers = list(board.attackers(not computer_color, our_piece_square))
        
        best_capture = None
        best_exchange = -100
        
        for attacker_sq in attackers:
            attacker_piece = board.piece_at(attacker_sq)
            attacker_value = piece_values.get(attacker_piece.piece_type, 0) if attacker_piece else 0
            
            # Can we capture this attacker?
            for move in board.legal_moves:
                if move.to_square == attacker_sq:
                    capturer = board.piece_at(move.from_square)
                    capturer_value = piece_values.get(capturer.piece_type, 0) if capturer else 0
                    
                    # Check if capturing wins the exchange
                    board.push(move)
                    
                    can_recapture = any(
                        enemy_move.to_square == attacker_sq
                        for enemy_move in board.legal_moves
                    )
                    
                    board.pop()
                    
                    # Calculate exchange value
                    if not can_recapture:
                        # Free capture of attacker
                        exchange_value = attacker_value
                    else:
                        # We take their attacker, they take our capturer
                        exchange_value = attacker_value - capturer_value
                    
                    # If this wins material, consider it
                    if exchange_value > best_exchange:
                        best_exchange = exchange_value
                        best_capture = move
        
        # Return the best capture if it wins material
        if best_exchange > 0:
            return best_capture
        
        return None

    def would_hang_piece(board, move):
        """Check if making this move would hang a piece (the moved piece OR other pieces)"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        # Make the move temporarily
        board.push(move)
        
        opponent_color = board.turn
        our_color = not opponent_color
        
        hanging = False
        
        # Check ALL our pieces to see if any are now hanging
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            
            if piece and piece.color == our_color:
                # Is this piece attacked?
                attackers = list(board.attackers(opponent_color, square))
                
                if len(attackers) > 0:
                    # It's attacked - is it defended?
                    defenders = list(board.attackers(our_color, square))
                    
                    if len(defenders) == 0:
                        # Attacked and undefended - hanging!
                        hanging = True
                        break
                    else:
                        # Defended - but can opponent win the exchange?
                        piece_value = piece_values[piece.piece_type]
                        
                        # Find lowest value attacker
                        min_attacker_value = 10
                        for attacker_sq in attackers:
                            attacker = board.piece_at(attacker_sq)
                            if attacker:
                                min_attacker_value = min(min_attacker_value, piece_values[attacker.piece_type])
                        
                        # If opponent can capture with lower value piece, it's bad
                        if min_attacker_value < piece_value:
                            hanging = True
                            break
        
        board.pop()
        return hanging
    
    def find_hanging_piece(board):
        """Find opponent pieces that can be captured profitably"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        best_capture = None
        best_value = -100
        
        for move in board.legal_moves:
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                
                if victim and attacker:
                    victim_value = piece_values.get(victim.piece_type, 0)
                    attacker_value = piece_values.get(attacker.piece_type, 0)
                    
                    # Make the capture
                    board.push(move)
                    
                    # Can opponent recapture?
                    can_recapture = any(
                        enemy_move.to_square == move.to_square
                        for enemy_move in board.legal_moves
                    )
                    
                    board.pop()
                    
                    # Calculate the exchange value
                    if not can_recapture:
                        # Free capture - take the victim value
                        exchange_value = victim_value
                    else:
                        # They can recapture - we win if victim > attacker
                        exchange_value = victim_value - attacker_value
                    
                    # Take it if we win material (positive exchange)
                    if exchange_value > best_value:
                        best_value = exchange_value
                        best_capture = move
        
        # Only return captures that win material
        if best_value > 0:
            return best_capture
        return None
    
    def would_allow_opponent_mate(board, move):
        """Check if making this move would allow opponent to mate us in 1"""
        # Make our move
        board.push(move)
        
        # Now it's opponent's turn - can they mate us?
        opponent_can_mate = False
        
        for opp_move in board.legal_moves:
            board.push(opp_move)
            if board.is_checkmate():
                opponent_can_mate = True
                board.pop()
                break
            board.pop()
        
        board.pop()  # Undo our move
        return opponent_can_mate
    
    def can_opponent_checkmate(board):
        """Check if opponent has a checkmate in one move"""
        
        # Temporarily give opponent the turn
        original_turn = board.turn
        board.turn = not original_turn
        
        has_mate = False
        mate_move = None
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                has_mate = True
                mate_move = move.uci()
                board.pop()
                break
            board.pop()
        
        # Restore our turn
        board.turn = original_turn
        
        if has_mate:
            debug_messages.append(f"Opponent has mate with: {mate_move}")
        else:
            debug_messages.append("No opponent mate found")
        
        return has_mate
    
    def leads_to_material_loss(board, move):
        """Check if this move results in net material loss after best play"""
        global debug_messages
        
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        debug_messages.append(f"Checking {move.uci()}")
        
        # Make the move
        board.push(move)
        
        # Find the best capture opponent can make
        best_opponent_gain = 0
        
        for opp_move in board.legal_moves:
            if board.is_capture(opp_move):
                victim = board.piece_at(opp_move.to_square)
                if victim:
                    victim_value = piece_values.get(victim.piece_type, 0)
                    attacker = board.piece_at(opp_move.from_square)
                    attacker_value = piece_values.get(attacker.piece_type, 0) if attacker else 0
                    
                    # Opponent captures our piece
                    board.push(opp_move)
                    
                    # Can WE recapture? And is our recapture worth it?
                    best_our_recapture_gain = 0
                    for our_recap in board.legal_moves:
                        if our_recap.to_square == opp_move.to_square:
                            our_recapturing_piece = board.piece_at(our_recap.from_square)
                            if our_recapturing_piece:
                                our_recapturer_value = piece_values.get(our_recapturing_piece.piece_type, 0)
                                
                                # We gain the attacker's piece value
                                # Net for us: gain attacker_value, lose our_recapturer_value if they can recapture
                                board.push(our_recap)
                                
                                they_can_recapture = any(
                                    their_move.to_square == opp_move.to_square
                                    for their_move in board.legal_moves
                                )
                                
                                board.pop()
                                
                                if they_can_recapture:
                                    # We trade: lose our_recapturer_value, gain attacker_value
                                    recapture_gain = attacker_value - our_recapturer_value
                                else:
                                    # We win their piece for free
                                    recapture_gain = attacker_value
                                
                                best_our_recapture_gain = max(best_our_recapture_gain, recapture_gain)
                    
                    # Net material change from opponent's perspective
                    # They capture victim_value, we recapture and gain best_our_recapture_gain
                    net_loss = victim_value - best_our_recapture_gain
                    
                    board.pop()
                    
                    debug_messages.append(f"  {opp_move.uci()}: lose {victim_value}, recapture gain {best_our_recapture_gain}, net {net_loss}")
                    
                    if net_loss > best_opponent_gain:
                        best_opponent_gain = net_loss
        
        board.pop()
        
        debug_messages.append(f"  Total loss: {best_opponent_gain}")
        
        return best_opponent_gain > 0
    
    def draw_debug():
        global debug_messages
        font = pygame.font.SysFont(None, 20)
        y = 10
        
        # Only show last 20 messages
        for msg in debug_messages[-20:]:
            text = font.render(msg, True, (255, 0, 0))
            screen.blit(text, (10, y))
            y += 20

    def exposes_piece_to_attack(board, move):
        """Check if moving a piece exposes another piece to capture"""
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        from_square = move.from_square
        
        # Make the move
        board.push(move)
        
        opponent_color = board.turn
        our_color = not opponent_color
        
        # Check if any of our pieces are now attacked and weren't before
        exposes = False
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            
            if piece and piece.color == our_color:
                # Is this piece now attacked by opponent?
                attackers = list(board.attackers(opponent_color, square))
                
                if attackers:
                    defenders = list(board.attackers(our_color, square))
                    piece_value = piece_values.get(piece.piece_type, 0)
                    
                    # Find if opponent can win this exchange
                    min_attacker_value = min(
                        piece_values.get(board.piece_at(sq).piece_type, 0)
                        for sq in attackers if board.piece_at(sq)
                    )
                    
                    # Losing exchange if attacker is worth less
                    if len(defenders) == 0 or min_attacker_value < piece_value:
                        # Was this piece safe BEFORE the move?
                        board.pop()
                        was_attacked_before = len(list(board.attackers(opponent_color, square))) > 0
                        board.push(move)
                        
                        # If it wasn't attacked before but is now, we exposed it
                        if not was_attacked_before:
                            exposes = True
                            break
        
        board.pop()
        return exposes
    
    def would_allow_fork(board, move):
        """Check if this move allows opponent to fork two of our pieces next turn"""
        global debug_messages
        
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        # Make our move
        board.push(move)
        
        # Check all opponent's possible moves
        for opp_move in board.legal_moves:
            # Make opponent's move
            board.push(opp_move)
            
            # From this new square, what can the opponent's piece attack?
            attacking_piece_square = opp_move.to_square
            attacked_squares = list(board.attacks(attacking_piece_square))
            
            # Count how many of OUR valuable pieces are attacked from this square
            our_pieces_attacked = []
            for attacked_sq in attacked_squares:
                piece = board.piece_at(attacked_sq)
                if piece and piece.color == board.turn:  # Our pieces (turn flipped twice)
                    if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                        our_pieces_attacked.append((attacked_sq, piece_values.get(piece.piece_type, 0)))
            
            # If 2+ valuable pieces attacked, it's a fork!
            if len(our_pieces_attacked) >= 2:
                # Check if both pieces are worth more than the forking piece
                forking_piece = board.piece_at(attacking_piece_square)
                forking_value = piece_values.get(forking_piece.piece_type, 0) if forking_piece else 0
                
                # Sort by value to get the two most valuable pieces
                our_pieces_attacked.sort(key=lambda x: x[1], reverse=True)
                
                # If we'd lose at least one piece worth more than the forking piece, it's bad
                if our_pieces_attacked[0][1] > forking_value:
                    debug_messages.append(f"  Fork risk: {opp_move.uci()} forks {len(our_pieces_attacked)} pieces")
                    board.pop()
                    board.pop()
                    return True
            
            board.pop()
        
        board.pop()
        return False

    def get_safe_move(board):
        """Pick a move - prioritize saving valuable pieces and don't hang pieces"""
        
        # ABSOLUTE HIGHEST PRIORITY: Checkmate in 1
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return move
            board.pop()
        
        attacked_piece = is_higher_value_piece_attacked(board)
        
        # HIGHEST PRIORITY: Prevent checkmate in 1
        if can_opponent_checkmate(board):
            debug_messages.append("MATE THREAT DETECTED!")
            
            # piece_values = {
            #     chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            #     chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
            # }
            
            # Find the mating move(s)
            original_turn = board.turn
            board.turn = not original_turn
            mating_moves = []
            for move in board.legal_moves:
                board.push(move)
                if board.is_checkmate():
                    mating_moves.append(move)
                board.pop()
            board.turn = original_turn
            
            # Find ALL moves that prevent ALL mating threats
            mate_preventing_moves = []
            
            for move in board.legal_moves:
                board.push(move)
                
                # Check if ANY of the mating moves still work
                prevents_all_mates = True
                for mate_move in mating_moves:
                    if mate_move in board.legal_moves:
                        board.push(mate_move)
                        if board.is_checkmate():
                            prevents_all_mates = False
                        board.pop()
                        if not prevents_all_mates:
                            break
                
                board.pop()
                
                if prevents_all_mates:
                    mate_preventing_moves.append(move)
            
            debug_messages.append(f"Found {len(mate_preventing_moves)} defenses")
        
        # FIRST PRIORITY: Check if any valuable piece is attacked by lower-value piece
        if attacked_piece is not None:
            # Before running away, check if we can just capture the attacker
            can_capture_attacker = can_capture_attacking_piece(board, attacked_piece)
            if can_capture_attacker and not would_allow_opponent_mate(board, can_capture_attacker):
                return can_capture_attacker
            
            safe_move = find_safe_square_for_piece(board, attacked_piece)
            if safe_move and not would_allow_opponent_mate(board, safe_move):
                return safe_move
            
        # SECOND PRIORITY: Capture hanging pieces
        # SECOND PRIORITY: Capture hanging pieces
        hanging_capture = find_hanging_piece(board)
        if hanging_capture and not would_allow_opponent_mate(board, hanging_capture) and not exposes_piece_to_attack(board, hanging_capture):
            return hanging_capture
        
        # THIRD PRIORITY: Filter out moves that would hang a piece OR allow opponent mate
        legal_moves = list(board.legal_moves)
        safe_moves = []
        
        for move in legal_moves:
            if (not would_hang_piece(board, move) and 
                not would_allow_opponent_mate(board, move) and
                not leads_to_material_loss(board, move) and
                not exposes_piece_to_attack(board, move) and
                not would_allow_fork(board, move)):
                safe_moves.append(move)
        
        # If we have safe moves, pick one (prefer captures)
        if safe_moves:
            captures = [m for m in safe_moves if board.is_capture(m)]
            if captures:
                return random.choice(captures)
            return random.choice(safe_moves)
        
        # If no completely safe moves, at least avoid giving mate
        moves_no_mate = [m for m in legal_moves if not would_allow_opponent_mate(board, m)]
        if moves_no_mate:
            return random.choice(moves_no_mate)
        
        # If no choice, pick any legal move
        return random.choice(legal_moves)

    running = True

    while running:
        #Initialize/reset game state
        pygame.display.set_caption("0rion  | Press \"i\" for more info")
        board = chess.Board()
        selected_square = None
        play_sound = False
        computer_thinking = False
        computer_move_time = 0
        COMPUTER_DELAY = 500
        player_is_white = True
        show_info = False
        disable_show_info = False
        disable_switch = False
        promotion_pending = False
        promotion_from = None
        promotion_to = None
        promotion_color = None
        game_over = False
        game_result = None
        debug_mode = False
        dragging_piece = None
        dragging_symbol = None

        # Inner game loop
        game_running = True
        while game_running and running:
            clock.tick(60)

            # This fixes the pygbag sound problem putting the
            # sound in a fresh frame cycle.
            if pending_sound:
                move_sound.play()
                pending_sound = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    game_running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and game_over:
                        game_running = False  # Break inner loop to restart
                        break

                    if player_is_white is True:
                        if event.key == pygame.K_i and show_info == False and disable_show_info == False:
                            show_info = True
                        elif event.key == pygame.K_i and show_info == True:
                            show_info = False
                        if event.key == pygame.K_d and disable_switch == False:
                            debug_mode = True
                            show_info = False
                            pygame.display.set_caption("0rion - DEBUG MODE")
                            screen = pygame.display.set_mode((WIDTH, TOTAL_HEIGHT))
                        if event.key == pygame.K_b and disable_switch == False:
                            player_is_white = False
                            show_info = False
                            pygame.display.set_caption("0rion")
                            disable_switch = True
                            computer_thinking = True
                            computer_move_time = pygame.time.get_ticks() + COMPUTER_DELAY

                # Human move

                # Debug mode interactions
                if debug_mode and event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    
                    # Check palette buttons
                    if pos[1] >= HEIGHT:
                        palette_piece = get_palette_piece(pos)
                        if palette_piece:
                            dragging_piece = None
                            dragging_symbol = palette_piece
                        else:
                            # Check control buttons
                            clear_rect = pygame.Rect(WIDTH - 180, HEIGHT + 10, 80, 35)
                            done_rect = pygame.Rect(WIDTH - 90, HEIGHT + 10, 80, 35)
                            turn_rect = pygame.Rect(WIDTH - 180, HEIGHT + 55, 170, 35)
                            
                            if clear_rect.collidepoint(pos):
                                board = chess.Board(None)  # Clear board
                            elif done_rect.collidepoint(pos):
                                debug_mode = False
                                disable_switch = True
                                disable_show_info = True
                                pygame.display.set_caption("0rion")
                                # Validate board has kings
                                if not (board.king(chess.WHITE) and board.king(chess.BLACK)):
                                    board = chess.Board()  # Reset if invalid
                            elif turn_rect.collidepoint(pos):
                                board.turn = not board.turn
                    else:
                        # Click on board
                        square = mouse_to_square(pos)
                        piece = board.piece_at(square)
                        
                        if piece:
                            # Pick up existing piece
                            dragging_piece = square
                            dragging_symbol = piece.symbol()
                            board.remove_piece_at(square)
                        elif dragging_symbol:
                            # Place piece from palette
                            piece_type = chess.Piece.from_symbol(dragging_symbol)
                            board.set_piece_at(square, piece_type)
                            dragging_symbol = None
                
                if debug_mode and event.type == pygame.MOUSEBUTTONUP:
                    if dragging_piece is not None or dragging_symbol:
                        pos = event.pos
                        if pos[1] < HEIGHT:  # Dropped on board
                            square = mouse_to_square(pos)
                            if dragging_symbol:
                                piece_type = chess.Piece.from_symbol(dragging_symbol)
                                board.set_piece_at(square, piece_type)
                        
                        dragging_piece = None
                        dragging_symbol = None
                
                if debug_mode and event.type == pygame.MOUSEMOTION:
                    # Right click to delete
                    if pygame.mouse.get_pressed()[2]:  # Right mouse button
                        pos = event.pos
                        if pos[1] < HEIGHT:
                            square = mouse_to_square(pos)
                            board.remove_piece_at(square)

                if debug_mode:
                    continue  # Skip normal game logic

                # Promotion Selection
                if event.type == pygame.MOUSEBUTTONDOWN and promotion_pending:
                    mx, my = event.pos

                    start_x = WIDTH // 2 - (2 * SQUARE)
                    y = HEIGHT // 2 - SQUARE // 2

                    for i, piece_type in enumerate([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]):
                        rect = pygame.Rect(start_x + i * SQUARE, y, SQUARE, SQUARE)
                        if rect.collidepoint(mx, my):
                            move = chess.Move(
                                promotion_from,
                                promotion_to,
                                promotion=piece_type
                            )

                            if move in board.legal_moves:
                                board.push(move)
                                play_sound = True

                                computer_thinking = True
                                computer_move_time = pygame.time.get_ticks() + COMPUTER_DELAY

                            promotion_pending = False




                # Regular move
                if event.type == pygame.MOUSEBUTTONDOWN and not promotion_pending:
                    square = mouse_to_square(event.pos)
                    if square is None:  # Clicked in palette area
                        continue
                    piece = board.piece_at(square)

                    # No piece selected yet → select if it's your piece
                    if selected_square is None:
                        if piece and piece.color == board.turn:
                            selected_square = square

                    else:
                        selected_piece = board.piece_at(selected_square)

                        # Clicked another own piece → switch selection
                        if piece and piece.color == board.turn:
                            selected_square = square

                        else:
                            move = chess.Move(selected_square, square)

                            # Pawn promotion check
                            if selected_piece and selected_piece.piece_type == chess.PAWN:
                                if (
                                    selected_piece.color == chess.WHITE
                                    and chess.square_rank(square) == 7
                                ) or (
                                    selected_piece.color == chess.BLACK
                                    and chess.square_rank(square) == 0
                                ):
                                    promotion_pending = True
                                    promotion_from = selected_square
                                    promotion_to = square
                                    promotion_color = selected_piece.color
                                    selected_square = None
                                    continue



                            if move in board.legal_moves:
                                board.push(move) #Causes the white pieces to move visually
                                
                                pygame.display.set_caption("0rion")
                                show_info = False #Turns off info text is it is displayed.
                                disable_show_info = True #Cannot look at info screen after the first move
                                disable_switch = True #Cannot switch colors after the first move
                                
                                move_sound.play()
                                
                                computer_thinking = True
                                computer_move_time = pygame.time.get_ticks() + COMPUTER_DELAY

                                # 🔴 CRITICAL: always reset
                                selected_square = None

                    

            # Computer move
            current_time = pygame.time.get_ticks()

            if (
                computer_thinking
                and board.turn != player_is_white
                and not board.is_game_over()
                and current_time >= computer_move_time
            ):
                move = get_safe_move(board)
                board.push(move)

                pending_sound = True
                
                

                computer_thinking = False

            if board.is_game_over() and not game_over and not debug_mode:
                game_over = True
                if board.is_checkmate():
                    if board.turn == player_is_white:
                        game_result = "loss"
                    else:
                        game_result = "win"
                else:
                    game_result = "draw"


            draw_board()

            if show_info:
                draw_info_text()

            draw_pieces()
            #draw_debug()
            
            # Draw dragging piece
            if debug_mode and dragging_symbol:
                mouse_pos = pygame.mouse.get_pos()
                piece_img = pieces[dragging_symbol]
                screen.blit(piece_img, (mouse_pos[0] - SQUARE // 2, mouse_pos[1] - SQUARE // 2))
            
            if debug_mode:
                clear_rect, done_rect, turn_rect = draw_piece_palette()
            
            if promotion_pending:
                draw_promotion_menu(promotion_color)

            if game_over:
                draw_game_over(game_result)

            pygame.display.flip()


            await asyncio.sleep(0)

    pygame.quit

asyncio.run(main())