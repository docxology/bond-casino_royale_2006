"""Texas hold'em game-theory engine (Casino Royale, 2006 finale).

Pure, deterministic core simulating a heads-up / multi-way no-limit hold'em
showdown. ``Le Chiffre``'s bankroll backs a single massive pot; this module
gives the agent the three analytical layers the story needs:

* **Hand strength** - exact 5/7-card hand evaluation and a Monte-Carlo equity
  simulator for win/tie/lose probabilities over random runouts.
* **Pot odds** - the break-even equity implied by the pot and the amount to
  call, plus expected-value accounting for a calling decision.
* **Opponent modelling** - a running model of an adversary's tendencies
  (VPIP, aggression factor) that maps to a starting-hand range, against which
  the agent's equity is recomputed before recommending an action.

Everything is deterministic: every RNG draw flows through a caller-supplied
:class:`random.Random` seeded by the mission (never the global RNG, never wall
clock). The module imports nothing outside the standard library, so it stays
importable even if the bond-api path dependency is unavailable.

Film trivia anchoring the maths: the final hand pits Bond's hole cards against
Le Chiffre's on a shared board, and the decision logic is precisely "is my
equity against his range above the price the pot is laying me?".
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Card representation
# --------------------------------------------------------------------------- #
# A card is an int in 0..51. rank = card // 4 + 2 (so 2..14, 14 = Ace); suit =
# card % 4 (0=clubs,1=diamonds,2=hearts,3=spades).

RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "cdhs"
#: All 52 cards as a constant tuple (canonical order).
FULL_DECK: tuple[int, ...] = tuple(range(52))

#: Names of the nine hand categories, indexed by evaluate_5()'s category code.
CATEGORY_NAMES: dict[int, str] = {
    8: "straight flush",
    7: "four of a kind",
    6: "full house",
    5: "flush",
    4: "straight",
    3: "three of a kind",
    2: "two pair",
    1: "one pair",
    0: "high card",
}

#: Cached rank char lookup for 2..14.
_RANK_CHAR_BY_RANK: dict[int, str] = {r: RANK_CHARS[r - 2] for r in range(2, 15)}
_SUIT_CHAR_BY_SUIT: dict[int, str] = dict(enumerate(SUIT_CHARS))


def card_rank(card: int) -> int:
    """Return the rank of ``card`` as an int in ``2..14`` (14 = Ace)."""
    return card // 4 + 2


def card_suit(card: int) -> int:
    """Return the suit index (0..3) of ``card``."""
    return card % 4


def card_str(card: int) -> str:
    """Render ``card`` as a two-character string, e.g. ``As``, ``Td``, ``7c``."""
    return _RANK_CHAR_BY_RANK[card_rank(card)] + _SUIT_CHAR_BY_SUIT[card_suit(card)]


def parse_card(token: str) -> int:
    """Parse a two-character card string (``As``, ``Td``...) into an int code.

    Raises:
        ValueError: if the token does not describe a valid card.
    """
    if len(token) != 2:
        raise ValueError(f"card token must be 2 chars, got {token!r}")
    rank_c, suit_c = token[0].upper(), token[1].lower()
    if rank_c not in RANK_CHARS or suit_c not in SUIT_CHARS:
        raise ValueError(f"invalid card token {token!r}")
    rank = RANK_CHARS.index(rank_c) + 2
    suit = SUIT_CHARS.index(suit_c)
    return (rank - 2) * 4 + suit


def parse_cards(tokens: Sequence[str]) -> tuple[int, ...]:
    """Parse a sequence of card strings into a tuple of int codes."""
    return tuple(parse_card(t) for t in tokens)


# --------------------------------------------------------------------------- #
# Hand evaluation
# --------------------------------------------------------------------------- #


def evaluate_5(cards: Sequence[int]) -> tuple[int, tuple[int, ...]]:
    """Evaluate exactly five cards to ``(category, tiebreak_ranks)``.

    ``category`` is one of the codes in :data:`CATEGORY_NAMES`; ``tiebreak_ranks``
    is the ordered rank tuple that lexicographically compares two hands of the
    same category (higher is better).
    """
    if len(cards) != 5:
        raise ValueError(f"evaluate_5 requires exactly 5 cards, got {len(cards)}")

    ranks = [card_rank(c) for c in cards]
    uniq = sorted(set(ranks), reverse=True)

    flush = len({card_suit(c) for c in cards}) == 1

    straight_high: int | None = None
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        elif uniq == [14, 5, 4, 3, 2]:  # the wheel: A-2-3-4-5
            straight_high = 5

    if straight_high is not None and flush:
        return (8, (straight_high,))
    if flush:
        return (5, tuple(uniq))

    counts: dict[int, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    groups = sorted(((cnt, r) for r, cnt in counts.items()), reverse=True)

    if straight_high is not None:
        return (4, (straight_high,))

    cnt0, rank0 = groups[0]
    cnt1, rank1 = groups[1]
    if cnt0 == 4:
        return (7, (rank0, rank1))
    if cnt0 == 3 and cnt1 == 2:
        return (6, (rank0, rank1))
    if cnt0 == 3:
        kickers = tuple(r for r in uniq if r != rank0)
        return (3, (rank0, *kickers))
    if cnt0 == 2 and groups[1][0] == 2:
        return (2, (rank0, rank1, groups[2][1]))
    if cnt0 == 2:
        kickers = tuple(r for r in uniq if r != rank0)
        return (1, (rank0, *kickers))
    return (0, tuple(uniq))


def best_hand(cards: Sequence[int]) -> tuple[int, tuple[int, ...]]:
    """Return the best five-card hand among any subset of ``cards`` (5-7)."""
    if len(cards) < 5:
        raise ValueError(f"best_hand requires at least 5 cards, got {len(cards)}")
    return max(evaluate_5(combo) for combo in itertools.combinations(cards, 5))


def compare_hands(hand_a: Sequence[int], hand_b: Sequence[int]) -> int:
    """Return -1/0/1 comparing the best hands of ``hand_a`` and ``hand_b``."""
    va, vb = best_hand(hand_a), best_hand(hand_b)
    if va > vb:
        return 1
    if va < vb:
        return -1
    return 0


def category_name(category: int) -> str:
    """Human-readable name for a hand category code."""
    return CATEGORY_NAMES[category]


# --------------------------------------------------------------------------- #
# Dealing (deterministic)
# --------------------------------------------------------------------------- #


def shuffled_deck(rng: random.Random) -> list[int]:
    """Return a freshly shuffled deck using ``rng`` (no global state)."""
    deck = list(FULL_DECK)
    rng.shuffle(deck)
    return deck


def deal_hands(deck: Sequence[int], num_players: int) -> tuple[tuple[int, ...], ...]:
    """Deal two hole cards per player (button rotation), returning hands."""
    if num_players < 1:
        raise ValueError("num_players must be >= 1")
    needed = num_players * 2
    if needed > len(deck):
        raise ValueError("not enough cards in deck to deal two per player")
    hands: list[list[int]] = [[] for _ in range(num_players)]
    for street in range(2):
        for seat in range(num_players):
            hands[seat].append(deck[seat + street * num_players])
    return tuple(tuple(h) for h in hands)


def community_cards(deck: Sequence[int], num_players: int) -> tuple[int, ...]:
    """Return the five board cards after hole cards have been dealt."""
    start = num_players * 2
    return tuple(deck[start : start + 5])


def dead_cards(holes: Sequence[Sequence[int]], board: Sequence[int]) -> set[int]:
    """Return the set of card codes already committed (in holes or on board)."""
    dead: set[int] = set()
    for hand in holes:
        dead.update(hand)
    dead.update(board)
    if len(dead) != len(holes) * 2 + len(board):
        raise ValueError("duplicate card detected across holes/board")
    return dead


# --------------------------------------------------------------------------- #
# Equity / game theory
# --------------------------------------------------------------------------- #


def exact_equity_turn_river(
    hole_a: tuple[int, ...],
    hole_b: tuple[int, ...],
    board: tuple[int, ...],
) -> tuple[float, float, float]:
    """Exact heads-up equities over every turn+river runout after a given flop.

    ``board`` must be exactly 3 community cards (the flop). All 990 possible
    two-card runouts are enumerated, so the returned ``(win_a, tie, win_b)``
    fractions are exact - no sampling, no RNG.

    Returns:
        ``(win_a, tie, win_b)`` each in ``[0, 1]``; tie is the fraction of
        runouts where the two best hands are equal.
    """
    if len(board) != 3:
        raise ValueError("exact_equity_turn_river requires a 3-card flop")
    holes_a, holes_b = set(hole_a), set(hole_b)
    board_set = set(board)
    dead = holes_a | holes_b | board_set
    if len(dead) != len(holes_a) + len(holes_b) + len(board_set):
        raise ValueError("duplicate card in holes/board")
    remaining = [c for c in range(52) if c not in dead]

    wins = ties = total = 0
    for c1, c2 in itertools.combinations(remaining, 2):
        runout = (*board, c1, c2)
        ba = best_hand(hole_a + runout)
        bb = best_hand(hole_b + runout)
        total += 1
        if ba > bb:
            wins += 1
        elif ba == bb:
            ties += 1
    return wins / total, ties / total, (total - wins - ties) / total


def monte_carlo_equity(
    holes: tuple[tuple[int, ...], ...],
    board: tuple[int, ...],
    num_simulations: int,
    rng: random.Random,
) -> tuple[tuple[float, float], ...]:
    """Monte-Carlo win/tie equities for ``holes`` over random board runouts.

    Args:
        holes: one tuple of 2 hole cards per player.
        board: 0-4 community cards already revealed.
        num_simulations: number of random runouts to simulate (> 0).
        rng: caller-supplied seeded RNG (deterministic).

    Returns:
        One ``(win_frac, tie_frac)`` per player, in seat order. Ties count as a
        fraction assigned to each tied player but not as a win.
    """
    if num_simulations < 1:
        raise ValueError("num_simulations must be >= 1")
    n = len(holes)
    if n < 2:
        raise ValueError("monte_carlo_equity requires at least 2 players")
    if len(board) > 5:
        raise ValueError("board cannot have more than 5 cards")
    dead = dead_cards(holes, board)
    deck = [c for c in range(52) if c not in dead]
    to_reveal = 5 - len(board)

    wins = [0] * n
    ties = [0] * n
    for _ in range(num_simulations):
        rng.shuffle(deck)
        runout = board + tuple(deck[:to_reveal])
        values = [best_hand(h + runout) for h in holes]
        best = max(values)
        winners = [i for i, v in enumerate(values) if v == best]
        if len(winners) == 1:
            wins[winners[0]] += 1
        else:
            for i in winners:
                ties[i] += 1
    return tuple((wins[i] / num_simulations, ties[i] / num_simulations) for i in range(n))


def equity_vs_range(
    hole: tuple[int, ...],
    range_cards: Sequence[Sequence[int]],
    board: tuple[int, ...],
    num_simulations: int,
    rng: random.Random,
) -> float:
    """Average win equity of ``hole`` against every hand in an opponent range.

    The opponent's "range" is a concrete set of hole-card pairs representing
    the hands their tendencies suggest; ``equity_vs_range`` returns the mean of
    the per-handup Monte-Carlo win equities. This is the number the agent
    compares against the pot-odds break-even before acting.
    """
    if not range_cards:
        raise ValueError("range_cards must not be empty")
    run = num_simulations // len(range_cards)
    if run < 1:
        run = 1
    total = 0.0
    for opp_hand in range_cards:
        win, _tie = monte_carlo_equity((tuple(hole), tuple(opp_hand)), board, run, rng)[0]
        total += win
    return total / len(range_cards)


def iter_opponent_hands(
    class_names: Sequence[str],
    dead: set[int],
    rng: random.Random,
    count: int,
) -> Iterator[tuple[int, ...]]:
    """Yield ``count`` concrete opponent hole-card pairs from hand classes.

    Each starting-hand *class* (``AA``, ``AKs``, ``T9o``...) is turned into a
    specific pair of cards drawn from the live deck, avoiding all dead cards.
    The same class may be drawn more than once, approximating a weighted range.
    """
    produced = 0
    while produced < count:
        for cls in class_names:
            if produced >= count:
                return
            pair = _cards_for_class(cls, dead, rng)
            if pair is not None:
                yield pair
                produced += 1


def _cards_for_class(
    class_name: str,
    dead: set[int],
    rng: random.Random,
) -> tuple[int, ...] | None:
    """Sample one concrete pair for a starting-hand class, or None if impossible."""
    if len(class_name) == 2:  # a pair, e.g. "AA" or "77"
        rc = class_name[0]
        rank = RANK_CHARS.index(rc) + 2
        suits = [s for s in range(4) if (rank - 2) * 4 + s not in dead]
        if len(suits) < 2:
            return None
        chosen = rng.sample(suits, 2)
        return tuple((rank - 2) * 4 + s for s in chosen)
    hi_c, lo_c, suited = class_name[0], class_name[1], class_name.endswith("s")
    hi, lo = RANK_CHARS.index(hi_c) + 2, RANK_CHARS.index(lo_c) + 2
    hi_cards = [(hi - 2) * 4 + s for s in range(4) if (hi - 2) * 4 + s not in dead]
    lo_cards = [(lo - 2) * 4 + s for s in range(4) if (lo - 2) * 4 + s not in dead]
    if not hi_cards or not lo_cards:
        return None
    if suited:
        common = [
            s for s in range(4) if (hi - 2) * 4 + s in hi_cards and (lo - 2) * 4 + s in lo_cards
        ]
        if not common:
            return None
        s = rng.choice(common)
        return ((hi - 2) * 4 + s, (lo - 2) * 4 + s)
    hi_pick = rng.choice(hi_cards)
    lo_pick = rng.choice(lo_cards)
    return (hi_pick, lo_pick)


# --------------------------------------------------------------------------- #
# Pot odds and decision
# --------------------------------------------------------------------------- #


def pot_odds_ratio(pot: float, to_call: float) -> float:
    """Return the pot odds ``pot / to_call`` (the price the pot offers)."""
    if pot < 0:
        raise ValueError("pot must be >= 0")
    if to_call <= 0:
        raise ValueError("to_call must be > 0")
    return pot / to_call


def break_even_equity(pot: float, to_call: float) -> float:
    """Equity at which calling is break-even: ``to_call / (pot + to_call)``."""
    if pot < 0 or to_call <= 0:
        raise ValueError("pot >= 0 and to_call > 0 required")
    return to_call / (pot + to_call)


def ev_of_call(equity: float, pot: float, to_call: float) -> float:
    """Expected value of calling, in chips: ``equity*(pot+to_call) - to_call``."""
    if not 0.0 <= equity <= 1.0:
        raise ValueError("equity must be in [0, 1]")
    if pot < 0 or to_call <= 0:
        raise ValueError("pot >= 0 and to_call > 0 required")
    return equity * (pot + to_call) - to_call


def equity_margin(equity: float, pot: float, to_call: float) -> float:
    """Decision margin ``equity - break_even`` (positive favours playing)."""
    return equity - break_even_equity(pot, to_call)


def recommend_action(
    pot: float,
    to_call: float,
    equity: float,
    *,
    raise_margin: float = 0.10,
    fold_margin: float = 0.0,
) -> str:
    """Recommend ``"fold"``, ``"call"``, or ``"raise"`` from equity vs price.

    If the equity margin is below ``fold_margin`` the hand is folded; above
    ``raise_margin`` it is raised (value extraction against a weak range);
    otherwise it is called.
    """
    margin = equity_margin(equity, pot, to_call)
    if margin < fold_margin:
        return "fold"
    if margin > raise_margin:
        return "raise"
    return "call"


# --------------------------------------------------------------------------- #
# Opponent modelling
# --------------------------------------------------------------------------- #


@dataclass
class OpponentModel:
    """Running tendency model of an adversary at the table."""

    name: str
    raises: int = 0
    bets: int = 0
    calls: int = 0
    folds: int = 0
    hands_seen: int = 0

    def update(self, action: str) -> None:
        """Record one observed action, incrementing the matching counter.

        ``action`` must be one of ``"raise"``, ``"bet"``, ``"call"``, ``"fold"``.
        ``hands_seen`` ticks once per action (documented simplification).
        """
        key = action.strip().lower()
        if key not in {"raise", "bet", "call", "fold"}:
            raise ValueError(f"unknown action {action!r}")
        if key == "raise":
            self.raises += 1
        elif key == "bet":
            self.bets += 1
        elif key == "call":
            self.calls += 1
        else:
            self.folds += 1
        self.hands_seen += 1

    @property
    def vpip(self) -> float:
        """Voluntarily-put-in-pot percentage over hands seen (approx)."""
        if self.hands_seen == 0:
            return 0.0
        return (self.raises + self.bets + self.calls) / self.hands_seen

    @property
    def aggression_factor(self) -> float:
        """(raises + bets) / calls; > 1 is aggressive, < 1 is passive."""
        if self.calls == 0:
            return float(self.raises + self.bets)
        return (self.raises + self.bets) / self.calls

    def archetype(self) -> str:
        """Map tendencies to a coarse label: tight/loose, passive/aggressive."""
        looseness = "loose" if self.vpip >= 0.5 else "tight"
        aggression = "aggressive" if self.aggression_factor >= 1.0 else "passive"
        return f"{looseness}-{aggression}"


def starting_hand_class(cards: Sequence[int]) -> str:
    """Canonical name of a two-card starting hand, e.g. ``AKs``, ``TT``, ``97o``."""
    r1, r2 = card_rank(cards[0]), card_rank(cards[1])
    if r1 == r2:
        return _RANK_CHAR_BY_RANK[r1] * 2
    hi, lo = max(r1, r2), min(r1, r2)
    suited = "s" if card_suit(cards[0]) == card_suit(cards[1]) else "o"
    return _RANK_CHAR_BY_RANK[hi] + _RANK_CHAR_BY_RANK[lo] + suited


#: Predefined starting-hand ranges for common opponent archetypes (as class
#: names). TIGHT ~ top hands; LOOSE ~ a wide, speculative range.
RANGE_ARCHETYPES: dict[str, frozenset[str]] = {
    "tight": frozenset(
        {
            "AA",
            "KK",
            "QQ",
            "JJ",
            "TT",
            "99",
            "AKs",
            "AQs",
            "AJs",
            "AKo",
            "AQo",
            "KQs",
            "88",
            "77",
            "AJo",
        }
    ),
    "loose": frozenset(
        {
            "AA",
            "KK",
            "QQ",
            "JJ",
            "TT",
            "99",
            "88",
            "77",
            "66",
            "55",
            "AKs",
            "AQs",
            "AJs",
            "ATs",
            "A9s",
            "A8s",
            "AKo",
            "AQo",
            "AJo",
            "ATo",
            "KQs",
            "KJs",
            "KTs",
            "KQo",
            "QJs",
            "QTs",
            "JTs",
            "T9s",
            "98s",
            "87s",
        }
    ),
}


def recommended_raise_margin(archetype: str) -> float:
    """Suggested value-extraction raise threshold for a range archetype.

    Against a loose-passive station we extract more (raise earlier); against a
    tight-aggressive hand we thin the range by raising less often.
    """
    if archetype == "loose-passive":
        return 0.06
    if archetype == "loose-aggressive":
        return 0.10
    if archetype == "tight-aggressive":
        return 0.14
    return 0.10
