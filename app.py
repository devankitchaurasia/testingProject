import streamlit as st
import pandas as pd
import json

from utils.ai_helper import ask_ai

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="AI Data Analyst",
    layout="wide"
)

st.title("📊 AI Data Analyst Assistant")


# =========================================
# QUERY EXECUTION ENGINE
# =========================================

def process_query(df, query):

    intent = query.get("intent")
    operation = query.get("operation")
    column = query.get("column")
    group_by = query.get("group_by")
    chart = query.get("chart")
    top_n = query.get("top_n")
    sort = query.get("sort", "desc")

    # Convert numeric column safely
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    result = None

    # =====================================
    # AGGREGATION / COMPARISON / TREND
    # =====================================

    if intent in ["aggregation", "comparison", "trend"]:

        if group_by:

            grouped = df.groupby(group_by)[column]

            if operation == "sum":
                result = grouped.sum()

            elif operation == "average":
                result = grouped.mean()

            elif operation == "count":
                result = grouped.count()

            elif operation == "max":
                result = grouped.max()

            elif operation == "min":
                result = grouped.min()

            result = result.reset_index()

            # Rename output column
            result.columns = [group_by, column]

        else:

            if operation == "sum":
                result = df[column].sum()

            elif operation == "average":
                result = df[column].mean()

            elif operation == "count":
                result = df[column].count()

            elif operation == "max":
                result = df[column].max()

            elif operation == "min":
                result = df[column].min()

    # =====================================
    # APPLY TOP N
    # =====================================

    if isinstance(result, pd.DataFrame) and top_n:

        result = result.sort_values(
            by=column,
            ascending=(sort == "asc")
        ).head(top_n)

    return result, chart


# =========================================
# FILE UPLOAD
# =========================================

uploaded_file = st.file_uploader(
    "Upload CSV or Excel File",
    type=["csv", "xlsx"]
)

# =========================================
# MAIN APP
# =========================================

if uploaded_file:

    # Read file safely
    if uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(
            uploaded_file,
            dtype=str
        )

    else:

        df = pd.read_excel(
            uploaded_file,
            dtype=str
        )

    # Clean dataframe
    df = df.fillna("")
    df = df.astype(str)

    # =====================================
    # DATA PREVIEW
    # =====================================

    st.subheader("📁 Dataset Preview")

    st.dataframe(df.head())

    st.write(f"Rows: {df.shape[0]}")
    st.write(f"Columns: {df.shape[1]}")

    # =====================================
    # USER QUESTION
    # =====================================

    question = st.text_input(
        "Ask question about your data"
    )

    # =====================================
    # AI PROCESSING
    # =====================================

    if question:

        prompt = f"""
                You are an AI data analyst.

                Dataset columns:
                {list(df.columns)}

                User Question:
                {question}

                Your task:
                Understand the business intent and return ONLY JSON.

                JSON format:

                {{
                "intent": "aggregation",
                "operation": "sum",
                "column": "Sales",
                "group_by": "Buyer",
                "chart": "bar",
                "top_n": 5,
                "sort": "desc",
                "filters": []
                }}

                Possible intents:
                - aggregation
                - comparison
                - trend
                - summary

                Allowed operations:
                - sum
                - average
                - count
                - max
                - min

                Allowed charts:
                - bar
                - line
                - pie
                - none

                IMPORTANT:
                - Return ONLY valid JSON
                - No explanation
                - No markdown
                """

        with st.spinner("🤖 AI analyzing data..."):

            answer = ask_ai(prompt)

            try:

                # =========================
                # PARSE AI JSON
                # =========================

                query = json.loads(answer)

                # =========================
                # EXECUTE QUERY
                # =========================

                result, chart = process_query(df, query)

                # =========================
                # SHOW RESULT
                # =========================

                st.subheader("📊 Analysis Result")

                if isinstance(result, pd.DataFrame):

                    st.dataframe(result)

                else:

                    st.metric(
                        label=f"{query['operation']} of {query['column']}",
                        value=result
                    )

                # =========================
                # CHARTS
                # =========================

                if (
                    isinstance(result, pd.DataFrame)
                    and query.get("group_by")
                ):

                    chart_data = result.set_index(
                        query["group_by"]
                    )

                    if chart == "bar":

                        st.subheader("📈 Bar Chart")

                        st.bar_chart(chart_data)

                    elif chart == "line":

                        st.subheader("📉 Line Chart")

                        st.line_chart(chart_data)

                # =========================
                # AI INSIGHT
                # =========================

                st.subheader("💡 AI Insight")

                if isinstance(result, pd.DataFrame):

                    top_row = result.iloc[0]

                    st.write(
                        f"""
                        Analysis completed successfully.

                        The query analyzed
                        '{query['column']}'
                        grouped by
                        '{query['group_by']}'.

                        Top result:
                        {top_row[query['group_by']]}
                        with value
                        {top_row[query['column']]}.
                        """
                    )

                else:

                    st.write(
                        f"""
                        The {query['operation']}
                        of {query['column']}
                        is {result}.
                        """
                    )

            except Exception as e:

                st.error(f"❌ Error: {e}")

                st.write("AI Raw Response:")

                st.code(answer)