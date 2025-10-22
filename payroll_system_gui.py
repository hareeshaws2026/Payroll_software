import sqlite3
import tkinter as tk
from tkinter import messagebox

# Initialize DB
def initialize_db():
    connection = sqlite3.connect('payroll_system.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        S_No INTEGER,
        employee_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        designation TEXT,
        basic REAL,
        da REAL,
        uan_number TEXT,
        esic_number TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        S_No INTEGER,
        employee_id INTEGER,
        month TEXT,
        working_days INTEGER,
        basic_amount REAL,
        da_amount REAL,
        gross_salary REAL,
        deductions REAL,
        net_salary REAL,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )
    ''')

    # migration: if older columns exist (basic, da) copy them into new names
    cursor.execute("PRAGMA table_info(employees)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'basic_salary' not in cols and 'basic' in cols:
        cursor.execute("ALTER TABLE employees ADD COLUMN basic_salary REAL")
        cursor.execute("UPDATE employees SET basic_salary = basic")
    if 'da' not in cols and 'da' in cols:
        cursor.execute("ALTER TABLE employees ADD COLUMN da REAL")
        cursor.execute("UPDATE employees SET da = da")

    # ensure payroll has basic_amount / da_amount in older DBs
    try:
        cursor.execute("ALTER TABLE payroll ADD COLUMN basic_amount REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE payroll ADD COLUMN da_amount REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()

# Add employee to DB
def add_employee(S_No, employee_id, name, designation, basic_salary, da, uan_number, esic_number):
    connection = sqlite3.connect('payroll_system.db')
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO employees (S_No, employee_id, name, designation, basic_salary, da, uan_number, esic_number)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (S_No, employee_id, name, designation, basic_salary, da, uan_number, esic_number))
    connection.commit()
    connection.close()

def generate_payroll(employee_db_id, month, working_days, deductions, da_override=None):
    connection = sqlite3.connect('payroll_system.db')
    cursor = connection.cursor()
    cursor.execute('SELECT basic_salary, S_No, da_percent FROM employees WHERE id = ?', (employee_db_id,))
    row = cursor.fetchone()
    if not row:
        connection.close()
        return None
    basic_salary, s_no, da_db = row
    # ensure floats
    basic_salary = float(basic_salary or 0.0)
    da_db = float(da_db or 0.0)
    da = float(da_override) if da_override is not None else da_db
    base_gross = (basic_salary / 30.0) * float(working_days)
    da_amount = base_gross * (da / 100.0)
    gross_salary = base_gross + da_amount
    net_salary = gross_salary - float(deductions)
    cursor.execute('''INSERT INTO payroll (S_No, employee_id, month, working_days, basic_amount, da_amount, gross_salary, deductions, net_salary)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (s_no, employee_db_id, month, working_days, base_gross, da_amount, gross_salary, deductions, net_salary))
    connection.commit()
    connection.close()
    # return numeric values so caller can display them (floats)
    return (base_gross, da_amount, gross_salary, net_salary)

# GUI code
def run_gui():
    def on_add_employee():
        try:
            s_no_raw = entry_number.get().strip()
            S_No = int(s_no_raw) if s_no_raw != '' else None
            employee_id = entry_empid.get().strip()
            name = entry_name.get()
            designation = entry_designation.get()
            basic_salary = float(entry_salary.get())
            da_percent = float(entry_da.get().strip()) if entry_da.get().strip() != '' else 0.0
            uan = entry_uan.get()
            esic = entry_esic.get()
            add_employee(S_No, employee_id, name, designation, basic_salary, da_percent, uan, esic)
            messagebox.showinfo("Success", f"Employee {name} added.")
            entry_number.delete(0, tk.END)
            entry_empid.delete(0, tk.END)
            entry_name.delete(0, tk.END)
            entry_designation.delete(0, tk.END)
            entry_salary.delete(0, tk.END)
            entry_da.delete(0, tk.END)
            entry_uan.delete(0, tk.END)
            entry_esic.delete(0, tk.END)
            update_employee_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_generate_payroll():
        try:
            emp_id = int(employee_var.get().split(':')[0])
            month = entry_month.get()
            working_days = int(entry_days.get())
            deductions = float(entry_deductions.get() or 0.0)
            da_raw = entry_pay_da.get().strip()
            da_override = float(da_raw) if da_raw != '' else None
            result = generate_payroll(emp_id, month, working_days, deductions, da_override)
            if result:
                base_gross, da_amount, gross_salary, net_salary = result
                messagebox.showinfo(
                    "Success",
                    f"Payroll generated for Employee ID {emp_id}.\nBasic: {base_gross:.2f}\nDA: {da_amount:.2f}\nGross: {gross_salary:.2f}\nNet: {net_salary:.2f}"
                )
            else:
                messagebox.showerror("Error", "Invalid Employee.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_employee_list():
        connection = sqlite3.connect('payroll_system.db')
        cursor = connection.cursor()
        cursor.execute('SELECT id, name FROM employees')
        employees = cursor.fetchall()
        connection.close()
        employee_var.set('')
        employee_menu['menu'].delete(0, 'end')
        for emp in employees:
            employee_menu['menu'].add_command(label=f"{emp[0]}: {emp[1]}", command=tk._setit(employee_var, f"{emp[0]}: {emp[1]}"))

    root = tk.Tk()
    root.title("Payroll System GUI")

    # Add Employee Frame
    frame_add = tk.LabelFrame(root, text="Add Employee", padx=10, pady=10)
    frame_add.grid(row=0, column=0, padx=10, pady=10)

    tk.Label(frame_add, text="S No:").grid(row=0, column=0)
    entry_number = tk.Entry(frame_add)
    entry_number.grid(row=0, column=1)

    tk.Label(frame_add, text="Employee ID:").grid(row=1, column=0)
    entry_empid = tk.Entry(frame_add)
    entry_empid.grid(row=1, column=1)

    tk.Label(frame_add, text="Name:").grid(row=2, column=0)
    entry_name = tk.Entry(frame_add)
    entry_name.grid(row=2, column=1)

    tk.Label(frame_add, text="Designation:").grid(row=3, column=0)
    entry_designation = tk.Entry(frame_add)
    entry_designation.grid(row=3, column=1)

    tk.Label(frame_add, text="Basic Salary:").grid(row=4, column=0)
    entry_salary = tk.Entry(frame_add)
    entry_salary.grid(row=4, column=1)

    tk.Label(frame_add, text="DA %:").grid(row=5, column=0)
    entry_da = tk.Entry(frame_add)
    entry_da.grid(row=5, column=1)

    tk.Label(frame_add, text="UAN Number:").grid(row=6, column=0)
    entry_uan = tk.Entry(frame_add)
    entry_uan.grid(row=6, column=1)

    tk.Label(frame_add, text="ESIC Number:").grid(row=7, column=0)
    entry_esic = tk.Entry(frame_add)
    entry_esic.grid(row=7, column=1)

    btn_add = tk.Button(frame_add, text="Add Employee", command=on_add_employee)
    btn_add.grid(row=8, columnspan=2, pady=10)

    # Generate Payroll Frame
    frame_payroll = tk.LabelFrame(root, text="Generate Payroll", padx=10, pady=10)
    frame_payroll.grid(row=1, column=0, padx=10, pady=10)

    employee_var = tk.StringVar(root)
    employee_menu = tk.OptionMenu(frame_payroll, employee_var, '')

    tk.Label(frame_payroll, text="Employee:").grid(row=0, column=0)
    employee_menu.grid(row=0, column=1)

    tk.Label(frame_payroll, text="DA % (enter to override employee DA):").grid(row=1, column=0)
    entry_pay_da = tk.Entry(frame_payroll)
    entry_pay_da.grid(row=1, column=1)

    tk.Label(frame_payroll, text="Month (e.g. October 2025):").grid(row=2, column=0)
    entry_month = tk.Entry(frame_payroll)
    entry_month.grid(row=2, column=1)

    tk.Label(frame_payroll, text="Working Days:").grid(row=3, column=0)
    entry_days = tk.Entry(frame_payroll)
    entry_days.grid(row=3, column=1)

    tk.Label(frame_payroll, text="Deductions:").grid(row=4, column=0)
    entry_deductions = tk.Entry(frame_payroll)
    entry_deductions.grid(row=4, column=1)

    btn_payroll = tk.Button(frame_payroll, text="Generate Payroll", command=on_generate_payroll)
    btn_payroll.grid(row=5, columnspan=2, pady=10)

    update_employee_list()
    root.mainloop()

if __name__ == '__main__':
    initialize_db()
    run_gui()
