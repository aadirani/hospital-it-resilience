# Code walkthrough: `tools/ups_runtime.py`

A plain-language explanation, so the code can be explained and defended without being a programmer.

## The problem it solves

When the grid fails, the UPS battery has to keep the server room running **until the generator takes over**. If the generator fails, the battery also has to give **enough time to shut down safely**. The script answers: *how long will my battery last, and how big does it need to be?*

## The physics, in one line

```
usable energy (Wh) = voltage × capacity (Ah) × depth of discharge × inverter efficiency × aging factor
runtime (hours)    = usable energy ÷ load (W)
```

Each factor explained:

| Factor | Value used | Why |
|---|---|---|
| **Voltage × Ah** | e.g., 48 V × 100 Ah = 4,800 Wh | The battery's rated ("nameplate") energy |
| **Depth of discharge** | Lead-acid 50%, LiFePO4 80% | Draining a battery fully every day shortens its life. In this setting outages happen daily, so the design only counts on the part that can be used regularly |
| **Inverter efficiency** | 90% | Turning battery DC into AC for the servers wastes about 10% as heat |
| **Aging factor** | 80% | Batteries lose capacity over time. Sizing for an old battery means the design still works in year 4 |

For example, 4,800 Wh × 0.8 × 0.9 × 0.8 = **2,765 Wh** actually usable. With 1,610 W of servers, that's 2,765 ÷ 1,610 ≈ 1.72 h ≈ **103 minutes**.

## The code, piece by piece

**`DEPTH_OF_DISCHARGE`**: a small lookup table with one number for each battery type.

**`class Battery`**: holds the battery's details (voltage, Ah, type, efficiency, aging). `@dataclass` is Python shorthand that creates the object without boilerplate code.
- `__post_init__` checks the inputs straight away and rejects nonsense like a battery type it doesn't know or a voltage of zero.
- `usable_wh()` is the formula above.

**`load_from_csv(path)`**: reads the device list (`device, quantity, watts`) and adds up `quantity × watts` for each row. The sample file adds up to 1,610 W.

**`runtime_minutes(battery, load_w)`**: usable energy ÷ load × 60. It refuses a load of zero, which would cause a divide-by-zero error.

**`required_capacity_ah(...)`**: the same formula run backwards. It works out how much usable energy **one** amp-hour gives at this voltage, then divides the energy needed by that. Example: 15 min at 1,610 W = 402.5 Wh needed; one Ah at 48 V gives 27.6 Wh usable, so 402.5 ÷ 27.6 ≈ **15 Ah**.

**`required_ups_va(load_w)`**: UPS units are rated in **VA**, not watts. Watts = VA × power factor (about 0.9 for modern UPS units). The function also adds **25% headroom** for growth and so the UPS doesn't run at full load all the time. 1,610 ÷ 0.9 × 1.25 ≈ **2,236 VA**, so a 3 kVA unit would be chosen.

**`main()`**: reads the command-line options, calls the functions above and prints a report. "Generator bridge" compares the runtime in seconds with the generator start time.

## The tests (`tests/test_ups_runtime.py`)

Each test checks one answer worked out by hand, for example that 48 V × 100 Ah gives exactly 2,764.8 Wh usable, that sizing is the exact inverse of runtime, and that bad inputs are rejected. GitHub Actions runs them automatically on every change (the "tests" badge in the README).

## Likely interview questions

- **"Why not just buy the biggest battery?"** Cost, weight, space and replacement cost every few years. The generator carries long outages. The battery only needs to cover the generator start plus a safe shutdown.
- **"Why LiFePO4?"** More usable capacity (80% vs 50%), many more charge cycles, and better tolerance of heat and daily cycling. It costs more up front but less over its lifetime when outages happen every day.
- **"What does the model ignore?"** Lead-acid batteries deliver less than rated capacity at high discharge rates (the Peukert effect), and temperature affects capacity. That's why the result is treated as an estimate and checked against the vendor's runtime tables.
