import sqlite3
from pathlib import Path
from contextlib import closing
import pandas as pd
import streamlit as st

st.set_page_config(page_title='College NIL Business Directory', page_icon='🏅', layout='wide')
DB = Path(__file__).with_name('nil_demo.db')

def connect():
    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# Labs 1 and 2: relational database and fictional sample records.
def initialize():
    with closing(connect()) as conn, conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS BUSINESS (
            Business_ID TEXT PRIMARY KEY, Business_Name TEXT NOT NULL,
            Industry TEXT NOT NULL, City TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS NIL_AGREEMENT (
            Agreement_ID TEXT PRIMARY KEY, Business_ID TEXT NOT NULL,
            Athlete_Name TEXT NOT NULL, Compensation_Amount REAL NOT NULL,
            FOREIGN KEY (Business_ID) REFERENCES BUSINESS(Business_ID))''')
        # Seed once, not on every rerun, so deleted records stay deleted.
        conn.execute('CREATE TABLE IF NOT EXISTS DEMO_SETUP (Version INTEGER PRIMARY KEY)')
        if not conn.execute('SELECT 1 FROM DEMO_SETUP WHERE Version=1').fetchone():
            if not conn.execute('SELECT 1 FROM BUSINESS LIMIT 1').fetchone():
                conn.executemany('INSERT INTO BUSINESS VALUES (?, ?, ?, ?)', [
                    ('B01','Peachtree Sportswear','Apparel','Atlanta'),
                    ('B02','Metro Fitness','Fitness','Decatur'),
                    ('B03','Southern Tech Solutions','Technology','Atlanta'),
                    ('B04','Campus Café','Food & Beverage','Atlanta'),
                    ('B05','Victory Media','Media','Marietta')])
            if not conn.execute('SELECT 1 FROM NIL_AGREEMENT LIMIT 1').fetchone():
                for row in [('A01','B01','Jordan Lee',1200.00),
                            ('A02','B02','Taylor Green',850.00),
                            ('A03','B01','Morgan Hill',500.00)]:
                    if conn.execute('SELECT 1 FROM BUSINESS WHERE Business_ID=?',(row[1],)).fetchone():
                        conn.execute('INSERT INTO NIL_AGREEMENT VALUES (?, ?, ?, ?)',row)
            conn.execute('INSERT INTO DEMO_SETUP VALUES (1)')

def read(query, params=()):
    with closing(connect()) as conn:
        return pd.read_sql_query(query, conn, params=params)

def write(query, params):
    with closing(connect()) as conn, conn:
        conn.execute(query, params)

def load_data():
    return read('SELECT * FROM BUSINESS ORDER BY City, Business_Name')

initialize()
st.title('🏅 College NIL Business Directory')
st.caption('NIL Sponsor Manager • Completed Streamlit labs • Fictional data')
if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))

# Lab 3: sidebar navigation.
st.sidebar.title('Navigation')
menu = st.sidebar.radio('Select an option', ['Home','Business Directory','NIL Agreements','Reports'])
data = load_data()

if menu == 'Home':
    st.header('Welcome')
    st.write('Manage sponsoring businesses, view NIL agreements, and explore reports using Python and SQLite.')
    totals = read('SELECT COUNT(*) AS n, COALESCE(SUM(Compensation_Amount),0) AS total FROM NIL_AGREEMENT').iloc[0]
    a,b,c = st.columns(3)
    a.metric('Businesses',len(data))
    b.metric('Agreements',int(totals.n))
    c.metric('Total Compensation',f'${totals.total:,.2f}')
    st.info('Select an option in the sidebar to explore the application.')

elif menu == 'Business Directory':
    st.header('Business Directory')
    tab1,tab2,tab3 = st.tabs(['📋 Directory','➕ Add Business','✏️ Edit / Delete'])
    with tab1:
        # Lab 3: SQL-driven filter; Lab 1: text search.
        industries = read('SELECT DISTINCT Industry FROM BUSINESS ORDER BY Industry')
        choice = st.selectbox('Select an industry',['All Industries']+industries['Industry'].tolist())
        query = 'SELECT Business_Name, Industry, City FROM BUSINESS'
        if choice == 'All Industries':
            df = read(query+' ORDER BY City, Business_Name')
        else:
            df = read(query+' WHERE Industry = ? ORDER BY City, Business_Name',(choice,))
        search = st.text_input('Search by name, industry, or city')
        if search:
            df = df[df.astype(str).apply(lambda s:s.str.contains(search,case=False,regex=False)).any(axis=1)]
        st.dataframe(df,hide_index=True)
        st.write('Number of businesses:',len(df))
        st.subheader('Businesses by industry')
        st.bar_chart(data['Industry'].value_counts())
    with tab2:
        with st.form('add_business',clear_on_submit=True):
            business_id = st.text_input('Business ID (e.g., B06)')
            name = st.text_input('Business name')
            industry = st.text_input('Industry')
            city = st.text_input('City')
            submitted = st.form_submit_button('Add business')
        if submitted:
            vals = tuple(v.strip() for v in (business_id,name,industry,city))
            if not all(vals):
                st.error('All four fields are required.')
            else:
                try:
                    write('INSERT INTO BUSINESS VALUES (?, ?, ?, ?)',vals)
                    st.session_state.notice = 'Business added.'
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error('That Business ID already exists. Choose another.')
    with tab3:
        if data.empty:
            st.info('No businesses to edit or delete.')
        else:
            selected = st.selectbox('Choose a business',data.Business_ID.tolist(),format_func=lambda x:f"{x} — {data.loc[data.Business_ID==x,'Business_Name'].iloc[0]}")
            current = data[data.Business_ID==selected].iloc[0]
            with st.form('edit_'+selected):
                name = st.text_input('Business name',value=current.Business_Name)
                industry = st.text_input('Industry',value=current.Industry)
                city = st.text_input('City',value=current.City)
                update = st.form_submit_button('Save changes')
            if update:
                vals = tuple(v.strip() for v in (name,industry,city))
                if not all(vals):
                    st.error('Fields cannot be blank.')
                else:
                    write('UPDATE BUSINESS SET Business_Name=?, Industry=?, City=? WHERE Business_ID=?',(*vals,selected))
                    st.session_state.notice = 'Updated successfully.'
                    st.rerun()
            st.warning('Deleting a business is permanent. Businesses with agreements cannot be deleted.')
            confirm = st.checkbox('I understand and want to delete the selected business',key='confirm_'+selected)
            if st.button('Delete selected business',disabled=not confirm):
                try:
                    write('DELETE FROM BUSINESS WHERE Business_ID=?',(selected,))
                    st.session_state.notice = 'Business deleted.'
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error('Cannot delete this business because NIL agreements reference it.')

elif menu == 'NIL Agreements':
    st.header('NIL Agreements')
    df = read('''SELECT B.Business_Name, N.Athlete_Name, N.Compensation_Amount
        FROM BUSINESS AS B INNER JOIN NIL_AGREEMENT AS N
        ON B.Business_ID = N.Business_ID
        ORDER BY N.Compensation_Amount DESC''')
    st.dataframe(df,hide_index=True)
    st.write('Number of agreements:',len(df))
    st.metric('Total Compensation',f"${df['Compensation_Amount'].sum():,.2f}")

elif menu == 'Reports':
    st.header('Business Summary Report')
    df = read('''SELECT B.Business_Name, COUNT(N.Agreement_ID) AS Agreement_Count,
        COALESCE(SUM(N.Compensation_Amount),0) AS Total_Compensation
        FROM BUSINESS AS B LEFT JOIN NIL_AGREEMENT AS N
        ON B.Business_ID = N.Business_ID
        GROUP BY B.Business_ID, B.Business_Name
        ORDER BY Total_Compensation DESC''')
    st.dataframe(df,hide_index=True)
    st.subheader('Total Compensation by Business')
    st.bar_chart(df.set_index('Business_Name')['Total_Compensation'])
    st.subheader('Number of Agreements by Business')
    st.bar_chart(df.set_index('Business_Name')['Agreement_Count'])

st.divider()
st.caption('Teaching demo: SQLite data is stored in nil_demo.db in this Codespace. Public cloud deployment may not preserve local data.')
