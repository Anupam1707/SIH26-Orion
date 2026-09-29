# Module 02: Predictive Analytics Engine
## Key Deliverable Component (a) — Technical Specification

---

## 1. Objective & Scope

The **Predictive Analytics Engine** analyzes historical cybercrime complaint data, transactional flows, and spatial ATM usage patterns to forecast potential cash withdrawal locations before funds are liquidated. It operates across three core analytical layers:
1. **Graph Tracing & Pattern Detection:** Multi-hop transaction reconstruction and behavioral typology detection.
2. **Structural & Temporal Anomaly Scoring:** OddBall power-law deviation and sliding-window temporal burst metrics.
3. **Geospatial & Machine Learning Forecasting:** Ensemble of spatial kernel density estimation, graph-aware gradient boosting (XGBoost), and recency baselines.

---

## 2. Graph Tracing & Pattern Detection

### 2.1 Chronological Multi-DiGraph
The financial network is modeled as a directed multigraph $G = (V, E)$, where vertices $V$ represent bank accounts and directed edges $E = \{(u, v, t, a, c)\}$ represent transactions with source $u$, destination $v$, timestamp $t$, amount in INR $a$, and channel $c$ (UPI, IMPS, NEFT).

When an NCRP complaint $C = (u_{\text{victim}}, a_{\text{loss}}, t_{\text{incident}}, t_{\text{reported}})$ is received:
- `trace_case(complaint_id)` performs forward breadth-first exploration along edges with $t \ge t_{\text{incident}}$.
- Branch pruning: Paths where cumulative transferred funds drop below 5% of $a_{\text{loss}}$ are pruned to suppress incidental noise.
- Conservation of flow: Accounts cannot forward more traced funds than have been chronologically received.

### 2.2 Typology Detection Rules
Syndicate money laundering follows known structural typologies. Five specialized detection heuristics are evaluated over the graph:

| Typology Rule | Mathematical Heuristic | Target Syndicate Behavior |
|---|---|---|
| **Mule Fan-In** | Account receives from $\ge 3$ distinct senders within 6 hours, and forwards $\ge 90\%$ of aggregate inflow within 24 hours; repeated $\ge 2$ times across history. Guarded against merchant false-positives via 24h receipt-coverage settlement windows. | Collector accounts aggregating stolen sums from multiple layer-1 mules. |
| **Layering Chain** | Directed path of $\ge 4$ accounts ($\ge 3$ hops) where, for each intermediary $v_i$, departure time $t_{\text{out}} - t_{\text{in}} < 3\text{h}$ and sum of outflows covers $85\%\text{--}98\%$ of inflows. | Classic money-laundering layering intended to obscure fund origin. |
| **Structuring (Smurfing)** | Account executing $\ge 3$ outbound transfers in the bracket $[\text{₹}9,000, \text{₹}9,900]$ (deliberately staying below mandatory ₹10,000 regulatory reporting thresholds). | Layer-1 mules attempting to evade automated banking threshold alerts. |
| **Scatter Dispersion** | Account dispersing funds to $\ge 6$ distinct recipient accounts within a tight 2-hour window. | High-speed multi-mule fan-out to parallelize cash-out agents. |
| **Rapid Pass-Through** | Account forwarding $\ge 90\%$ of an incoming receipt within 60 minutes, observed across $\ge 3$ distinct episodes. | Ephemeral transit mule accounts. |

---

## 3. Structural & Temporal Anomaly Engines

### 3.1 OddBall Structural Scoring (`detect/oddball.py`)
OddBall analyzes the ego-network $G_v$ of each account $v$, measuring the relationship between the number of ego-neighbors $N_v$ and the number of intra-ego edges $E_v$.
In standard social and economic graphs, networks adhere to an empirical power-law:
$$E_v \propto N_v^\alpha, \quad \text{where } 1 \le \alpha \le 2$$

1. Fit linear regression in log-space across the active graph:
   $$\log_{10}(E_v) = \alpha \log_{10}(N_v) + \beta$$
2. Compute expected edges: $\hat{E}_v = 10^{\alpha \log_{10}(N_v) + \beta}$
3. Calculate structural anomaly distance:
   $$\text{Score}_{\text{raw}}(v) = \frac{\max(E_v, \hat{E}_v)}{\min(E_v, \hat{E}_v)} \cdot \log_{10}(|E_v - \hat{E}_v| + 1)$$
4. Topological group classification:
   - If $E_v < \hat{E}_v$: classified as **STAR** topology (indicative of hub-and-spoke mule collectors).
   - If $E_v \ge \hat{E}_v$: classified as **NEAR_CLIQUE** (tightly interconnected synthetic rings).
5. Group-wise Z-score normalization: To eliminate bias toward dense cliques and surface star-shaped mule hubs, Z-scores are computed independently within each topological shape group.

### 3.2 Sliding-Window Temporal Burst Scoring (`detect/temporal.py`)
Mule accounts exhibit acute bursts of activity compared to normal civilian accounts.
1. For accounts with $\ge 5$ outbound transfers, identify the **densest 48-hour continuous window**.
2. Within this densest window, compute:
   - Coefficient of Variation of inter-transfer time gaps: $CV_{\text{gap}} = \frac{\sigma_{\text{gap}}}{\mu_{\text{gap}}}$
   - Coefficient of Variation of transaction amounts: $CV_{\text{amount}} = \frac{\sigma_{\text{amount}}}{\mu_{\text{amount}}}$
   - Burstiness concentration ratio: $R_{\text{burst}} = \frac{N_{\text{window}}}{N_{\text{total}}}$
3. Composite burst metric:
   $$\text{Score}_{\text{burst}} = -Z(CV_{\text{gap}}) + Z(R_{\text{burst}}) - Z(CV_{\text{amount}})$$
   *(Accounts with low jitter in time gaps, high concentration, and uniform structuring achieve maximum burst scores).*

---

## 4. Cash-Out Prediction Models

For an active case at prediction time $t_{\text{pred}} = \max(t_{\text{reported}}, t_{\text{last\_L2\_transfer}})$, the engine ranks all ATMs $a \in \mathcal{A}$ over forecast horizons $H \in \{2\text{h}, 6\text{h}, 24\text{h}\}$.

### 4.1 Recency Baseline
Ranks ATMs based on the temporal proximity of past withdrawals executed by accounts in the traced chain and their 1-hop neighborhood:
$$P_{\text{base}}(a) = \sum_{w \in W(a)} \exp\left(-\lambda \cdot (t_{\text{pred}} - t_w)\right)$$
Provides a robust benchmark, particularly effective against static syndicates operating fixed ATM pools.

### 4.2 Spatial Kernel Density Estimation (KDE)
Models the spatial distribution of cash-out risk as a continuous probability density over geographic coordinates $(\text{lat}, \text{lng})$:
1. Coordinate transformation: Projects coordinates to local Cartesian kilometer offsets via equirectangular projection centered at the regional centroid:
   $$x = R_{\text{earth}} \cdot (\text{lng} - \text{lng}_0) \cdot \cos\left(\frac{\text{lat}_0 \cdot \pi}{180}\right), \quad y = R_{\text{earth}} \cdot (\text{lat} - \text{lat}_0)$$
2. Fits Gaussian Kernel Density with bandwidth $h$:
   $$\hat{f}(x, y) = \frac{1}{n h^2 2\pi} \sum_{i=1}^n \exp\left(-\frac{(x - x_i)^2 + (y - y_i)^2}{2h^2}\right)$$
3. Bandwidth $h$ is optimized strictly over training-period cases (Days 1–70) via prequential log-likelihood cross-validation.

### 4.3 Graph-Aware XGBoost Classifier
A supervised gradient boosted tree model trained on $(Case, ATM)$ pairs with strict chronological holdout splits (Train: Days 1–70, Test: Days 71–90).

**Engineered Feature Vector:**
- $d(a, \text{District}_{L2})$: Euclidean distance from ATM to terminal L2 account home districts.
- $W_{7d}(a), W_{30d}(a)$: Count of historical withdrawals at this ATM by chain-linked accounts over 7-day and 30-day lookbacks.
- $\hat{f}_{\text{KDE}}(a)$: Spatial KDE density evaluated at ATM coordinates.
- $H_{\text{hops}}$: Number of graph hops from victim to current fund-holding account.
- $S_{\text{burst}}$: Temporal burst score of active chain accounts.
- $\tau_{\text{hour}}, \tau_{\text{dow}}$: Hour of day (0–23) and day of week (0–6) of the prediction timestamp.
- $\mathbb{I}_{\text{district\_hop}}$: Binary flag indicating if the candidate ATM district differs from the district of the previous withdrawal (capturing cross-jurisdictional evasion).

**Explainability Integration:**
Predictions are decomposed using tree SHAP contributions (`pred_contribs=True`). The top 3 positive feature contributions are translated dynamically into human-readable investigator justifications (e.g., *"Accounts in this chain withdrew here 4 times in the past 30 days"*, *"Current fund location is 1 hop from withdrawal"*).
