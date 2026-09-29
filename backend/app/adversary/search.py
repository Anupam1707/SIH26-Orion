"""Greedy search for adversary evasion (spec §11).

Finds the most cost-effective sequence of moves to evade top-5 ATM detection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.adversary.moves import add_mule_hop, delay_withdrawal, split_amount, switch_atm


@dataclass
class MoveLogEntry:
    step: int
    move: str
    description: str
    cost: float
    cumulative_cost: float
    target_atms: list[str]
    top5_atms: list[str]
    detection_prob: float
    detected: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvasionResult:
    complaint_id: str
    initial_detected: bool
    final_detected: bool
    total_cost: float
    initial_probability: float
    final_probability: float
    moves: list[MoveLogEntry]
    hardened: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "complaint_id": self.complaint_id,
            "hardened": self.hardened,
            "initial_detected": self.initial_detected,
            "final_detected": self.final_detected,
            "total_cost": self.total_cost,
            "initial_probability": self.initial_probability,
            "final_probability": self.final_probability,
            "moves_count": len(self.moves),
            "moves": [m.to_dict() for m in self.moves],
        }


def greedy_evasion_search(
    complaint_id: str,
    initial_targets: list[str],
    amount_inr: float,
    atm_predictions: list[dict],
    all_atms: list[dict],
    freeze_risk_per_hour: float = 0.02,
    max_steps: int = 8,
    hardened: bool = False,
) -> EvasionResult:
    """Execute greedy search with no budget cap until undetected or no move improves probability."""
    # Top 5 ATMs for the 6h horizon
    sorted_atms = sorted(atm_predictions, key=lambda x: -x["probability"])
    top5_ids = [a["id"] for a in sorted_atms[:5]]
    prob_map = {a["id"]: a["probability"] for a in sorted_atms}
    atm_lookup = {a["id"]: a for a in all_atms}

    current_targets = list(initial_targets) if initial_targets else ([sorted_atms[0]["id"]] if sorted_atms else [])
    initial_detected = any(a in top5_ids for a in current_targets)
    initial_prob = max((prob_map.get(a, 0.0) for a in current_targets), default=0.0)

    # Candidate ATMs outside the top 5
    non_top5_atms = [a for a in all_atms if a["id"] not in top5_ids]

    moves_log: list[MoveLogEntry] = []
    cumulative_cost = 0.0
    current_prob = initial_prob
    current_detected = initial_detected

    if not initial_detected:
        return EvasionResult(
            complaint_id=complaint_id,
            initial_detected=False,
            final_detected=False,
            total_cost=0.0,
            initial_probability=initial_prob,
            final_probability=initial_prob,
            moves=[],
            hardened=hardened,
        )

    # Threshold for entering top 5: probability of the 5th ATM
    top5_cutoff = sorted_atms[4]["probability"] if len(sorted_atms) >= 5 else 0.0

    for step in range(1, max_steps + 1):
        if not current_detected:
            break

        candidates: list[tuple[float, Any, list[str], float, bool]] = []
        # (efficiency, move_result, new_targets, new_prob, new_detected)

        # Move 1: Switch ATM (for each current target that is in top 5)
        for target_id in current_targets:
            if target_id in top5_ids and target_id in atm_lookup:
                curr_atm = atm_lookup[target_id]
                for cand in non_top5_atms[:10]:  # Evaluate closest 10 candidates outside top 5
                    m = switch_atm(curr_atm, cand, current_targets)
                    new_targets = m.target_atms
                    new_det = any(a in top5_ids for a in new_targets)
                    new_prob = max((prob_map.get(a, 0.0) for a in new_targets), default=0.0)
                    drop = current_prob - new_prob
                    if drop > 0 and m.cost > 0:
                        efficiency = drop / m.cost
                        candidates.append((efficiency, m, new_targets, new_prob, new_det))

        # Move 2: Delay (Wait 12 hours)
        m_delay = delay_withdrawal(amount_inr, freeze_risk_per_hour, current_targets)
        new_prob_delay = max(0.0, current_prob * 0.25)
        drop_delay = current_prob - new_prob_delay
        new_det_delay = new_prob_delay >= top5_cutoff and current_detected
        if drop_delay > 0 and m_delay.cost > 0:
            candidates.append((drop_delay / m_delay.cost, m_delay, current_targets, new_prob_delay, new_det_delay))

        # Move 3: Add Mule Hop (Insert extra layer)
        m_hop = add_mule_hop(current_targets)
        new_prob_hop = max(0.0, current_prob * 0.70)
        drop_hop = current_prob - new_prob_hop
        new_det_hop = new_prob_hop >= top5_cutoff and current_detected
        if drop_hop > 0 and m_hop.cost > 0:
            candidates.append((drop_hop / m_hop.cost, m_hop, current_targets, new_prob_hop, new_det_hop))

        # Move 4: Split Amount across 2 more ATMs
        if non_top5_atms:
            m_split = split_amount(non_top5_atms[:2], current_targets)
            new_prob_split = max(0.0, current_prob * 0.50)
            drop_split = current_prob - new_prob_split
            new_det_split = new_prob_split >= top5_cutoff and current_detected
            if drop_split > 0 and m_split.cost > 0:
                candidates.append(
                    (drop_split / m_split.cost, m_split, m_split.target_atms, new_prob_split, new_det_split)
                )

        if not candidates:
            break

        # Pick the move that maximizes drop in detection probability per ₹ of cost
        candidates.sort(key=lambda x: -x[0])
        best_eff, best_move, next_targets, next_prob, next_det = candidates[0]

        if best_eff <= 0 or next_prob >= current_prob:
            break

        cumulative_cost = round(cumulative_cost + best_move.cost, 2)
        current_targets = next_targets
        current_prob = round(next_prob, 4)
        current_detected = next_det

        moves_log.append(
            MoveLogEntry(
                step=step,
                move=best_move.move,
                description=best_move.description,
                cost=best_move.cost,
                cumulative_cost=cumulative_cost,
                target_atms=list(current_targets),
                top5_atms=list(top5_ids),
                detection_prob=current_prob,
                detected=current_detected,
            )
        )

        if not current_detected:
            break

    return EvasionResult(
        complaint_id=complaint_id,
        initial_detected=initial_detected,
        final_detected=current_detected,
        total_cost=cumulative_cost,
        initial_probability=initial_prob,
        final_probability=current_prob,
        moves=moves_log,
        hardened=hardened,
    )
