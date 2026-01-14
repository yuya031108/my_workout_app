import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date

def get_db_connection():
    return sqlite3.connect('workout.db')

class WorkoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("筋トレ記録アプリ")
        self.root.geometry("500x650") # 少し縦を長くしました

        # --- 入力エリア ---
        tk.Label(root, text="【 記録の追加 】", font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(root, text="種目を選択:").pack()
        self.exercise_combo = ttk.Combobox(root, state="readonly")
        self.exercise_combo.pack(pady=5)
        self.refresh_exercises()

        tk.Label(root, text="重量 (kg):").pack()
        self.weight_entry = tk.Entry(root)
        self.weight_entry.pack(pady=5)

        tk.Label(root, text="回数:").pack()
        self.reps_entry = tk.Entry(root)
        self.reps_entry.pack(pady=5)

        # 追加：セット数
        tk.Label(root, text="セット数:").pack()
        self.sets_entry = tk.Entry(root)
        self.sets_entry.pack(pady=5)

        tk.Button(root, text="記録を保存", command=self.add_record, bg="#e1e1e1").pack(pady=10)

        # --- 操作エリア ---
        tk.Frame(root, height=2, bd=1, relief="sunken").pack(fill="x", padx=5, pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="履歴を表示", command=self.show_history).pack(side="left", padx=5)
        tk.Button(btn_frame, text="自己ベスト", command=self.show_bests).pack(side="left", padx=5)
        tk.Button(btn_frame, text="種目追加", command=self.open_add_exercise_window).pack(side="left", padx=5)

        # --- 表示エリア ---
        self.display_area = tk.Text(root, height=15, width=60)
        self.display_area.pack(pady=10, padx=10)

    def refresh_exercises(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exercises')
        self.exercises = cursor.fetchall()
        conn.close()
        self.exercise_combo['values'] = [f"{ex[0]}: {ex[1]}" for ex in self.exercises]

    def add_record(self):
        try:
            ex_info = self.exercise_combo.get()
            if not ex_info:
                raise ValueError("種目を選んでください")
            
            ex_id = int(ex_info.split(":")[0])
            weight = float(self.weight_entry.get())
            reps = int(self.reps_entry.get())
            scount = int(self.sets_entry.get()) # セット数を取得
            
            conn = get_db_connection()
            cursor = conn.cursor()
            today = date.today().strftime("%Y-%m-%d")
            # set_countをINSERTに追加
            cursor.execute('''
                INSERT INTO sets (date, exercise_id, weight, reps, set_count) 
                VALUES (?, ?, ?, ?, ?)
            ''', (today, ex_id, weight, reps, scount))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "記録しました！")
            self.weight_entry.delete(0, tk.END)
            self.reps_entry.delete(0, tk.END)
            self.sets_entry.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("エラー", f"入力を確認してください: {e}")

    def show_history(self):
        self.display_area.delete("1.0", tk.END)
        conn = get_db_connection()
        cursor = conn.cursor()
        # SELECTにset_countを追加
        cursor.execute('''
            SELECT sets.date, exercises.name, sets.weight, sets.reps, sets.set_count 
            FROM sets JOIN exercises ON sets.exercise_id = exercises.id
            ORDER BY sets.date DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        self.display_area.insert(tk.END, "--- 履歴 ---\n")
        for r in rows:
            self.display_area.insert(tk.END, f"{r[0]} | {r[1]}: {r[2]}kg x {r[3]}回 ({r[4]}セット)\n")

    def show_bests(self):
        self.display_area.delete("1.0", tk.END)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT exercises.name, MAX(sets.weight) FROM sets
            JOIN exercises ON sets.exercise_id = exercises.id
            GROUP BY exercises.name ORDER BY MAX(sets.weight) DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        self.display_area.insert(tk.END, "--- 自己ベスト ---\n")
        for r in rows:
            self.display_area.insert(tk.END, f"{r[0]}: {r[1]}kg\n")

    def open_add_exercise_window(self):
        win = tk.Toplevel(self.root)
        win.title("種目追加")
        win.geometry("300x150")
        
        tk.Label(win, text="新しい種目名:").pack(pady=5)
        ent = tk.Entry(win)
        ent.pack(pady=5)
        
        def save():
            name = ent.get()
            if name:
                conn = get_db_connection()
                conn.execute('INSERT INTO exercises (name) VALUES (?)', (name,))
                conn.commit()
                conn.close()
                self.refresh_exercises()
                win.destroy()
        
        tk.Button(win, text="追加", command=save).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkoutApp(root)
    root.mainloop()