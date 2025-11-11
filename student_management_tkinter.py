import sqlite3
import csv
import os
from tkinter import *
from tkinter import ttk, messagebox, filedialog

DB_NAME = 'students.db'

# ---------- Database helpers ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            course TEXT,
            marks REAL
        )
    ''')
    conn.commit()
    conn.close()


def insert_student(roll, name, age, course, marks):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('INSERT INTO students (roll, name, age, course, marks) VALUES (?, ?, ?, ?, ?)',
                    (roll, name, age, course, marks))
        conn.commit()
        conn.close()
        return True, 'Student added successfully.'
    except sqlite3.IntegrityError:
        return False, 'Error: Roll number already exists.'
    except Exception as e:
        return False, f'Error: {e}'


def fetch_all_students():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT roll, name, age, course, marks FROM students ORDER BY roll')
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_student(roll):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT roll, name, age, course, marks FROM students WHERE roll = ?', (roll,))
    row = cur.fetchone()
    conn.close()
    return row


def update_student(roll, name, age, course, marks):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE students SET name=?, age=?, course=?, marks=? WHERE roll=?',
                (name, age, course, marks, roll))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def delete_student(roll):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM students WHERE roll = ?', (roll,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


# ---------- GUI ----------
class StudentApp:
    def __init__(self, root):
        self.root = root
        root.title('Student Management System')
        root.geometry('820x520')
        root.resizable(False, False)

        # --- Input frame ---
        self.frm_input = LabelFrame(root, text='Student Details', padx=10, pady=10)
        self.frm_input.place(x=10, y=10, width=400, height=220)

        Label(self.frm_input, text='Roll No:').grid(row=0, column=0, sticky=W)
        Label(self.frm_input, text='Name:').grid(row=1, column=0, sticky=W)
        Label(self.frm_input, text='Age:').grid(row=2, column=0, sticky=W)
        Label(self.frm_input, text='Course:').grid(row=3, column=0, sticky=W)
        Label(self.frm_input, text='Marks (%):').grid(row=4, column=0, sticky=W)

        self.var_roll = StringVar()
        self.var_name = StringVar()
        self.var_age = StringVar()
        self.var_course = StringVar()
        self.var_marks = StringVar()

        Entry(self.frm_input, textvariable=self.var_roll, width=22).grid(row=0, column=1, pady=4)
        Entry(self.frm_input, textvariable=self.var_name, width=22).grid(row=1, column=1, pady=4)
        Entry(self.frm_input, textvariable=self.var_age, width=22).grid(row=2, column=1, pady=4)
        Entry(self.frm_input, textvariable=self.var_course, width=22).grid(row=3, column=1, pady=4)
        Entry(self.frm_input, textvariable=self.var_marks, width=22).grid(row=4, column=1, pady=4)

        # Buttons
        btn_add = Button(self.frm_input, text='Add Student', width=14, command=self.add_student)
        btn_add.grid(row=5, column=0, pady=8)
        btn_update = Button(self.frm_input, text='Update Student', width=14, command=self.update_student)
        btn_update.grid(row=5, column=1, pady=8)

        btn_clear = Button(self.frm_input, text='Clear Fields', width=30, command=self.clear_fields)
        btn_clear.grid(row=6, column=0, columnspan=2, pady=4)

        # --- Search & Actions ---
        self.frm_actions = LabelFrame(root, text='Actions', padx=10, pady=10)
        self.frm_actions.place(x=420, y=10, width=380, height=220)

        Label(self.frm_actions, text='Search by Roll No:').grid(row=0, column=0, sticky=W)
        self.var_search = StringVar()
        Entry(self.frm_actions, textvariable=self.var_search, width=20).grid(row=0, column=1, pady=6)
        btn_search = Button(self.frm_actions, text='Search', width=12, command=self.search_student)
        btn_search.grid(row=0, column=2, padx=6)

        btn_view = Button(self.frm_actions, text='View All', width=12, command=self.load_students)
        btn_view.grid(row=1, column=0, pady=6)
        btn_delete = Button(self.frm_actions, text='Delete', width=12, command=self.delete_selected)
        btn_delete.grid(row=1, column=1, pady=6)
        btn_export = Button(self.frm_actions, text='Export CSV', width=12, command=self.export_csv)
        btn_export.grid(row=1, column=2, pady=6)

        # --- Table frame ---
        self.frm_table = Frame(root)
        self.frm_table.place(x=10, y=240, width=790, height=260)

        cols = ('roll', 'name', 'age', 'course', 'marks')
        self.tree = ttk.Treeview(self.frm_table, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=140 if c != 'name' else 200)

        vsb = ttk.Scrollbar(self.frm_table, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self.frm_table, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_row_select)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.frm_table.grid_rowconfigure(0, weight=1)
        self.frm_table.grid_columnconfigure(0, weight=1)

        # initialize
        self.load_students()

    # ---------- UI actions ----------
    def add_student(self):
        roll = self.var_roll.get().strip()
        name = self.var_name.get().strip()
        age = self.var_age.get().strip()
        course = self.var_course.get().strip()
        marks = self.var_marks.get().strip()

        if not roll or not name:
            messagebox.showwarning('Input error', 'Roll and Name are required.')
            return

        # basic validation
        try:
            age_val = int(age) if age else None
        except ValueError:
            messagebox.showwarning('Input error', 'Age must be a number.')
            return

        try:
            marks_val = float(marks) if marks else None
        except ValueError:
            messagebox.showwarning('Input error', 'Marks must be a number.')
            return

        ok, msg = insert_student(roll, name, age_val, course, marks_val)
        if ok:
            messagebox.showinfo('Success', msg)
            self.load_students()
            self.clear_fields()
        else:
            messagebox.showerror('Error', msg)

    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = fetch_all_students()
        for r in rows:
            self.tree.insert('', END, values=r)

    def search_student(self):
        roll = self.var_search.get().strip()
        if not roll:
            messagebox.showwarning('Input error', 'Please enter a roll number to search.')
            return
        row = fetch_student(roll)
        if row:
            # select in treeview
            for item in self.tree.get_children():
                if self.tree.item(item)['values'][0] == roll:
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break
            # populate fields
            self.var_roll.set(row[0])
            self.var_name.set(row[1])
            self.var_age.set(row[2] if row[2] is not None else '')
            self.var_course.set(row[3] if row[3] is not None else '')
            self.var_marks.set(row[4] if row[4] is not None else '')
        else:
            messagebox.showinfo('Not found', 'No student with that roll number.')

    def on_row_select(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])['values']
            self.var_roll.set(vals[0])
            self.var_name.set(vals[1])
            self.var_age.set(vals[2])
            self.var_course.set(vals[3])
            self.var_marks.set(vals[4])

    def update_student(self):
        roll = self.var_roll.get().strip()
        if not roll:
            messagebox.showwarning('Input error', 'Please select a student to update (Roll required).')
            return
        name = self.var_name.get().strip()
        try:
            age_val = int(self.var_age.get().strip()) if self.var_age.get().strip() else None
        except ValueError:
            messagebox.showwarning('Input error', 'Age must be a number.')
            return
        try:
            marks_val = float(self.var_marks.get().strip()) if self.var_marks.get().strip() else None
        except ValueError:
            messagebox.showwarning('Input error', 'Marks must be a number.')
            return

        ok = update_student(roll, name, age_val, self.var_course.get().strip(), marks_val)
        if ok:
            messagebox.showinfo('Success', 'Student record updated.')
            self.load_students()
            self.clear_fields()
        else:
            messagebox.showerror('Error', 'Update failed. Is the roll number correct?')

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selection error', 'Please select a student in the table to delete.')
            return
        roll = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno('Confirm Delete', f'Are you sure you want to delete roll {roll}?'):
            ok = delete_student(roll)
            if ok:
                messagebox.showinfo('Deleted', 'Student deleted successfully.')
                self.load_students()
                self.clear_fields()
            else:
                messagebox.showerror('Error', 'Delete failed.')

    def export_csv(self):
        rows = fetch_all_students()
        if not rows:
            messagebox.showinfo('No data', 'No student records to export.')
            return
        fpath = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
        if not fpath:
            return
        try:
            with open(fpath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Roll', 'Name', 'Age', 'Course', 'Marks'])
                writer.writerows(rows)
            messagebox.showinfo('Exported', f'Exported {len(rows)} records to {os.path.basename(fpath)}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to export CSV: {e}')

    def clear_fields(self):
        self.var_roll.set('')
        self.var_name.set('')
        self.var_age.set('')
        self.var_course.set('')
        self.var_marks.set('')
        self.var_search.set('')


# ---------- main ----------
if __name__ == '__main__':
    init_db()
    root = Tk()
    app = StudentApp(root)
    root.mainloop()
