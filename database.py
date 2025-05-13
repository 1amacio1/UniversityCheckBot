import pandas as pd
import sqlite3
#импортируем библиотеку для работы с базой данных и работой с excel файлами

#название файла
excel_file = 'vuzi.xlsx'

#считываем excel файл
df = pd.read_excel(excel_file)

#поддключаемся к базе данных, если её нет, то создается новая
conn = sqlite3.connect("vuzes.db")

#данные из excel файла записываются в базу данных
df.to_sql("universities", conn, if_exists="replace", index=False)

#закрываем базу данных 
conn.close()