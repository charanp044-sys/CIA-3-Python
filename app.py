
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Campus Library Management",
    layout="wide"
)

st.title("Campus Library Management Dashboard")
st.write("Manage and explore campus library records.")

# Load CSV dataset
@st.cache_data
def load_data():
    df = pd.read_csv("library_data.csv.csv")
    df["Issue_Date"] = pd.to_datetime(df["Issue_Date"], errors="coerce")
    df["Return_Date"] = pd.to_datetime(df["Return_Date"], errors="coerce")
    return df

df = load_data()

# Sidebar navigation
st.sidebar.header("Navigation")

menu = st.sidebar.radio(
    "Select Operation",
    [
        "Home",
        "Book Details",
        "Search Books",
        "Issue Books",
        "Return Books"
    ]
)

# Sidebar filters
st.sidebar.header("Filter Options")

category_options = ["All"] + sorted(
    df["Category"].dropna().unique().tolist()
)

category = st.sidebar.selectbox(
    "Select Book Category",
    category_options
)

status_options = ["All"] + sorted(
    df["Status"].dropna().unique().tolist()
)

status = st.sidebar.selectbox(
    "Select Book Status",
    status_options
)

# Apply filters
filtered_df = df.copy()

if category != "All":
    filtered_df = filtered_df[
        filtered_df["Category"] == category
    ]

if status != "All":
    filtered_df = filtered_df[
        filtered_df["Status"] == status
    ]

# HOME PAGE
if menu == "Home":

    st.header("Library Overview")

    # KPI Metrics
    total_books = df.drop_duplicates("Book_ID")["Total_Copies"].sum()

    available_books = df.drop_duplicates(
        "Book_ID"
    )["Available_Copies"].sum()

    issued_books = total_books - available_books

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Books", int(total_books))
    col2.metric("Available Books", int(available_books))
    col3.metric("Issued Books", int(issued_books))
    col4.metric("Total Records", len(df))

    st.divider()

    st.subheader("Library Information")

    st.write("""
    Welcome to the Campus Library Management System.

    This application helps manage:
    - Library book details
    - Book availability
    - Student borrowing records
    - Book issuing and returning
    - Book category information
    """)

    st.subheader("Recent Library Records")

    st.dataframe(
        df.tail(10),
        use_container_width=True,
        hide_index=True
    )

# BOOK DETAILS
elif menu == "Book Details":

    st.header("Book Details")

    book_details = df.drop_duplicates(
        subset="Book_ID"
    )

    st.dataframe(
        book_details[
            [
                "Book_ID",
                "Book_Title",
                "Author",
                "Category",
                "Total_Copies",
                "Available_Copies"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Available Books")

    available = book_details[
        book_details["Available_Copies"] > 0
    ]

    st.dataframe(
        available[
            ["Book_ID", "Book_Title", "Author", "Available_Copies"]
        ],
        use_container_width=True,
        hide_index=True
    )

# SEARCH BOOKS
elif menu == "Search Books":

    st.header("Search Library Books")

    search = st.text_input(
        "Enter Book Title, Author or Book ID"
    )

    if search:

        result = df[
            df["Book_Title"].str.contains(
                search, case=False, na=False
            ) |
            df["Author"].str.contains(
                search, case=False, na=False
            ) |
            df["Book_ID"].str.contains(
                search, case=False, na=False
            )
        ]

        if result.empty:
            st.warning("No matching books found.")

        else:
            st.success("Books found!")

            st.dataframe(
                result[
                    [
                        "Book_ID",
                        "Book_Title",
                        "Author",
                        "Category",
                        "Available_Copies"
                    ]
                ].drop_duplicates("Book_ID"),
                use_container_width=True,
                hide_index=True
            )

# ISSUE BOOKS
elif menu == "Issue Books":

    st.header("Issue Books to Students")

    book_details = df.drop_duplicates("Book_ID")

    available = book_details[
        book_details["Available_Copies"] > 0
    ]

    if available.empty:
        st.warning("No books are currently available.")

    else:

        with st.form("issue_form"):

            student_id = st.text_input("Student ID")
            student_name = st.text_input("Student Name")

            department = st.selectbox(
                "Department",
                ["MCA", "BCA", "MBA", "BBA", "Other"]
            )

            selected_book = st.selectbox(
                "Select Book",
                available["Book_ID"].tolist(),
                format_func=lambda x:
                    available.loc[
                        available["Book_ID"] == x,
                        "Book_Title"
                    ].iloc[0]
            )

            submit = st.form_submit_button("Issue Book")

            if submit:

                if not student_id.strip() or not student_name.strip():
                    st.error("Please enter student details.")

                elif (
                    (df["Student_ID"].astype(str) == student_id)
                    & (df["Status"] == "Issued")
                ).any():
                    st.error("This student ID already has an issued book record. Return it before issuing another.")

                else:

                    book_title = available.loc[
                        available["Book_ID"] == selected_book,
                        "Book_Title"
                    ].iloc[0]

                    new_record = pd.DataFrame([{
                        "Book_ID": selected_book,
                        "Book_Title": book_title,
                        "Author": available.loc[
                            available["Book_ID"] == selected_book,
                            "Author"
                        ].iloc[0],
                        "Category": available.loc[
                            available["Book_ID"] == selected_book,
                            "Category"
                        ].iloc[0],
                        "Total_Copies": available.loc[
                            available["Book_ID"] == selected_book,
                            "Total_Copies"
                        ].iloc[0],
                        "Available_Copies": available.loc[
                            available["Book_ID"] == selected_book,
                            "Available_Copies"
                        ].iloc[0] - 1,
                        "Student_ID": student_id,
                        "Student_Name": student_name,
                        "Department": department,
                        "Issue_Date": pd.Timestamp.today(),
                        "Return_Date": pd.NaT,
                        "Status": "Issued"
                    }])

                    df = pd.concat(
                        [df, new_record],
                        ignore_index=True
                    )

                    # Update availability in all rows for this book
                    df.loc[
                        df["Book_ID"] == selected_book,
                        "Available_Copies"
                    ] = new_record["Available_Copies"].iloc[0]

                    df.to_csv(
                        "library_data_extended.csv",
                        index=False
                    )

                    st.cache_data.clear()

                    st.success("Book issued successfully!")
                    st.rerun()

# RETURN BOOKS
elif menu == "Return Books":

    st.header("Return Library Books")

    issued = df[df["Status"] == "Issued"]

    if issued.empty:

        st.info("No books are currently issued.")

    else:

        issued = issued.reset_index()

        selected = st.selectbox(
            "Select Student and Book",
            issued.index.tolist(),
            format_func=lambda x:
                issued.loc[x, "Student_Name"]
                + " - "
                + issued.loc[x, "Book_Title"]
        )

        if st.button("Return Book"):

            original_index = df[
                (df["Student_ID"] == issued.loc[selected, "Student_ID"])
                & (df["Book_ID"] == issued.loc[selected, "Book_ID"])
                & (df["Status"] == "Issued")
            ].index[0]

            selected_book = df.loc[
                original_index, "Book_ID"
            ]

            df.loc[
                original_index, "Status"
            ] = "Returned"

            df.loc[
                original_index, "Return_Date"
            ] = pd.Timestamp.today()

            df.loc[
                df["Book_ID"] == selected_book,
                "Available_Copies"
            ] += 1

            df.to_csv(
                "library_data_extended.csv",
                index=False
            )

            st.cache_data.clear()

            st.success("Book returned successfully!")
            st.rerun()

# VISUALIZATIONS
if menu == "Home" and not filtered_df.empty:

    st.divider()
    st.header("Library Visualizations")

    tab1, tab2, tab3 = st.tabs([
        "Book Categories",
        "Book Availability",
        "Issue Records"
    ])

    with tab1:

        category_count = df.drop_duplicates(
            "Book_ID"
        ).groupby(
            "Category"
        ).size().reset_index(name="Total Books")

        fig1 = px.bar(
            category_count,
            x="Category",
            y="Total Books",
            color="Category",
            title="Books by Category"
        )

        st.plotly_chart(fig1, use_container_width=True)

    with tab2:

        availability = df.drop_duplicates(
            "Book_ID"
        )

        fig2 = px.pie(
            availability,
            names="Category",
            values="Total_Copies",
            title="Book Distribution by Category"
        )

        st.plotly_chart(fig2, use_container_width=True)

    with tab3:

        issue_data = df.dropna(
            subset=["Issue_Date"]
        ).copy()

        issue_data["Month"] = (
            issue_data["Issue_Date"].dt.strftime("%Y-%m")
        )

        monthly_issues = issue_data.groupby(
            "Month"
        ).size().reset_index(name="Total Issues")

        fig3 = px.line(
            monthly_issues,
            x="Month",
            y="Total Issues",
            markers=True,
            title="Monthly Book Issue Records"
        )

        st.plotly_chart(fig3, use_container_width=True)
