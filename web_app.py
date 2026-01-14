import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

def get_db_connection():
    return sqlite3.connect('workout.db', check_same_thread=False)

st.set_page_config(page_title="認証付き筋トレログ", layout="centered")

# --- 認証機能 (ログイン・新規登録) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 ログイン / 新規登録")
    
    auth_mode = st.radio("モード選択", ["ログイン", "新規登録"])
    user_input = st.text_input("ユーザー名")
    pass_input = st.text_input("パスワード", type="password")
    
    if st.button("実行"):
        conn = get_db_connection()
        if auth_mode == "新規登録":
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user_input, pass_input))
                conn.commit()
                st.success("アカウントを作成しました！ログインしてください。")
            except sqlite3.IntegrityError:
                st.error("そのユーザー名は既に使用されています。")
        
        else: # ログインモード
            user = conn.execute('SELECT id, password FROM users WHERE username = ?', (user_input,)).fetchone()
            if user and user[1] == pass_input:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが違います。")
        conn.close()
    st.stop() # ログイン前はここで止める

# --- ログアウトボタン ---
with st.sidebar:
    st.write(f"ログイン中: {st.session_state['username']} さん")
    if st.button("ログアウト"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- メインコンテンツ (ここからはログイン後のみ表示される) ---
st.title(f"🏋️ {st.session_state['username']} の筋トレ記録")

# 種目の追加機能（サイドバー）
with st.sidebar:
    st.divider()
    new_ex = st.text_input("種目を追加")
    if st.button("追加"):
        if new_ex:
            conn = get_db_connection()
            conn.execute('INSERT INTO exercises (name) VALUES (?)', (new_ex,))
            conn.commit()
            conn.close()
            st.rerun()

# 記録入力
conn = get_db_connection()
exercises_df = pd.read_sql_query('SELECT id, name FROM exercises', conn)
if not exercises_df.empty:
    with st.form("record_form"):
        selected_ex_name = st.selectbox("種目", exercises_df['name'])
        ex_id = exercises_df[exercises_df['name'] == selected_ex_name]['id'].values[0]
        c1, c2, c3 = st.columns(3)
        weight = c1.number_input("重量(kg)", min_value=0.0)
        reps = c2.number_input("回数", min_value=1)
        sets = c3.number_input("セット数", min_value=1)
        
        if st.form_submit_button("保存"):
            today = date.today().strftime("%Y-%m-%d")
            conn.execute('''
                INSERT INTO sets (user_id, date, exercise_id, weight, reps, set_count) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (st.session_state['user_id'], today, int(ex_id), weight, int(reps), int(sets)))
            conn.commit()
            st.success("保存完了！")
conn.close()

# タブ表示
tab1, tab2, tab3 = st.tabs(["📋 履歴", "🏆 自己ベスト", "📈 成長グラフ"])
uid = st.session_state['user_id']

with tab1:
    conn = get_db_connection()
    df = pd.read_sql_query('''
        SELECT date, name, weight, reps, set_count 
        FROM sets JOIN exercises ON sets.exercise_id = exercises.id
        WHERE user_id = ? ORDER BY date DESC
    ''', conn, params=(uid,))
    conn.close()
    st.dataframe(df, use_container_width=True)

with tab2:
    if not df.empty:
        best_df = df.groupby('name')['weight'].max().reset_index()
        st.table(best_df)

with tab3:
    if not df.empty:
        chart_data = df.pivot_table(index='date', columns='name', values='weight')
        st.line_chart(chart_data)