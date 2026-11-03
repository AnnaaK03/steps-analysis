"""
Step analysis from Apple Health

What the program does:
  1. Reads the export.xml file (Apple Health export)
  2. Takes steps recorded by the iPhone only
  3. Calculates steps per day and prints statistics
  4. Draws five charts and saves them to the results/ folder
"""

from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import os
import xml.etree.ElementTree as ET

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # draw to files, no window

# ---------- Settings ----------
BASE_DIR = os.path.dirname(os.path.abspath(
    __file__))  # folder with this script
XML_FILE = os.path.join(BASE_DIR, "export.xml")        # Apple Health export
OUTPUT_DIR = os.path.join(BASE_DIR, "results")         # where charts are saved
PERSON = "Anna Kuran"                                  # name used in titles
GOAL = 8000                                            # daily step goal
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# years shown in the monthly chart
YEARS_TO_COMPARE = 3
# year shown in the weekday chart
WEEKDAY_YEAR = 2026


# ---------- 1. Loading data ----------
def load_steps(xml_file):
    """Reads the XML and returns a table: date + steps (iPhone only)."""
    records = []
    for _, element in ET.iterparse(xml_file):
        if element.tag == "Record":
            is_steps = element.get(
                "type") == "HKQuantityTypeIdentifierStepCount"
            from_iphone = "iPhone" in (element.get("device") or "")
            if is_steps and from_iphone:
                records.append({
                    "date": element.get("startDate")[:10],  # only "YYYY-MM-DD"
                    "steps": float(element.get("value")),
                })
        element.clear()  # free memory
    return pd.DataFrame(records)


def make_daily(records):
    """Adds up all records of one day into a single number."""
    daily = records.groupby("date")["steps"].sum()
    daily.index = pd.to_datetime(daily.index)
    return daily


# ---------- 2. Statistics ----------
def longest_streak(daily, goal):
    """Longest run of consecutive days when the goal was reached."""
    best = current = 0
    for steps in daily:
        if steps >= goal:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def print_statistics(daily):
    """Prints the main numbers to the console."""
    print(f"\n===== Step statistics: {PERSON} =====")
    print(f"Period: {daily.index.min().date()} to {daily.index.max().date()}")
    print(f"Days with data: {len(daily)}")
    print(f"Total steps: {daily.sum():,.0f}")
    print(f"Average per day: {daily.mean():,.0f}")
    print(f"Median: {daily.median():,.0f}")
    print(f"Best day: {daily.idxmax().date()} ({daily.max():,.0f} steps)")
    share = (daily >= GOAL).mean() * 100
    print(f"Days reaching {GOAL}+ steps: {share:.0f}%")
    print(f"Longest goal streak: {longest_streak(daily, GOAL)} days")


# ---------- 3. Charts ----------
def plot_summary(daily):
    """Chart 0: one compact summary slide - key numbers + podium of the best days."""
    fig = plt.figure(figsize=(12, 6))
    # one big canvas, coordinates from 0 to 100
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    # Title and period
    start, end = daily.index.min().date(), daily.index.max().date()
    ax.text(3, 55, f"Step summary - {PERSON}",
            fontsize=22, fontweight="bold", va="center")
    ax.text(3, 50.5, f"{start}  to  {end}",
            fontsize=13, color="gray", va="center")

    # Six number cards (2 rows x 3 columns)
    share = (daily >= GOAL).mean() * 100
    cards = [
        ("Total steps", f"{daily.sum():,.0f}"),
        ("Average per day", f"{daily.mean():,.0f}"),
        ("Median", f"{daily.median():,.0f}"),
        ("Days with data", f"{len(daily)}"),
        (f"Days with {GOAL}+ steps", f"{share:.0f}%"),
        ("Longest goal streak", f"{longest_streak(daily, GOAL)} days"),
    ]
    for i, (label, value) in enumerate(cards):
        x = 3 + (i % 3) * 20          # column
        y = 28 - (i // 3) * 19        # row
        box = FancyBboxPatch((x, y), 18, 16, boxstyle="round,pad=0.4",
                             facecolor="#EEF3FA", edgecolor="#B8C7DD")
        ax.add_patch(box)
        ax.text(x + 9, y + 10, value, fontsize=20, fontweight="bold",
                ha="center", va="center", color="#1F3B63")
        ax.text(x + 9, y + 3.5, label, fontsize=11,
                ha="center", va="center", color="gray")

    # Three best days
    top3 = daily.nlargest(3)                       # best day, 2nd, 3rd
    ax.text(82, 47, "Top 3 best days", fontsize=15,
            fontweight="bold", ha="center", va="center")
    #           x position, height, color,     place
    podium = [(70, 20, "#B0B0B0", 2),             # silver - on the left
              (82, 26, "#D4AF37", 1),             # gold   - in the middle
              (94, 15, "#CD7F32", 3)]             # bronze - on the right
    base = 8
    for x, height, color, place in podium:
        day, steps = top3.index[place - 1], top3.iloc[place - 1]
        ax.add_patch(plt.Rectangle((x - 5.5, base), 11, height,
                     facecolor=color, edgecolor="white"))
        ax.text(x, base + height / 2, str(place), fontsize=26,
                fontweight="bold", color="white", ha="center", va="center")
        ax.text(x, base + height + 3.8,
                f"{steps:,.0f}", fontsize=13, fontweight="bold", ha="center", va="center")
        ax.text(x, base + height + 1.4, str(day.date()),
                fontsize=9.5, color="gray", ha="center", va="center")

    plt.savefig(os.path.join(OUTPUT_DIR, "0_summary.png"),
                dpi=150, facecolor="white")
    plt.close()


def plot_trend(daily):
    """Chart 1: steps per day for all years + 30-day average."""
    plt.figure(figsize=(12, 5))
    plt.plot(daily.index, daily, color="lightsteelblue",
             linewidth=0.6, label="Steps per day")
    plt.plot(daily.index, daily.rolling(30).mean(),
             color="darkblue", linewidth=2, label="30-day average")
    plt.axhline(GOAL, color="green", linestyle="--", label=f"Goal {GOAL}")
    plt.title(f"Daily steps, all years - {PERSON}")
    plt.ylabel("Steps")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "1_trend.png"), dpi=150)
    plt.close()


def plot_years(daily):
    """Chart 2: average steps by year (all years)."""
    by_year = daily.groupby(daily.index.year).mean()
    plt.figure(figsize=(8, 5))
    plt.bar(by_year.index.astype(str), by_year.values, color="darkorange")
    plt.axhline(GOAL, color="green", linestyle="--", label=f"Goal {GOAL}")
    plt.title("Average steps by year")
    plt.ylabel("Steps")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "2_years.png"), dpi=150)
    plt.close()


def plot_months(daily):
    """Chart 3: average steps by month, compared across the last few years."""
    monthly = daily.groupby([daily.index.year, daily.index.month]).mean()
    # rows = months, columns = years
    table = monthly.unstack(0)
    # keep only the last years
    table = table[table.columns[-YEARS_TO_COMPARE:]]
    table.index = [MONTHS[m - 1] for m in table.index]
    table.plot(kind="bar", figsize=(11, 5), width=0.8)
    plt.axhline(GOAL, color="green", linestyle="--", label=f"Goal {GOAL}")
    plt.title(f"Average steps by month, last {YEARS_TO_COMPARE} years")
    plt.ylabel("Steps")
    plt.xticks(rotation=0)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "3_months.png"), dpi=150)
    plt.close()


def plot_weekdays(daily):
    """Chart 4: average steps by day of the week in one chosen year."""
    year_data = daily[daily.index.year == WEEKDAY_YEAR]
    by_day = year_data.groupby(year_data.index.dayofweek).mean()
    plt.figure(figsize=(8, 5))
    plt.bar(DAYS, by_day.values, color="steelblue", label=str(WEEKDAY_YEAR))
    plt.axhline(GOAL, color="green", linestyle="--", label=f"Goal {GOAL}")
    plt.title(f"Average steps by day of the week, {WEEKDAY_YEAR}")
    plt.ylabel("Steps")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "4_weekdays.png"), dpi=150)
    plt.close()


# ---------- Main part ----------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Reading data (this may take about a minute)...")
    records = load_steps(XML_FILE)
    daily = make_daily(records)

    print_statistics(daily)

    plot_summary(daily)
    plot_trend(daily)
    plot_years(daily)
    plot_months(daily)
    plot_weekdays(daily)


if __name__ == "__main__":
    main()

