from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd, streamlit as st

# MongoDB connection details
client = MongoClient("mongodb://192.168.1.112:27017/")
db1 = client['Electrify_15min']
db2 = client['Electrify_15min']
db3 = client['Electrify_15min']

# Collections
collection1 = db1['store_data']
collection2 = db2['store_data']
collection3 = db3['store_data']


# Function to count status for each slot in a collection
def get_status_counts(collection):
    slots = [f'status_{hour:02d}-{minute:02d}' for hour in range(24) for minute in range(0, 60, 15)]
    status_counts = {slot: {"pending_count": 0, "done_count": 0, "not_found_count": 0} for slot in slots}

    for doc in collection.find():
        for slot in slots:
            if slot in doc:
                status = doc[slot]
                if status == "pending":
                    status_counts[slot]["pending_count"] += 1
                elif status == "done":
                    status_counts[slot]["done_count"] += 1
                elif status == "not_found":
                    status_counts[slot]["not_found_count"] += 1

    return status_counts


# Fetch status counts for each collection
status_counts_1 = get_status_counts(collection1)
status_counts_2 = get_status_counts(collection2)
status_counts_3 = get_status_counts(collection3)

# Prepare data for the DataFrame
data = []
for slot in status_counts_1.keys():
    row = {
        "slot": slot,
        "ChargePoint_pending_count": status_counts_1[slot]["pending_count"],
        "ChargePoint_done_count": status_counts_1[slot]["done_count"],
        "ChargePoint_not_found_count": status_counts_1[slot]["not_found_count"],
        "Evgo_pending_count": status_counts_2[slot]["pending_count"],
        "Evgo_done_count": status_counts_2[slot]["done_count"],
        "Evgo_not_found_count": status_counts_2[slot]["not_found_count"],
        "Electrify_America_pending_count": status_counts_3[slot]["pending_count"],
        "Electrify_America_done_count": status_counts_3[slot]["done_count"],
        "Electrify_America_not_found_count": status_counts_3[slot]["not_found_count"]
    }
    data.append(row)

# Convert to DataFrame
df = pd.DataFrame(data)


# Display the DataFrame as a table
# st.title("MongoDB Status Dashboard")
# st.dataframe(df)

# Function to check if a slot's pending count should be highlighted
def should_highlight_pending(slot):
    current_time = datetime.now().time()
    slot_time = datetime.strptime(slot, "status_%H-%M").time()
    slot_end = datetime.combine(datetime.today(), slot_time) + timedelta(minutes=15)
    time_diff = datetime.combine(datetime.today(), current_time) - slot_end

    # Check if the current time is between 0 to 5 minutes after the slot end
    return timedelta(minutes=0) <= time_diff <= timedelta(minutes=5)


# Function to generate HTML table with styling
def generate_html_table(df):
    html = "<table border='1' style='border-collapse: collapse;'>"

    # Create table headers with colspan
    html += """
    <thead>
        <tr>
            <th rowspan='2'>Slot</th>
            <th colspan='3'>ChargePoint</th>
            <th colspan='3'>Evgo</th>
            <th colspan='3'>Electrify_America</th>
        </tr>
        <tr>
            <th>pending_count</th>
            <th>done_count</th>
            <th>not_found_count</th>
            <th>pending_count</th>
            <th>done_count</th>
            <th>not_found_count</th>
            <th>pending_count</th>
            <th>done_count</th>
            <th>not_found_count</th>
        </tr>
    </thead>
    """

    # Create table rows
    html += "<tbody>"
    for index, row in df.iterrows():
        html += "<tr>"
        html += f"<td>{row['slot']}</td>"

        # Process each tablename's counts and add highlight if needed
        for tablename in ['ChargePoint', 'Evgo', 'Electrify_America']:
            for count_type in ['pending_count', 'done_count', 'not_found_count']:
                value = row[f'{tablename}_{count_type}']
                style = ""
                if count_type == 'pending_count' and value > 0 and should_highlight_pending(row['slot']):
                    style = "style='background-color: red;'"
                html += f"<td {style}>{value}</td>"

        html += "</tr>"

    html += "</tbody></table>"

    return html


# Generate the HTML table
html_table = generate_html_table(df)

# Display the HTML table in Streamlit
st.set_page_config(
    layout="wide",
)
st.title("EV Charger Utilization Data Dashboard")
st.markdown(html_table, unsafe_allow_html=True)