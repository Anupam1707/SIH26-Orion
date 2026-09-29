# Module 06: Node-Capacity Min-Cut Fund Blocking
## Mathematical Formulation & Operational Intervention Spec

---

## 1. Problem Formulation: The Freezing Dilemma

In financial cyber fraud mitigation, Law Enforcement Agencies (LEAs) and Banks face a fundamental operational challenge:
- **Freezing too many accounts** causes severe collateral damage to innocent citizens, creates compliance overhead, and overwhelms bank nodal officers.
- **Freezing too late or at the wrong hops** allows funds to slip past to ATM cash-out points.

**Goal:** Identify the **minimal set of accounts** to freeze that **maximizes the volume of stopped funds** before cash-out occurs.

---

## 2. Mathematical Modeling via Node-Capacity Minimum Cut

Standard minimum-cut algorithms (e.g., Ford-Fulkerson, Edmonds-Karp, Boykov-Kolmogorov) find the minimal cut across **edges**. However, in financial investigations, **interventions act upon nodes (accounts)**, not transaction channels.

MuleTrail solves this by converting node freezing into an edge cut problem via **directed node splitting**.

### 2.1 Graph Transformation
Given the traced directed acyclic case subgraph $G = (V, E)$ at the current demo clock:
1. **Super-Source ($S$) and Super-Sink ($T$):**
   - Add $S$ connected to the victim account: $c(S, v_{\text{victim}}) = \infty$.
   - Connect all terminal recipient / withdrawing accounts $v_{\text{term}}$ to $T$: $c(v_{\text{term}}, T) = \infty$.
2. **Node Splitting:**
   - Every intermediate account $v \in V \setminus \{v_{\text{victim}}, S, T\}$ is split into an in-vertex $v_{\text{in}}$ and an out-vertex $v_{\text{out}}$.
   - An internal directed edge $(v_{\text{in}}, v_{\text{out}})$ is created.
   - All original incoming edges to $v$ now terminate at $v_{\text{in}}$: $(u_{\text{out}}, v_{\text{in}})$ with capacity $\infty$.
   - All original outgoing edges from $v$ now originate from $v_{\text{out}}$: $(v_{\text{out}}, w_{\text{in}})$ with capacity $\infty$.

### 2.2 Capacity Assignment: Prioritizing Account Count with Volume Tiebreak
To ensure the cut strictly minimizes the **number of accounts** frozen (rather than treating accounts as cost-free conduits), internal edge capacities are defined as:
$$c(v_{\text{in}}, v_{\text{out}}) = 1 - 0.01 \times \left(\frac{\text{Money through } v}{\text{Total case amount}}\right)$$

**Properties of this formulation:**
1. Since each account's capacity satisfies $0.99 \le c(v) \le 1.0$, cutting $k$ accounts incurs a capacity cost between $[0.99k, 1.0k]$.
2. Therefore, cutting $k$ accounts is **strictly cheaper** than cutting $k+1$ accounts ($1.0k < 0.99(k+1)$ holds for all realistic $k \le 99$). The algorithm will **never freeze extra accounts** unnecessarily.
3. Among multiple cuts with equal account counts $k$, the cut minimizing total capacity will select the accounts that carried the **highest proportion of funds** (maximizing the tiebreaker deduction).

### 2.3 Chronological Departure Invariance
Crucially, accounts through which money has **already completely departed** by the active demo clock cannot stop funds if frozen.
$$\text{If } t_{\text{last\_out}}(v) \le t_{\text{clock}} \text{ and balance is zero: } c(v_{\text{in}}, v_{\text{out}}) = \infty$$
Assigning infinite capacity guarantees the min-cut will **never waste freezing orders on dead accounts**.

---

## 3. Greedy Fallback & Freeze Simulation

### 3.1 Bounded Fallback
If the optimal minimum cut requires freezing more than $k_{\text{max}}$ accounts (default $k_{\text{max}} = 3$), the engine automatically engages a greedy heuristic:
1. Iteratively evaluate every candidate active account $v$.
2. Compute the reduction in reachable funds if $v$ is blocked.
3. Freeze the account yielding the highest marginal fund interception until $k_{\text{max}}$ accounts are selected or remaining reachable flow drops to zero.

### 3.2 Freeze Simulation Engine
The `/block/{complaint_id}/simulate` endpoint provides an immediate quantitative impact assessment:
- **Baseline Reachable Flow:** Maximum network flow from $S$ to $T$ over the transaction subgraph (with edge capacities set to actual transfer amounts), excluding already-withdrawn cash.
- **Post-Intervention Flow:** Max flow recomputed after removing chosen accounts.
- **Interception Rate:**
  $$\text{Recovery Rate} = \frac{\text{Flow}_{\text{before}} - \text{Flow}_{\text{after}}}{\text{Flow}_{\text{before}}} \times 100\%$$
- Visualized in the UI with animated before/after impact bars.
