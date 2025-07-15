#!/usr/bin/env python3
"""
Mathematical Analysis of Rounding Errors in NESTA vs Ofgem Rate Calculations

This script explores whether rounding errors in monetary figures (£ to 2 decimal places)
and rate calculations (pence/kWh to 2 decimal places) could explain the observed
discrepancies between NESTA calculated rates and Ofgem published rates.

Key discrepancies observed:
- Electricity variable rate: NESTA 25.64p/kWh vs Ofgem 25.73p/kWh = 0.088p/kWh difference
- Gas variable rate: NESTA 6.34p/kWh vs Ofgem 6.33p/kWh = 0.011p/kWh difference
- Electricity standing charge: NESTA 51.21p/day vs Ofgem 51.37p/day = 0.16p/day difference
- Gas standing charge: NESTA 29.67p/day vs Ofgem 29.82p/day = 0.15p/day difference
"""

import math

print("🔢 MATHEMATICAL ANALYSIS OF ROUNDING ERRORS")
print("="*80)

# Typical household consumption
elec_kwh = 2700  # kWh per year
gas_kwh = 11500  # kWh per year

print(f"Typical household consumption:")
print(f"  Electricity: {elec_kwh:,} kWh/year")
print(f"  Gas: {gas_kwh:,} kWh/year")
print()

# Observed discrepancies
elec_rate_diff = 0.088  # p/kWh (25.73 - 25.64)
gas_rate_diff = 0.011   # p/kWh (6.34 - 6.33)
elec_standing_diff = 0.16  # p/day (51.37 - 51.21)
gas_standing_diff = 0.15   # p/day (29.82 - 29.67)

print("🔍 OBSERVED DISCREPANCIES:")
print(f"  Electricity variable rate: {elec_rate_diff:.3f}p/kWh")
print(f"  Gas variable rate: {gas_rate_diff:.3f}p/kWh")
print(f"  Electricity standing charge: {elec_standing_diff:.2f}p/day")
print(f"  Gas standing charge: {gas_standing_diff:.2f}p/day")
print()

print("📊 ROUNDING ERROR ANALYSIS")
print("="*50)

print("\n1. MAXIMUM ROUNDING ERRORS:")
print("   When rounding to 2 decimal places:")
print("   - £ values: ±£0.005 maximum error")
print("   - p/kWh values: ±0.005p/kWh maximum error")
print("   - p/day values: ±0.005p/day maximum error")

# Calculate impact of £ rounding on derived rates
print("\n2. IMPACT OF £ ROUNDING ON DERIVED RATES:")
annual_cost_error = 0.005  # £

elec_rate_error_from_cost = (annual_cost_error * 100) / elec_kwh  # Convert £ to p and divide by kWh
gas_rate_error_from_cost = (annual_cost_error * 100) / gas_kwh

print(f"   If annual cost rounded to ±£{annual_cost_error:.3f}:")
print(f"   → Electricity rate error: ±{elec_rate_error_from_cost:.4f}p/kWh")
print(f"   → Gas rate error: ±{gas_rate_error_from_cost:.4f}p/kWh")

# Calculate impact of p/kWh rounding on annual costs
print("\n3. IMPACT OF p/kWh ROUNDING ON ANNUAL COSTS:")
rate_error = 0.005  # p/kWh

elec_annual_error_from_rate = (rate_error * elec_kwh) / 100  # Convert p to £
gas_annual_error_from_rate = (rate_error * gas_kwh) / 100

print(f"   If rate rounded to ±{rate_error:.3f}p/kWh:")
print(f"   → Electricity annual cost error: ±£{elec_annual_error_from_rate:.3f}")
print(f"   → Gas annual cost error: ±£{gas_annual_error_from_rate:.3f}")

print("\n4. COMPARISON WITH OBSERVED DISCREPANCIES:")
print("-" * 50)

def assess_rounding_explanation(observed_diff, max_rounding_error, name):
    """Assess whether rounding could explain observed difference"""
    total_max_error = 2 * max_rounding_error  # Both NESTA and Ofgem could have rounding errors
    could_explain = abs(observed_diff) <= total_max_error

    print(f"\n   {name}:")
    print(f"   • Observed difference: {observed_diff:+.3f}")
    print(f"   • Maximum single rounding error: ±{max_rounding_error:.3f}")
    print(f"   • Maximum combined error (both sides): ±{total_max_error:.3f}")
    print(f"   • Could rounding explain this? {'YES' if could_explain else 'NO'}")

    if could_explain:
        # Calculate what the true values would need to be
        midpoint = observed_diff / 2
        print(f"   • Possible scenario:")
        print(f"     - True Ofgem value: X + {midpoint:.3f}")
        print(f"     - True NESTA value: X - {midpoint:.3f}")
        print(f"     - Both round to nearest 0.01, creating observed difference")

    return could_explain

# Assess each discrepancy
elec_rate_explained = assess_rounding_explanation(elec_rate_diff, 0.005, "Electricity variable rate")
gas_rate_explained = assess_rounding_explanation(gas_rate_diff, 0.005, "Gas variable rate")
elec_standing_explained = assess_rounding_explanation(elec_standing_diff, 0.005, "Electricity standing charge")
gas_standing_explained = assess_rounding_explanation(gas_standing_diff, 0.005, "Gas standing charge")

print(f"\n{'='*60}")
print("📋 SUMMARY OF ROUNDING ERROR ANALYSIS")
print("="*60)

explanations = {
    "Electricity variable rate": elec_rate_explained,
    "Gas variable rate": gas_rate_explained,
    "Electricity standing charge": elec_standing_explained,
    "Gas standing charge": gas_standing_explained
}

for component, explained in explanations.items():
    status = "✅ COULD BE ROUNDING" if explained else "❌ EXCEEDS ROUNDING"
    print(f"  {component:<25}: {status}")

print(f"\nCan rounding explain ALL discrepancies? {'YES' if all(explanations.values()) else 'NO'}")

if not all(explanations.values()):
    print("\n🔍 DISCREPANCIES THAT EXCEED SIMPLE ROUNDING ERRORS:")
    for component, explained in explanations.items():
        if not explained:
            print(f"  • {component}")
    print("\nThese require investigation beyond rounding errors:")
    print("  - Different data sources")
    print("  - Different calculation methodologies")
    print("  - Different treatment of policy costs")
    print("  - Systematic differences in base rates")

print(f"\n{'='*60}")
print("🧮 CASCADING ROUNDING ERROR ANALYSIS")
print("="*60)

print("\nCould MULTIPLE rounding steps create larger cumulative errors?")
print("\nExample calculation chain:")
print("1. Policy costs calculated from individual levies")
print("2. Each levy contribution rounded to 2 decimal places")
print("3. Policy costs summed and rounded again")
print("4. Added to base costs and rounded")
print("5. Final rate calculation and rounding")

# Simulate cascading rounding with 5 steps
n_steps = 5
max_error_per_step = 0.005
max_cumulative_error = n_steps * max_error_per_step

print(f"\nWith {n_steps} rounding steps:")
print(f"  Maximum error per step: ±{max_error_per_step:.3f}p/kWh")
print(f"  Worst-case cumulative error: ±{max_cumulative_error:.3f}p/kWh")
print(f"  Could explain {elec_rate_diff:.3f}p/kWh electricity difference? {'YES' if elec_rate_diff <= max_cumulative_error else 'NO'}")

# Statistical approach - random walk of rounding errors
import random
random.seed(42)

print(f"\n🎯 MONTE CARLO SIMULATION:")
print("Simulating 10,000 calculation chains with random rounding at each step...")

simulation_results = []
for _ in range(10000):
    cumulative_error = 0
    for step in range(n_steps):
        # Random rounding error between -0.005 and +0.005
        step_error = random.uniform(-0.005, 0.005)
        cumulative_error += step_error
    simulation_results.append(abs(cumulative_error))

# Calculate percentiles
simulation_results.sort()
p95 = simulation_results[int(0.95 * len(simulation_results))]
p99 = simulation_results[int(0.99 * len(simulation_results))]
maximum = max(simulation_results)

print(f"  95th percentile absolute error: {p95:.3f}p/kWh")
print(f"  99th percentile absolute error: {p99:.3f}p/kWh")
print(f"  Maximum observed error: {maximum:.3f}p/kWh")

print(f"\n  Could cascading rounding explain {elec_rate_diff:.3f}p/kWh difference?")
print(f"  • 95% confidence: {'YES' if elec_rate_diff <= p95 else 'NO'}")
print(f"  • 99% confidence: {'YES' if elec_rate_diff <= p99 else 'NO'}")

print(f"\n{'='*60}")
print("🏁 FINAL CONCLUSION")
print("="*60)

if all(explanations.values()):
    print("✅ ALL observed discrepancies could be explained by simple rounding errors.")
    print("   The differences may be due to:")
    print("   • Different rounding practices between NESTA and Ofgem")
    print("   • Timing of rounding in calculation chain")
    print("   • Precision differences in intermediate calculations")
elif elec_rate_diff <= p99:
    print("⚠️  MIXED RESULTS:")
    print("   • Some discrepancies explainable by simple rounding")
    print("   • Electricity variable rate difference could be cascading rounding")
    print("   • Standing charge differences may require further investigation")
else:
    print("❌ ROUNDING ALONE CANNOT EXPLAIN ALL DISCREPANCIES")
    print("   The observed differences suggest:")
    print("   • Systematic methodological differences")
    print("   • Different underlying data sources")
    print("   • Different treatment of policy costs or base rates")
    print("   • More than just rounding precision issues")

print(f"\nRecommendation: {'Focus on rounding precision and calculation order' if all(explanations.values()) or elec_rate_diff <= p99 else 'Investigate fundamental methodological differences'}")