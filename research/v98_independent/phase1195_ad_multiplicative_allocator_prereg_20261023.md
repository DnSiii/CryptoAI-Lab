# V98 Independent Phase1195 — AD multiplicative actual-wealth sleeve allocator preregistration (2026-10-23)

AD remains a **seven-slot composed engine under construction**; the four source sleeves and Bayesian router exist, but no complete engine has passed economic validation. This preregisters **only the Dynamic Allocator's causal virtual sleeve accounting and target-mixture rule**, before any official AD system PnL. Execution, 81-corner governor and actual cash/NAV remain separate hard gates.

## Four-sleeve net log-wealth mixture (not AC coordinate search)
At each completed bar t, maintain four virtual sleeve wealth accounts initialized to 1.0 and expert mixture prior [0.70 Growth, 0.10 Opportunity, 0.10 Relative Value, 0.10 Stress]. Prior sleeve holdings decided at t-1 are marked to t using realized **simple** asset close-to-close returns, signed native funding paid at t, and fixed severe fee 0.0012 on the absolute sleeve turnover decided at t-1. These are causal **virtual performance features**, not AD executable PnL.

Update each positive sleeve wealth multiplicatively. Mixture logits = log(prior)+0.25*log(virtual_wealth), then softmax; posterior floor 0.03 each and renormalize. Regime posterior [off, transition, on] multiplies Growth by (0.5 + on), Opportunity and RV by (0.5 + 0.5*transition), Stress by (0.5 + off); renormalize. No static score map or four-pass coordinate optimizer. Rejected sleeve wealth<=0, nonfinite or malformed input fails closed.

## Sleeve intent conversion
Growth input is four long/cash weights from Phase1189. Opportunity Phase1191 -1/0/+1 converted to signed **0.10** weight per active asset. RV Phase1192 gross-1 neutral weights converted to signed **0.15** gross. Stress Phase1193 signed gross-0.15/0.30 *already* actual-NAV-dependent. Mixture is weighted sum of those four vectors. Prior executed weights/actual inventory are NOT silently assumed to equal desired mixture: downstream governor/executor must handle real fill, liquidity, fee/funding, mark-to-market and capacity.

At t, virtual sleeve wealth update uses *previous* sleeve targets; next targets can only execute at t+1 open. Do not use 2025+, XRP, V14/V15/V99, Phase083 or future results. No post-result sign/learning-rate/prior/fee rescue. The complete AD must later pass 90-cell executable growth gate with positive marginal contribution for all non-core sleeves.
