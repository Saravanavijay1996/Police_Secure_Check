import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# ----------------------- DATABASE CONNECTION -----------------------
def create_connection():
    """Create connection to MySQL database"""
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Balanandy@22',
            database='securecheck',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None


# ----------------------- FETCH DATA FUNCTION -----------------------
def fetch_data(query):
    """Fetch data from MySQL and return as DataFrame"""
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()
        finally:
            connection.close()
    else:
        return pd.DataFrame()


# ----------------------- STREAMLIT DASHBOARD -----------------------
st.set_page_config(page_title="Securecheck Police Dashboard", layout="wide")

st.title("🛡️ SecureCheck: Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insights for law enforcement 🚔")

# ----------------------- SHOW POLICE LOG TABLE -----------------------
st.header("📋 Police Logs Overview")
query = "SELECT * FROM police_logs"
data = fetch_data(query)

if not data.empty:
    st.dataframe(data, use_container_width=True)
else:
    st.warning("No data found in police_logs table.")


# ----------------------- METRICS SECTION -----------------------
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_stops = data.shape[0]
    st.metric("Total Police Stops", total_stops)

with col2:
    arrests = data[data['stop_outcome'].str.contains("arrest", case=False, na=False)].shape[0]
    st.metric("Total Arrests", arrests)

with col3:
    warnings = data[data['stop_outcome'].str.contains("warning", case=False, na=False)].shape[0]
    st.metric("Total Warnings", warnings)

with col4:
    drug_related = data[data['drugs_related_stop'] == 1].shape[0]
    st.metric("Drug Related Stops", drug_related)


# ----------------------- CHARTS SECTION -----------------------
st.header("📊 Visual Insights")
tab1, tab2 = st.tabs(["Stops by Violation", "Driver Gender Distribution"])

with tab1:
    if not data.empty and 'violation' in data.columns:
        violation_data = data['violation'].value_counts().reset_index()
        violation_data.columns = ['Violation', 'Count']
        fig = px.bar(
            violation_data,
            x='Violation',
            y='Count',
            title="Stops by Violation Type",
            color='Violation'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Violation chart.")

with tab2:
    if not data.empty and 'driver_gender' in data.columns:
        gender_data = data['driver_gender'].value_counts().reset_index()
        gender_data.columns = ['Gender', 'Count']
        fig = px.pie(
            gender_data,
            names='Gender',
            values='Count',
            title="Driver Gender Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Driver Gender chart.")


# Advanced Queries
st.header("⚙️ Advanced Insights")

query_map = {
    "top 10 vehicle_Number involved in drug-related stops": "SELECT vehicle_number, COUNT(*) AS drug_stop_count FROM SECURECHECK.police_logs WHERE drugs_related_stop = TRUE GROUP BY vehicle_number ORDER BY drug_stop_count DESC LIMIT 10;",
    "most frequently searched": "SELECT vehicle_number, COUNT(*) AS search_count FROM SECURECHECK.police_logs WHERE search_conducted = TRUE GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10;",
    "driver age group had the highest arrest rate": "SELECT CASE WHEN driver_age BETWEEN 16 AND 25 THEN '16-25' WHEN driver_age BETWEEN 26 AND 35 THEN '26-35' WHEN driver_age BETWEEN 36 AND 45 THEN '36-45' WHEN driver_age BETWEEN 46 AND 55 THEN '46-55' WHEN driver_age BETWEEN 56 AND 65 THEN '56-65' ELSE '66+'  END AS age_group, COUNT(*) AS total_stops, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percentage FROM SECURECHECK.police_logs WHERE driver_age IS NOT NULL GROUP BY age_group ORDER BY arrest_rate_percentage DESC;",
    "gender distribution of drivers stopped in each country": "SELECT country_name, driver_gender, COUNT(*) AS total_stops, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY country_name), 2) AS percentage FROM SECURECHECK.police_logs WHERE driver_gender IS NOT NULL GROUP BY country_name, driver_gender ORDER BY country_name, total_stops DESC;",
    "race and gender combination has the highest search rate": "SELECT driver_race, driver_gender, COUNT(*) AS total_stops, SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches, ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_rate_percentage FROM SECURECHECK.police_logs WHERE driver_race IS NOT NULL AND driver_gender IS NOT NULL GROUP BY driver_race, driver_gender ORDER BY search_rate_percentage DESC LIMIT 1;",
    "time of day sees the most traffic stops": "SELECT CASE WHEN HOUR(stop_time) BETWEEN 5 AND 11 THEN 'Morning (05:00-11:59)' WHEN HOUR(stop_time) BETWEEN 12 AND 16 THEN 'Afternoon (12:00-16:59)' WHEN HOUR(stop_time) BETWEEN 17 AND 20 THEN 'Evening (17:00-20:59)' ELSE 'Night (21:00-04:59)' END AS time_of_day, COUNT(*) AS total_stops FROM SECURECHECK.police_logs WHERE stop_time IS NOT NULL GROUP BY time_of_day ORDER BY total_stops DESC;",
    "average stop duration for different violations": "SELECT violation, ROUND(AVG(CAST(stop_duration AS UNSIGNED)), 2) AS avg_stop_duration_minutes FROM securecheck.police_logs WHERE stop_duration IS NOT NULL GROUP BY violation ORDER BY avg_stop_duration_minutes DESC;",
    "stops during the night more likely to lead to arrests": "SELECT CASE WHEN HOUR(stop_time) BETWEEN 21 AND 23 OR HOUR(stop_time) BETWEEN 0 AND 4 THEN 'Night (21:00-04:59)' ELSE 'Day (05:00-20:59)' END AS time_period, COUNT(*) AS total_stops, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage FROM securecheck.police_logs WHERE stop_time IS NOT NULL GROUP BY time_period ORDER BY arrest_rate_percentage DESC;",
    "most associated with searches or arrests": "SELECT violation, COUNT(*) AS total_stops, SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches, ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_rate_percentage, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage FROM securecheck.police_logs WHERE violation IS NOT NULL GROUP BY violation ORDER BY search_rate_percentage DESC, arrest_rate_percentage DESC;",
    "most common among younger drivers (<25)": "SELECT violation, COUNT(*) AS total_stops, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_of_young_driver_stops FROM securecheck.police_logs WHERE driver_age < 25 AND violation IS NOT NULL GROUP BY violation ORDER BY total_stops DESC LIMIT 10;",
    "violation that rarely results in search or arrest": "SELECT violation, COUNT(*) AS total_stops, SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches, ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_rate_percentage, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage FROM securecheck.police_logs WHERE violation IS NOT NULL GROUP BY violation HAVING search_rate_percentage < 5 AND arrest_rate_percentage < 5 ORDER BY total_stops DESC;",
    "countries that report the highest rate of drug-related stops": "SELECT country_name, COUNT(*) AS total_stops, SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_stops, ROUND(SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS drug_stop_rate_percentage FROM securecheck.police_logs WHERE country_name IS NOT NULL GROUP BY country_name ORDER BY drug_stop_rate_percentage DESC LIMIT 10;",
    "arrest rate by country and violation": "SELECT country_name, violation, COUNT(*) AS total_stops, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage FROM securecheck.police_logs WHERE country_name IS NOT NULL AND violation IS NOT NULL GROUP BY country_name, violation ORDER BY arrest_rate_percentage DESC, total_stops DESC;",
    "country that has the most stops with search conducted": "SELECT country_name, COUNT(*) AS total_searches FROM securecheck.police_logs WHERE search_conducted = TRUE GROUP BY country_name ORDER BY total_searches DESC LIMIT 1;",
    "Yearly Breakdown of Stops and Arrests by Country": "SELECT country_name, YEAR(stop_date) AS stop_year, COUNT(*) AS total_stops, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage, SUM(COUNT(*)) OVER (PARTITION BY country_name ORDER BY YEAR(stop_date)) AS cumulative_stops, SUM(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)) OVER (PARTITION BY country_name ORDER BY YEAR(stop_date)) AS cumulative_arrests FROM securecheck.police_logs WHERE country_name IS NOT NULL AND stop_date IS NOT NULL GROUP BY country_name, YEAR(stop_date) ORDER BY country_name, stop_year;",
    "Driver Violation Trends Based on Age and Race": "WITH age_race_violation AS (SELECT CASE WHEN driver_age BETWEEN 16 AND 25 THEN '16-25' WHEN driver_age BETWEEN 26 AND 35 THEN '26-35' WHEN driver_age BETWEEN 36 AND 45 THEN '36-45' WHEN driver_age BETWEEN 46 AND 55 THEN '46-55' WHEN driver_age BETWEEN 56 AND 65 THEN '56-65' ELSE '66+' END AS age_group, driver_race, violation, COUNT(*) AS total_stops FROM securecheck.police_logs WHERE driver_age IS NOT NULL AND driver_race IS NOT NULL AND violation IS NOT NULL GROUP BY age_group, driver_race, violation) SELECT  age_group, driver_race, violation, total_stops, ROUND(total_stops * 100.0 / SUM(total_stops) OVER (PARTITION BY age_group, driver_race), 2) AS percentage_within_group FROM age_race_violation ORDER BY age_group, driver_race, total_stops DESC;",
    "Time Period Analysis of Stops, Number of Stops by Year,Month, Hour of the Day": "SELECT YEAR(stop_date) AS stop_year, MONTH(stop_date) AS stop_month, HOUR(stop_time) AS stop_hour, COUNT(*) AS total_stops FROM securecheck.police_logs WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL GROUP BY YEAR(stop_date), MONTH(stop_date), HOUR(stop_time) ORDER BY stop_year, stop_month, stop_hour;",
    "Violations with High Search and Arrest Rates": "WITH violation_stats AS (SELECT violation, COUNT(*) AS total_stops, SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests FROM securecheck.police_logs WHERE violation IS NOT NULL GROUP BY violation) SELECT violation, total_stops, total_searches, ROUND(total_searches * 100.0 / total_stops, 2) AS search_rate_percentage, total_arrests, ROUND(total_arrests * 100.0 / total_stops, 2) AS arrest_rate_percentage, RANK() OVER (ORDER BY (total_searches * 1.0 / total_stops) DESC) AS search_rate_rank, RANK() OVER (ORDER BY (total_arrests * 1.0 / total_stops) DESC) AS arrest_rate_rank FROM violation_stats ORDER BY search_rate_percentage DESC, arrest_rate_percentage DESC;",
    "Driver Demographics by Country": "WITH age_grouped AS (SELECT country_name, CASE WHEN driver_age BETWEEN 16 AND 25 THEN '16-25' WHEN driver_age BETWEEN 26 AND 35 THEN '26-35' WHEN driver_age BETWEEN 36 AND 45 THEN '36-45' WHEN driver_age BETWEEN 46 AND 55 THEN '46-55' WHEN driver_age BETWEEN 56 AND 65 THEN '56-65' ELSE '66+' END AS age_group, driver_gender, driver_race, COUNT(*) AS total_stops FROM securecheck.police_logs WHERE country_name IS NOT NULL AND driver_age IS NOT NULL AND driver_gender IS NOT NULL AND driver_race IS NOT NULL GROUP BY country_name, age_group, driver_gender, driver_race) SELECT country_name, age_group, driver_gender, driver_race, total_stops, ROUND(total_stops * 100.0 / SUM(total_stops) OVER (PARTITION BY country_name), 2) AS percentage_of_country FROM age_grouped ORDER BY country_name, age_group, total_stops DESC;",
    "Top 5 Violations with Highest Arrest Rates": "SELECT violation, COUNT(*) AS total_stops, SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests, ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percentage FROM securecheck.police_logs WHERE violation IS NOT NULL GROUP BY violation HAVING COUNT(*) > 10   -- optional: filter out rare violations ORDER BY arrest_rate_percentage DESC LIMIT 5;"
}

selected_query = st.selectbox(
    "Select a Query to Run",
    list(query_map.keys()),
    key="advanced_query_select"
)

if st.button("Run Query", key="run_query_btn"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("No result found for the selected query.")


# ----------------------- PREDICTION FORM -----------------------
st.markdown("---")
st.header("🧠 Predict Stop Outcome & Violation")

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date", key="stop_date")
    stop_time = st.time_input("Stop Time", key="stop_time")
    county_name = st.text_input("County Name", key="county_name")
    driver_gender = st.selectbox("Driver Gender", ["male", "female"], key="driver_gender")
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27, key="driver_age")
    driver_race = st.text_input("Driver Race", key="driver_race")
    search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"], key="search_conducted")
    drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"], key="drug_related")

    stop_duration_options = data['stop_duration'].dropna().unique() if not data.empty else ["0-15 min", "16-30 min"]
    stop_duration = st.selectbox("Stop Duration", stop_duration_options, key="stop_duration")

    vehicle_number = st.text_input("Vehicle Number", key="vehicle_number")
    submitted = st.form_submit_button("Predict Stop Outcome & Violation", key="predict_btn")

if submitted:
    filtered_data = data[
        (data['driver_gender'] == driver_gender) &
        (data['driver_age'] == driver_age) &
        (data['search_conducted'] == int(search_conducted)) &
        (data['stop_duration'] == stop_duration) &
        (data['drugs_related_stop'] == int(drugs_related_stop))
    ]

    if not filtered_data.empty:
        predicted_outcome = filtered_data['stop_outcome'].mode()[0]
        predicted_violation = filtered_data['violation'].mode()[0]
    else:
        predicted_outcome = "warning"
        predicted_violation = "speeding"

    search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
    drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"

    st.markdown(f"""
    🚓 **Prediction Summary**

    - **Predicted Violation:** {predicted_violation}
    - **Predicted Stop Outcome:** {predicted_outcome}

    📝 A {driver_age}-year-old {driver_gender} driver in **{county_name}** was stopped at **{stop_time.strftime('%I:%M %p')}** on **{stop_date.strftime('%B %d, %Y')}**.  
    {search_text}, and the stop {drug_text}.
    """)

st.markdown("---")
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")
