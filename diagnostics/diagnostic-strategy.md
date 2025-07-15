Created 14/07/2025

# Model narrative
https://medium.com/data-analytics-at-nesta/a-model-for-experimenting-with-energy-bills-rebalancing-levies-with-python-and-streamlit-08182638e8fc

# Notebook files to demonstrate model logic (note dates!)
2025-06-24 asf_levies_model/notebooks/testing_tariff_update.py
2025-02-11 asf_levies_model/notebooks/consumer_collection_example.py
2025-02-05 asf_levies_model/notebooks/levy_collection_Example.py
2025-01-27 asf_levies_model/notebooks/consumer_class_example.py
2025-01-17 asf_levies_model/notebooks/eco4_and_gbis_levies.py
2024-12-23 asf_levies_model/notebooks/report_scenarios_summary_v2.py
2024-11-14 asf_levies_model/notebooks/report_scenarios_summary.py
2024-11-04 asf_levies_model/notebooks/consumption_distribution_exploration.py
2024-10-28 asf_levies_model/notebooks/price_ratio_increments.py
2024-09-12 asf_levies_model/notebooks/price_ratio_calculation_example.py
2024-09-12 asf_levies_model/notebooks/model_example.py
2024-09-05 asf_levies_model/notebooks/model_example_with_outputs.py
2024-08-19 asf_levies_model/notebooks/model_development.py
2024-08-19 asf_levies_model/notebooks/Denominator_Exploration.py
2024-07-30 asf_levies_model/notebooks/README.md


Based on the complexity of this energy levy rebalancing model and your previous attempts, here's a strategic approach to build the LLM agent's context window systematically:

## **Phase 1: Foundation & Core Architecture** 
Start with the fundamental building blocks to establish domain understanding:

1. **Read the foundational files first:**
   ```bash
   # Start with the README and core documentation
   asf_levies_model/notebooks/README.md
   asf_levies_model/notebooks/archetypes.md
   ```

2. **Early model development** (chronological approach):
   ```bash
   # Original prototyping - builds mental model
   asf_levies_model/notebooks/model_development.py
   asf_levies_model/notebooks/Denominator_Exploration.py
   ```

## **Phase 2: Core Model Understanding**
Build understanding of the OOP architecture mentioned in the Medium article:

3. **Basic model structure:**
   ```bash
   asf_levies_model/notebooks/model_example.py
   asf_levies_model/notebooks/model_example_with_outputs.py
   ```

4. **Key class implementations:**
   ```bash
   # Consumer class - represents household archetypes
   asf_levies_model/notebooks/consumer_class_example.py
   
   # Levy collection - how levies are structured
   asf_levies_model/notebooks/levy_collection_Example.py
   
   # Consumer collection - how households are grouped
   asf_levies_model/notebooks/consumer_collection_example.py
   ```

## **Phase 3: Specific Levy Types**
Understand the specific policy schemes:

5. **Specific levy implementations:**
   ```bash
   asf_levies_model/notebooks/eco4_and_gbis_levies.py
   ```

## **Phase 4: Analysis & Applications**
Once core model is understood, move to analysis:

6. **Scenario analysis:**
   ```bash
   asf_levies_model/notebooks/report_scenarios_summary.py
   asf_levies_model/notebooks/report_scenarios_summary_v2.py
   ```

7. **Price ratio calculations:**
   ```bash
   asf_levies_model/notebooks/price_ratio_calculation_example.py
   asf_levies_model/notebooks/price_ratio_increments.py
   ```

## **Phase 5: Latest Developments**
Finally, the most recent work:

8. **Latest tariff work:**
   ```bash
   asf_levies_model/notebooks/testing_tariff_update.py  # Most recent (June 24, 2025)
   ```

## **Context Building Strategy:**

### **For Each Phase:**
1. **Read files in small chunks** (200-300 lines at a time)
2. **Extract key concepts** before moving to next file
3. **Build a glossary** of domain terms (levy, tariff, archetype, etc.)
4. **Map relationships** between classes/objects
5. **Identify the data flow** through the model

### **Key Questions to Address Systematically:**
- What are the core classes and their relationships?
- How are levies currently structured?
- What does "rebalancing" mean in practice?
- How are different household types represented?
- What are the key metrics/outputs?

### **Avoid Context Overload:**
- **Don't load all files at once**
- **Focus on understanding one concept fully before moving on**
- **Use the chronological development** (git log order) to understand evolution
- **Start with examples/demonstrations** rather than core library code

### **Critical Success Factors:**
1. **Domain vocabulary first** - understand energy policy terms
2. **Object relationships** - map the OOP structure clearly  
3. **Data flow understanding** - how inputs become outputs
4. **Incremental complexity** - build understanding layer by layer

This systematic approach should prevent the complexity from overwhelming the agent while building comprehensive understanding of the tariff rebalancing model.


------


