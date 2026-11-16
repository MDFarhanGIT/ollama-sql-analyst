import json
import re
import sqlite3

import ollama
import streamlit as st

MODEL = "qwen2.5:1.5b"

SALES = [
    ("2026-01-05", "Asha", "North", "Laptop", 2, 65000),
    ("2026-01-08", "Ravi", "South", "Phone", 5, 18000),
    ("2026-01-12", "Asha", "North", "Phone", 3, 18000),
    ("2026-01-16", "Meera", "West", "Laptop", 1, 65000),
    ("2026-01-20", "Ravi", "South", "Tablet", 4, 25000),
    ("2026-02-02", "Meera", "West", "Phone", 6, 18000),
    ("2026-02-07", "Asha", "North", "Tablet", 2, 25000),
    ("2026-02-11", "Ravi", "South", "Laptop", 1, 65000),
    ("2026-02-18", "Meera", "West", "Tablet", 3, 25000),
    ("2026-02-22", "Asha", "North", "Laptop", 1, 65000),
]

st.set_page_config(page_title="Local Sales Analyst", page_icon="📊")
st.title("Local Sales Analyst")
st.caption("Ask questions about sample sales data. The app runs locally.")

with st.expander("View the sample sales data"):
    st.dataframe(
        [
            {
                "sale_date": row[0],
                "salesperson": row[1],
                "region": row[2],
                "product": row[3],
                "quantity": row[4],
                "unit_price": row[5],
            }
            for row in SALES
        ],
        width="stretch",
        hide_index=True,
    )

if "history" not in st.session_state:
    st.session_state.history = []


def create_database():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE sales (
            sale_date TEXT,
            salesperson TEXT,
            region TEXT,
            product TEXT,
            quantity INTEGER,
            unit_price REAL
        )
        """
    )

    connection.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)",
        SALES,
    )

    # SQLite will reject database changes after this is enabled.
    connection.execute("PRAGMA query_only = ON")
    return connection


def make_sql(question):
    prompt = f"""
Create one SQLite SELECT query for this question:
{question}

Use only the table sales, with these columns:
sale_date, salesperson, region, product, quantity, unit_price

For total revenue, calculate SUM(quantity * unit_price).
Return only the SQL query, with no Markdown or explanation.
Keep results to at most 50 rows.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )

    sql = (response.message.content or "").strip()

    if sql.startswith("```"):
        sql = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", sql, flags=re.DOTALL)
        sql = sql.strip()

    sql = sql.rstrip(";").strip()

    if not re.match(r"(?i)^SELECT\b", sql):
        raise ValueError("The model did not return a SELECT query.")

    if any(marker in sql for marker in (";", "--", "/*", "*/")):
        raise ValueError("The query contains unsupported SQL syntax.")

    return sql


def ask_sales_data(question):
    sql = make_sql(question)
    connection = create_database()

    try:
        cursor = connection.execute(sql)
        rows = [dict(row) for row in cursor.fetchmany(50)]
    finally:
        connection.close()

    if not rows:
        answer = "I couldn't find matching sales records."
    else:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Explain the SQL results clearly and briefly. "
                        "Use only the supplied results."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n"
                        f"Query results: {json.dumps(rows)}"
                    ),
                },
            ],
        )
        answer = response.message.content

    return sql, rows, answer


for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sql"):
            with st.expander("Show generated SQL"):
                st.code(message["sql"], language="sql")

        if message.get("rows"):
            st.dataframe(
                message["rows"],
                width="stretch",
                hide_index=True,
            )


question = st.chat_input("Ask about sales, products, or regions")

if question:
    st.session_state.history.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Querying the sample data..."):
            try:
                sql, rows, answer = ask_sales_data(question)
                st.markdown(answer)

                with st.expander("Show generated SQL"):
                    st.code(sql, language="sql")

                if rows:
                    st.dataframe(
                        rows,
                        width="stretch",
                        hide_index=True,
                    )

                st.session_state.history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "rows": rows,
                    }
                )

            except Exception as error:
                error_message = f"Couldn't answer that question: {error}"
                st.error(error_message)
                st.session_state.history.append(
                    {"role": "assistant", "content": error_message}
                )