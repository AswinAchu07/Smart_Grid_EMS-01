# Mathematical Formulation: Energy Management System & Physical Battery Model

## 1. Physical Conservation Laws

At every discrete simulation timestep \(t \in \{1, 2, \dots, T\}\) with interval \(\Delta t\) (hours):

### 1.1 Power Balance at the Electrical Load
The instantaneous electric load demand \(L_t\) must be satisfied at all times:
\[
P_{s\_load,t} + P_{bat\_load,t} + P_{grid\_load,t} = L_t \quad \forall t
\]
where:
- \(P_{s\_load,t} \ge 0\): Solar PV power supplied directly to load (kW)
- \(P_{bat\_load,t} \ge 0\): Battery power discharged to supply load (kW)
- \(P_{grid\_load,t} \ge 0\): Power imported from the electrical grid (kW)

### 1.2 Solar PV Generation Allocation
Total available solar power \(S_t\) is allocated across load, storage, and grid export:
\[
P_{s\_load,t} + P_{s\_bat,t} + P_{s\_grid,t} = S_t \quad \forall t
\]
where:
- \(P_{s\_bat,t} \ge 0\): Solar PV power routed to charge the battery (kW)
- \(P_{s\_grid,t} \ge 0\): Excess solar PV power exported to the grid (kW)

### 1.3 Strict System Energy Conservation
Summing both equations verifies that Total Energy Sources equals Total Energy Sinks:
\[
\underbrace{S_t + P_{bat\_load,t} + P_{grid\_load,t}}_{\text{Total Energy Sources}} = \underbrace{L_t + P_{s\_bat,t} + P_{s\_grid,t}}_{\text{Total Energy Sinks}}
\]

---

## 2. Battery Storage Physics & SOC Dynamics

### 2.1 State of Charge (SOC) Continuity
The battery's State of Charge \(SOC_t \in [SOC_{min}, SOC_{max}]\) evolves according to:
\[
SOC_{t} = SOC_{t-1} + \frac{P_{ch,t} \cdot \eta_{ch} \cdot \Delta t}{C_{kwh}} - \frac{P_{dis,t} \cdot \Delta t}{\eta_{dis} \cdot C_{kwh}}
\]
where:
- \(C_{kwh}\): Rated total battery capacity (e.g. 10.0 kWh)
- \(\eta_{ch} \in (0, 1]\): Charging efficiency (e.g. 0.95)
- \(\eta_{dis} \in (0, 1]\): Discharging efficiency (e.g. 0.95)
- \(P_{ch,t} = P_{s\_bat,t}\): Total charging power (kW)
- \(P_{dis,t} = P_{bat\_load,t}\): Total discharging power (kW)

### 2.2 Power Rating & Mutual Exclusivity Constraints
Charging and discharging are bounded by hardware power converters and cannot occur simultaneously:
\[
0 \le P_{ch,t} \le P_{ch\_max} \cdot u_{ch,t}
\]
\[
0 \le P_{dis,t} \le P_{dis\_max} \cdot u_{dis,t}
\]
\[
u_{ch,t} + u_{dis,t} \le 1, \quad u_{ch,t}, u_{dis,t} \in \{0, 1\}
\]

---

## 3. Mixed-Integer Linear Programming (MILP) Optimization Formulation

### 3.1 Objective Function
The objective is to minimize total net operating cost over horizon \(T\) (e.g., \(T=24\text{ h}\)), accounting for Time-of-Use (TOU) import tariffs, feed-in export remuneration, and battery cycling depreciation:
\[
\min \sum_{t=1}^T \Big( c_{import,t} \cdot P_{grid\_load,t} - c_{export,t} \cdot P_{s\_grid,t} + c_{deg} \cdot (P_{ch,t} + P_{dis,t}) \Big) \cdot \Delta t
\]
where:
- \(c_{import,t}\): Hourly electricity purchase tariff ($/kWh)
- \(c_{export,t}\): Feed-in tariff ($/kWh)
- \(c_{deg}\): Battery degradation penalty ($0.005 / kWh)
