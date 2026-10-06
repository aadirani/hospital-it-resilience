"""UPS battery runtime and sizing calculator for a small server room.

Answers three planning questions:
  1. How long will this battery bank carry this load?
  2. How big must the bank be to carry the load for a target time?
  3. Does the battery bridge the gap until the generator takes over?

Standard library only. Results are planning estimates; always confirm
against the UPS vendor's runtime tables before buying.
"""

import argparse
import csv
from dataclasses import dataclass

# Share of the rated capacity you can use regularly without killing the battery early.
DEPTH_OF_DISCHARGE = {
    "lead-acid": 0.5,
    "lifepo4": 0.8,
}


@dataclass
class Battery:
    voltage: float                     # nominal bank voltage, volts
    capacity_ah: float                 # rated capacity, amp-hours
    chemistry: str = "lifepo4"
    inverter_efficiency: float = 0.9   # energy lost converting DC battery power to AC
    aging_factor: float = 0.8          # capacity left near end of battery life

    def __post_init__(self):
        if self.chemistry not in DEPTH_OF_DISCHARGE:
            raise ValueError(f"unknown chemistry: {self.chemistry}")
        if self.voltage <= 0 or self.capacity_ah <= 0:
            raise ValueError("voltage and capacity must be positive")

    def usable_wh(self) -> float:
        """Energy (watt-hours) the bank can actually deliver to the load."""
        return (self.voltage * self.capacity_ah
                * DEPTH_OF_DISCHARGE[self.chemistry]
                * self.inverter_efficiency * self.aging_factor)


def load_from_csv(path: str) -> float:
    """Total load in watts from a CSV with columns: device, quantity, watts."""
    with open(path, newline="", encoding="utf-8") as f:
        return sum(int(row["quantity"]) * float(row["watts"])
                   for row in csv.DictReader(f))


def runtime_minutes(battery: Battery, load_w: float) -> float:
    if load_w <= 0:
        raise ValueError("load must be positive")
    return battery.usable_wh() / load_w * 60


def required_capacity_ah(load_w: float, minutes: float, voltage: float,
                         chemistry: str = "lifepo4",
                         inverter_efficiency: float = 0.9,
                         aging_factor: float = 0.8) -> float:
    """Smallest capacity (Ah) that carries load_w for the given minutes."""
    one_ah = Battery(voltage, 1, chemistry, inverter_efficiency, aging_factor)
    return (load_w * minutes / 60) / one_ah.usable_wh()


def required_ups_va(load_w: float, power_factor: float = 0.9,
                    headroom: float = 0.25) -> float:
    """UPS rating (VA) for the load, with headroom for growth."""
    return load_w / power_factor * (1 + headroom)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--load-csv", required=True, help="CSV with device,quantity,watts")
    p.add_argument("--voltage", type=float, required=True, help="battery bank voltage (V)")
    p.add_argument("--capacity-ah", type=float, required=True, help="battery bank capacity (Ah)")
    p.add_argument("--chemistry", choices=sorted(DEPTH_OF_DISCHARGE), default="lifepo4")
    p.add_argument("--target-minutes", type=float, default=15,
                   help="runtime the design must reach (default 15)")
    p.add_argument("--generator-start-seconds", type=float, default=60,
                   help="time for the generator to start and the switch to transfer (default 60)")
    args = p.parse_args(argv)

    load_w = load_from_csv(args.load_csv)
    battery = Battery(args.voltage, args.capacity_ah, args.chemistry)
    runtime = runtime_minutes(battery, load_w)
    needed_ah = required_capacity_ah(load_w, args.target_minutes, args.voltage, args.chemistry)
    bridge_margin = runtime * 60 - args.generator_start_seconds

    print(f"Total load:            {load_w:,.0f} W")
    print(f"Suggested UPS rating:  {required_ups_va(load_w):,.0f} VA")
    print(f"Usable battery energy: {battery.usable_wh():,.0f} Wh ({args.chemistry})")
    print(f"Estimated runtime:     {runtime:,.1f} min")
    print(f"Needed for {args.target_minutes:g} min:    {needed_ah:,.0f} Ah at {args.voltage:g} V")
    print(f"Target met:            {'YES' if runtime >= args.target_minutes else 'NO'}")
    print(f"Generator bridge:      {'OK' if bridge_margin > 0 else 'FAILS'}"
          f" ({bridge_margin:,.0f} s spare)")


if __name__ == "__main__":
    main()
