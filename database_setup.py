import sqlite3

def init_db():
    conn = sqlite3.connect('workout.db')
    cursor = conn.cursor()
    
    # ユーザーテーブル
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
    
    # 種目テーブル（categoryを追加）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL,
        category TEXT NOT NULL
    )''')
    
    # セット記録テーブル
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT NOT NULL,
        exercise_id INTEGER, weight REAL, reps INTEGER, set_count INTEGER, 
        FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    )''')
    
    # 初期データ（部位付き）
    initial_exercises = [
        ('ベンチプレス', '胸'),
        ('スクワット', '脚'),
        ('デッドリフト', '背中'),
        ('ショルダープレス', 'その他')
    ]
    cursor.executemany('INSERT INTO exercises (name, category) VALUES (?, ?)', initial_exercises)
    
    conn.commit()
    conn.close()
    print("部位カテゴリ対応版データベースを作成しました！")

if __name__ == "__main__":
    init_db()