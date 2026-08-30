# Pull Request: Lotería Tabla Generation Engine

## Overview

This PR introduces a constraint satisfaction engine to generate valid, mathematically balanced Lotería *tablas* (4x4 playing boards). Because the combinatorial space is highly constrained by the game's multiple winning configurations, standard randomized generation yields high collision rates (duplicate winning lines across different boards).

To solve this, the implementation uses a **stochastic hill-climbing algorithm with min-conflicts**, utilizing $O(1)$ stateful lookups to rapidly resolve board collisions via localized delta-scoring.

## System Constraints & Rules

The engine strictly enforces the following constraints:

1. **Intra-Tabla Uniqueness:** A single 16-card tabla can never contain duplicate cards.
2. **Perfect Distribution:** Across all $K$ tablas (e.g., $16 \times 50 = 800$ total slots), every card from the $N$-card universe (54 or 56) appears an equal number of times, with a maximum frequency difference of exactly 1.
3. **Collision Resistance (Size-4):** If 4 cards form a winning configuration on Tabla A, that exact subset of 4 cards cannot form a winning configuration on any other Tabla B.
4. **Collision Resistance (Size-3):** A softer constraint heavily penalizing any 3-card subsets of a winning line that are duplicated across multiple tablas' winning configurations.

**Winning Configurations (12 per tabla):** 4 rows, 4 columns, 2 diagonals, 1 *pozo* (center 2x2), and the 4 corners.

---

## Data Structures

### 1. `WIN_CONFIGS` (Static Geometry)

A static tuple of tuples mapping the 12 winning shapes to 1D array indices (0-15).

* **Why:** Tuples evaluate faster than lists, guarantee immutability, and abstract the 2D grid logic into flat arrays for faster iteration.

### 2. State Registries (`seen_4` and `seen_3`)

Implemented as `collections.defaultdict(set)`.

* **Keys:** `frozenset` of integers (representing the 4-card or 3-card subsets). `frozenset` is used because the physical order of the cards in a winning line does not matter. It provides immediate hashability without manual sorting.
* **Values:** A `set` of `tabla_id` integers tracking exactly which boards contain that subset.
* **Why:** Allows $O(1)$ lookups to detect collisions. If `len(seen_4[frozenset(...)]) > 1`, a collision exists.

---

## Algorithm Architecture

### Phase 1: Deterministic Initialization

Instead of picking random numbers and checking frequencies, the engine builds a "stacked deck."

1. Calculates the required total slots ($16 \times K$) and deals the $N$ integers into a 1D array, guaranteeing perfect mathematical distribution.
2. Shuffles this deck globally.
3. Deals cards sequentially into the $K$ tablas. A validation gate ensures no duplicate card is added to a single tabla. If a duplicate is drawn, it forces a targeted swap with another tabla to maintain constraints without altering global frequencies.

### Phase 2: Stochastic Optimization (Mutation Engine)

The engine calculates an initial global "Conflict Score" by heavily penalizing Size-4 collisions and lightly penalizing Size-3 collisions. It then enters a mutation loop:

1. **Targeting:** Selects two distinct tablas and one card index from each at random.
2. **Validation Gate:** Checks if swapping these two cards would break intra-tabla uniqueness. If so, aborts and selects new targets.
3. **State Extraction (Delta-Scoring):** Dynamically subtracts the current state of both tablas from the `seen_4` and `seen_3` registries to calculate the local score delta.
4. **Swap & Re-Evaluate:** Swaps the cards and injects the new tabla states back into the registries.
5. **Hill-Climbing:** If the global conflict score decreases or stays the same (sideways move), the swap is committed. If the score increases, the swap and registry states are reverted.

---

## Reviewer Notes & Considerations

* **Why Hill-Climbing vs. Backtracking?** Backtracking through an 800-node graph with complex geometric subset constraints leads to catastrophic combinatorial explosion. Hill-climbing scales linearly with $K$ and aggressively walks down the error gradient in milliseconds.
* **Performance Optimization:** The delta-scoring function (`apply_tabla_state`) is the most critical optimization in this PR. By dynamically removing and adding only the two modified tablas from the state dictionaries, we bypass the need to evaluate the other $K-2$ boards on every iteration.
* **Sideways Moves:** The condition `if current_score + step_delta <= current_score` uses `<=` rather than `<`. This is intentional. Accepting neutral swaps allows the algorithm to "walk" across flat plains in the state space to escape local minima.
* **Configurability:** $N$ and $K$ are exposed as runtime constants, allowing the generation of purist 54-card decks or modern 56-card decks without logic changes.