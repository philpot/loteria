import random
from collections import defaultdict
from itertools import combinations
import json

# 1D indices for a 4x4 grid representing the 12 winning lines
WIN_CONFIGS = (
    (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11), (12, 13, 14, 15),  # Rows
    (0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),  # Cols
    (0, 5, 10, 15), (3, 6, 9, 12),                                 # Diags
    (5, 6, 9, 10),                                                 # Pozo
    (0, 3, 12, 15)                                                 # Corners
)

def generate_initial_tablas(k: int, n: int) -> list[list[int]]:
    total_slots = 16 * k
    base_count = total_slots // n
    remainder = total_slots % n
    
    # Build perfectly balanced deck
    deck = []
    for i in range(1, n + 1):
        deck.extend([i] * (base_count + (1 if i <= remainder else 0)))
    random.shuffle(deck)
    
    tablas: list[list[int]] = [[] for _ in range(k)]
    
    # Deal cards ensuring intra-tabla uniqueness
    for card in deck:
        valid_tablas = [t for t in tablas if len(t) < 16 and card not in t]
        if valid_tablas:
            # Append to the tabla with the least cards to keep dealing even
            min(valid_tablas, key=len).append(card)
        else:
            # Edge case: All tablas with room already have this card.
            # Force a swap with a valid card from another tabla.
            t_dest = random.choice([t for t in tablas if len(t) < 16])
            for t_src in tablas:
                if t_src is t_dest:
                    continue
                for i, c in enumerate(t_src):
                    if c not in t_dest and card not in t_src:
                        t_dest.append(c)
                        t_src[i] = card
                        break
                else:
                    continue
                break

    return tablas

def apply_tabla_state(tabla_id: int, tabla: list[int], seen_4: dict, seen_3: dict, is_adding: bool) -> int:
    delta_score = 0
    for config in WIN_CONFIGS:
        cards_4 = frozenset(tabla[i] for i in config)
        old_count = len(seen_4[cards_4])
        
        if is_adding:
            seen_4[cards_4].add(tabla_id)
        else:
            seen_4[cards_4].discard(tabla_id)
            
        new_count = len(seen_4[cards_4])
        delta_score += (max(0, new_count - 1) - max(0, old_count - 1)) * 1000
        
        for cards_3 in combinations(cards_4, 3):
            subset = frozenset(cards_3)
            old_sub_count = len(seen_3[subset])
            
            if is_adding:
                seen_3[subset].add(tabla_id)
            else:
                seen_3[subset].discard(tabla_id)
                
            new_sub_count = len(seen_3[subset])
            delta_score += (max(0, new_sub_count - 1) - max(0, old_sub_count - 1)) * 1
            
    return delta_score

def optimize_tablas(tablas: list[list[int]], max_iterations: int = 50000) -> list[list[int]]:
    seen_4 = defaultdict(set)
    seen_3 = defaultdict(set)
    current_score = 0
    
    for tabla_id, tabla in enumerate(tablas):
        current_score += apply_tabla_state(tabla_id, tabla, seen_4, seen_3, is_adding=True)
        
    print(f"Initial Conflict Score: {current_score}")
        
    iterations = 0
    while current_score > 0 and iterations < max_iterations:
        t1_idx, t2_idx = random.sample(range(len(tablas)), 2)
        c1_idx, c2_idx = random.randint(0, 15), random.randint(0, 15)
        
        card1, card2 = tablas[t1_idx][c1_idx], tablas[t2_idx][c2_idx]
        if card2 in tablas[t1_idx] or card1 in tablas[t2_idx]:
            continue
            
        step_delta = 0
        step_delta += apply_tabla_state(t1_idx, tablas[t1_idx], seen_4, seen_3, is_adding=False)
        step_delta += apply_tabla_state(t2_idx, tablas[t2_idx], seen_4, seen_3, is_adding=False)
        
        tablas[t1_idx][c1_idx] = card2
        tablas[t2_idx][c2_idx] = card1
        
        step_delta += apply_tabla_state(t1_idx, tablas[t1_idx], seen_4, seen_3, is_adding=True)
        step_delta += apply_tabla_state(t2_idx, tablas[t2_idx], seen_4, seen_3, is_adding=True)
        
        if current_score + step_delta <= current_score:
            current_score += step_delta
        else:
            # Revert state
            apply_tabla_state(t1_idx, tablas[t1_idx], seen_4, seen_3, is_adding=False)
            apply_tabla_state(t2_idx, tablas[t2_idx], seen_4, seen_3, is_adding=False)
            
            tablas[t1_idx][c1_idx] = card1
            tablas[t2_idx][c2_idx] = card2
            
            apply_tabla_state(t1_idx, tablas[t1_idx], seen_4, seen_3, is_adding=True)
            apply_tabla_state(t2_idx, tablas[t2_idx], seen_4, seen_3, is_adding=True)
            
        iterations += 1
        
        if iterations % 5000 == 0:
            print(f"Iteration {iterations}: Score = {current_score}")
            
    print(f"Final Score: {current_score} after {iterations} iterations")
    return tablas

if __name__ == "__main__":
    K_TABLAS = 50
    N_CARDS = 54
    
    print("Generating perfectly balanced pool...")
    initial_grids = generate_initial_tablas(K_TABLAS, N_CARDS)
    
    print("Optimizing constraints...")
    final_grids = optimize_tablas(initial_grids, max_iterations=100000)
    
    # Save the output to pipe into your text graphics and font mutation scripts
    with open("loteria_matrices.json", "w") as f:
        json.dump(final_grids, f, indent=2)
    print("Saved optimized layout to loteria_matrices.json")