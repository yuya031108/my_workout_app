import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

def get_db_connection():
    return sqlite3.connect('workout.db', check_same_thread=False)

st.set_page_config(page_title="部位フィルター付き筋トレログ", layout="centered")

# --- 1. セッション状態の初期化 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 2. ログイン画面 ---
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
                st.success("作成完了。ログインしてください。")
            except sqlite3.IntegrityError:
                st.error("既に使用されています。")
        else:
            user = conn.execute('SELECT id, password FROM users WHERE username = ?', (user_input,)).fetchone()
            if user and user[1] == pass_input:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが違います。")
        conn.close()
    st.stop() 

# --- 3. ログイン後のメイン画面 ---
uid = st.session_state['user_id']
st.title(f"🏋️ {st.session_state['username']} の筋トレ記録")

# --- サイドバー：種目管理 ---
with st.sidebar:
    st.write(f"ログイン中: {st.session_state['username']} さん")
    if st.button("ログアウト"):
        st.session_state['logged_in'] = False
        st.rerun()
    st.divider()
    st.header("🛠 種目の管理")
    new_name = st.text_input("新しい種目名")
    new_cat = st.selectbox("部位を選択", ["胸", "背中", "脚", "その他"], key="add_cat")
    if st.button("種目を追加"):
        if new_name:
            conn = get_db_connection()
            conn.execute('INSERT INTO exercises (name, category) VALUES (?, ?)', (new_name, new_cat))
            conn.commit()
            conn.close()
            st.rerun()
    
    st.divider()
    conn = get_db_connection()
    all_ex_df = pd.read_sql_query('SELECT id, name FROM exercises', conn)
    conn.close()
    if not all_ex_df.empty:
        target_ex = st.selectbox("削除する種目を選択", all_ex_df['name'], key="del_ex_select")
        if st.button("種目を完全に消す"):
            conn = get_db_connection()
            conn.execute('DELETE FROM exercises WHERE name = ?', (target_ex,))
            conn.commit()
            conn.close()
            st.rerun()

# --- 記録入力エリア ---
st.subheader("💪 今日の記録を入力")
conn = get_db_connection()
filter_cat = st.radio("部位フィルター", ["すべて", "胸", "背中", "脚", "その他"], horizontal=True)
if filter_cat == "すべて":
    ex_list = pd.read_sql_query('SELECT id, name FROM exercises', conn)
else:
    ex_list = pd.read_sql_query('SELECT id, name FROM exercises WHERE category = ?', conn, params=(filter_cat,))

if not ex_list.empty:
    with st.form("input_form"):
        sel_name = st.selectbox("種目", ex_list['name'])
        sel_id = int(ex_list[ex_list['name'] == sel_name]['id'].values[0])
        col1, col2, col3 = st.columns(3)
        w = col1.number_input("重量(kg)", min_value=0.0, step=0.5)
        r = col2.number_input("回数", min_value=1, step=1)
        s = col3.number_input("セット数", min_value=1, step=1)
        if st.form_submit_button("保存"):
            conn.execute('INSERT INTO sets (user_id, date, exercise_id, weight, reps, set_count) VALUES (?, ?, ?, ?, ?, ?)',
                         (uid, date.today().strftime("%Y-%m-%d"), sel_id, w, r, s))
            conn.commit()
            st.success("保存しました")
            st.rerun()
conn.close()

# --- データ取得 ---
conn = get_db_connection()
all_data_df = pd.read_sql_query('''
    SELECT sets.id, sets.date, exercises.category, exercises.name, sets.weight, sets.reps, sets.set_count 
    FROM sets JOIN exercises ON sets.exercise_id = exercises.id
    WHERE sets.user_id = ? ORDER BY sets.date DESC, sets.id DESC
''', conn, params=(uid,))
conn.close()

# --- タブ表示 ---
tab1, tab2, tab3 = st.tabs(["📋 履歴", "🏆 自己ベスト", "🗓️ 活動ログ"])

with tab1:
    st.subheader("履歴の管理")
    if not all_data_df.empty:
        for index, row in all_data_df.iterrows():
            c = st.columns([2, 2, 4, 1])
            c[0].write(row['date'])
            c[1].write(row['category'])
            c[2].write(f"{row['name']} {row['weight']}kg")
            if c[3].button("🗑️", key=f"rec_{row['id']}"):
                conn = get_db_connection()
                conn.execute('DELETE FROM sets WHERE id = ?', (int(row['id']),))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.info("記録がありません")

with tab2:
    st.subheader("種目別自己ベスト")
    if not all_data_df.empty:
        best_df = all_data_df.groupby(["category", "name"])["weight"].max().reset_index()
        best_df.columns = ["部位", "種目名", "最高重量(kg)"]
        st.table(best_df.sort_values("最高重量(kg)", ascending=False))

with tab3:
    st.subheader("日別活動ログ")
    if not all_data_df.empty:
        sel_date = st.date_input("日付選択", value=date.today())
        target = sel_date.strftime("%Y-%m-%d")
        day_data = all_data_df[all_data_df['date'] == target]
        if not day_data.empty:
            for cat in ["胸", "背中", "脚", "その他"]:
                cat_d = day_data[day_data['category'] == cat]
                if not cat_d.empty:
                    st.info(f"**【{cat}】**")
                    for _, r in cat_d.iterrows():
                        st.write(f"・{r['name']}: {r['weight']}kg x {r['reps']} ({r['set_count']}set)")
        else:
            st.warning("記録なし")