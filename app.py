"""
Streamlit Web Application for Fire AI Take-Home Assignment Project A.
Run with: streamlit run app.py
"""

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def run_streamlit_app():
    if not STREAMLIT_AVAILABLE:
        print("Streamlit is not installed in the current environment.")
        print("Please install via: pip install streamlit")
        print("Alternatively, run the interactive CLI via: python cli.py")
        return

    from project_a.models.user_input import TaxpayerInput
    from project_a.parsers.input_parser import parse_natural_language_input
    from project_a.calculators.tax_engine import calculate_income_tax, compare_regimes
    from project_a.llm.compiled_rules_engine import CompiledRulesTaxEngine

    st.set_page_config(
        page_title="Fire AI - Indian Salaried Tax Engine",
        page_icon="💰",
        layout="wide",
    )

    st.title("💰 Fire AI - Indian Salaried Income Tax Engine")
    st.caption("Rules vs LLMs: Deterministic Accuracy • Statutory Traceability • FY 2024-25 & 2025-26")

    tabs = st.tabs([
        "💬 Natural Language Assistant",
        "🧮 Interactive Calculator & Comparison",
        "⚖️ FY 2024-25 vs FY 2025-26 Law Change",
        "📊 Engine Benchmarks & Audit Trail"
    ])

    # --- TAB 1: Natural Language ---
    with tabs[0]:
        st.subheader("Natural Language Tax Description")
        st.write("Describe your income, rent, city, and investments in English or Hinglish.")

        sample_prompts = [
            "My salary is 12 lakh, I live in Mumbai, pay 25k rent monthly, and invested 1.5 lakh in PPF. Old regime, FY 2024-25.",
            "Meri salary 10 lakh hai aur rent 20k per month hai, old regime, FY 2024-25.",
            "Salary 15 lakh, new regime, FY 2024-25.",
            "Package 14 lakh hai naye regime me calculate karo FY 2025-26.",
            "Salary 9L, 80C 1.2L, parents senior citizens, medical insurance 40000, old regime, FY 2024-25."
        ]
        selected_sample = st.selectbox("Or choose a sample query:", [""] + sample_prompts)
        user_query = st.text_area(
            "Enter your description:",
            value=selected_sample if selected_sample else "",
            placeholder="e.g. My salary is 12 lakh, I pay 25k monthly rent in Mumbai..."
        )

        if st.button("Parse & Calculate Tax", key="nl_btn"):
            if not user_query.strip():
                st.warning("Please enter a query.")
            else:
                parse_res = parse_natural_language_input(user_query)

                if parse_res.status == "clarification_needed":
                    st.warning("⚠️ Additional Information Required")
                    for q in parse_res.clarification_questions:
                        st.markdown(f"- **{q}**")
                    if parse_res.detected_entities:
                        with st.expander("Detected Parameters"):
                            st.json(parse_res.detected_entities)

                elif parse_res.status == "contradiction_detected":
                    st.error("❌ Contradiction or Ambiguity Detected")
                    for q in parse_res.clarification_questions:
                        st.markdown(f"- **{q}**")

                elif parse_res.status == "error":
                    st.error(f"Error parsing input: {parse_res.clarification_questions}")

                elif parse_res.status == "success":
                    st.success("✅ Successfully Parsed Taxpayer Profile")
                    tp = parse_res.taxpayer_input

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Profile Summary")
                        st.write(f"**Gross Salary:** ₹{tp.gross_salary:,.0f}")
                        st.write(f"**Regime:** {tp.regime.upper()}")
                        st.write(f"**Financial Year:** {tp.financial_year}")
                        st.write(f"**City:** {tp.city_type.capitalize()}")

                    comp = compare_regimes(tp)
                    with col2:
                        st.markdown("### Recommendation")
                        st.metric(
                            label=f"Recommended: {comp['recommended_regime'].upper()} Regime",
                            value=f"Save ₹{comp['savings']:,.0f}" if comp["savings"] > 0 else "Equal Tax"
                        )
                        st.info(comp["reason"])

                    # Breakdown
                    res = calculate_income_tax(tp)
                    st.markdown("### Step-by-Step Statutory Breakdown")
                    st.table({
                        "Metric": [
                            "Gross Salary", "Standard Deduction", "HRA Exemption", "Section 80C",
                            "Section 80CCD(1B)", "Section 80D", "Home Loan Interest", "Total Deductions",
                            "Taxable Income (Sec 288A)", "Tax before Rebate", "Section 87A Rebate",
                            "Tax after Rebate", "Surcharge", "Cess (4%)", "Final Tax (Sec 288B)"
                        ],
                        "Amount (₹)": [
                            f"₹{res['gross_salary']:,.2f}",
                            f"₹{res['standard_deduction']:,.2f}",
                            f"₹{res['hra_exemption']:,.2f}",
                            f"₹{res['section_80c']:,.2f}",
                            f"₹{res['section_80ccd_1b']:,.2f}",
                            f"₹{res['section_80d']:,.2f}",
                            f"₹{res['home_loan_deduction']:,.2f}",
                            f"₹{res['total_deductions']:,.2f}",
                            f"₹{res['taxable_income']:,.2f}",
                            f"₹{res['tax_before_rebate']:,.2f}",
                            f"₹{res['rebate_87a']:,.2f}",
                            f"₹{res['tax_after_rebate']:,.2f}",
                            f"₹{res.get('surcharge_amount', 0):,.2f}",
                            f"₹{res['cess']:,.2f}",
                            f"₹{res['final_tax']:,}",
                        ]
                    })

                    with st.expander("Legal Audit Trail"):
                        for step in res["traceability"]:
                            st.write(f"✓ {step}")

    # --- TAB 2: Interactive Calculator ---
    with tabs[1]:
        st.subheader("Manual Taxpayer Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            gross = st.number_input("Gross Annual Salary (₹)", min_value=0.0, value=1200000.0, step=50000.0)
            regime = st.selectbox("Selected Regime", ["new", "old"])
            fy = st.selectbox("Financial Year", ["2024-25", "2025-26"])
        with c2:
            st.markdown("**HRA Inputs (Old Regime only)**")
            basic = st.number_input("Basic Salary (₹)", min_value=0.0, value=600000.0, step=50000.0)
            hra_rec = st.number_input("HRA Received (₹)", min_value=0.0, value=200000.0, step=25000.0)
            rent = st.number_input("Annual Rent Paid (₹)", min_value=0.0, value=180000.0, step=20000.0)
            city = st.selectbox("City Type", ["metro", "non_metro"])
        with c3:
            st.markdown("**Deductions (Old Regime only)**")
            c_80 = st.number_input("Section 80C (PPF/EPF/ELSS) (₹)", min_value=0.0, value=150000.0, max_value=500000.0, step=10000.0)
            nps = st.number_input("Section 80CCD(1B) NPS (₹)", min_value=0.0, value=50000.0, max_value=100000.0, step=10000.0)
            med = st.number_input("Section 80D Health Insurance (₹)", min_value=0.0, value=25000.0, step=5000.0)
            hl = st.number_input("Section 24(b) Home Loan Interest (₹)", min_value=0.0, value=200000.0, step=25000.0)

        tp_manual = TaxpayerInput(
            gross_salary=gross,
            regime=regime,
            financial_year=fy,
            basic_salary=basic,
            hra_received=hra_rec,
            annual_rent=rent,
            city_type=city,
            section_80c=c_80,
            section_80ccd_1b=nps,
            self_family_medical=med,
            home_loan_interest=hl
        )

        comp_manual = compare_regimes(tp_manual)
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Old Regime Tax", f"₹{comp_manual['old_regime']['final_tax']:,}")
        with col_res2:
            st.metric("New Regime Tax", f"₹{comp_manual['new_regime']['final_tax']:,}")

        st.info(f"**Recommendation:** {comp_manual['reason']}")

    # --- TAB 3: Law Change Simulator ---
    with tabs[2]:
        st.subheader("Budget Law Change Exercise: FY 2024-25 vs FY 2025-26")
        st.write("Examine the direct impact of the revised New Tax Regime slabs and enhanced Section 87A rebate (up to ₹12 Lakh).")

        sim_salary = st.slider("Select Gross Salary for Comparison", min_value=500000, max_value=2500000, value=1275000, step=25000)

        tp24 = TaxpayerInput(gross_salary=sim_salary, regime="new", financial_year="2024-25")
        tp25 = TaxpayerInput(gross_salary=sim_salary, regime="new", financial_year="2025-26")

        r24 = calculate_income_tax(tp24)
        r25 = calculate_income_tax(tp25)
        savings = r24["final_tax"] - r25["final_tax"]

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("FY 2024-25 Tax Liability", f"₹{r24['final_tax']:,}")
        with m2:
            st.metric("FY 2025-26 Tax Liability", f"₹{r25['final_tax']:,}")
        with m3:
            st.metric("Tax Relief / Savings", f"₹{savings:,}", delta=f"-₹{savings:,}" if savings > 0 else "0")

    # --- TAB 4: Benchmarks ---
    with tabs[3]:
        st.subheader("Engine Benchmarks & Reproducibility")
        try:
            with open("benchmark_results.json", "r") as f:
                b_data = json.load(f)
            st.json(b_data)
        except Exception:
            st.info("Run `python -m project_a.benchmarks.benchmark_runner` to generate benchmark_results.json.")


if __name__ == "__main__":
    if STREAMLIT_AVAILABLE:
        run_streamlit_app()
    else:
        print("Streamlit not installed. Running CLI demonstration instead...")
        from cli import main
        main()

