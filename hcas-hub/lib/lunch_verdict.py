"""Lunch verdict logic — pure, unit-testable."""
from dataclasses import dataclass


@dataclass
class Verdict:
    label: str       # EAT_LUNCH | YOUR_CALL | ORDER_UBER
    headline: str    # short text shown on the card
    emoji: str
    color: str       # tailwind color name


def verdict_for(avg_rating: float | None, rating_count: int) -> Verdict:
    if avg_rating is None or rating_count < 5:
        return Verdict(
            label="YOUR_CALL",
            headline="Not enough ratings yet — try it and rate it",
            emoji="🤷",
            color="slate",
        )
    if avg_rating < 2.5:
        return Verdict(
            label="ORDER_UBER",
            headline="Order Uber Eats — this one's a miss",
            emoji="🚗",
            color="rose",
        )
    if avg_rating < 3.5:
        return Verdict(
            label="YOUR_CALL",
            headline="Your call — it's just okay",
            emoji="😐",
            color="amber",
        )
    return Verdict(
        label="EAT_LUNCH",
        headline="Eat the lunch — students rate this one",
        emoji="✅",
        color="emerald",
    )


# Self-test (run: python lib/lunch_verdict.py)
if __name__ == "__main__":
    cases = [
        (None, 0, "YOUR_CALL"),
        (4.5, 2, "YOUR_CALL"),         # too few ratings
        (1.8, 142, "ORDER_UBER"),
        (2.49, 50, "ORDER_UBER"),
        (2.5, 50, "YOUR_CALL"),
        (3.49, 50, "YOUR_CALL"),
        (3.5, 50, "EAT_LUNCH"),
        (4.6, 200, "EAT_LUNCH"),
    ]
    for r, n, want in cases:
        got = verdict_for(r, n).label
        assert got == want, f"verdict_for({r}, {n}) -> {got}, want {want}"
    print(f"all {len(cases)} verdict tests pass")
