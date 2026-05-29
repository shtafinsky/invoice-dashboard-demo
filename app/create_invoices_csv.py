import pandas as pd
import random
import calendar as cl
from datetime import datetime as dt, timedelta as tdl, date as dd

# Kundenliste (typisch CH/DE KMU)
customers = [
    "Müller AG", "Meier GmbH", "Keller AG",
    "Weber AG", "Huber GmbH", "Schmid AG",
    "coop AG", "Migros AG", "Payfix GmbH,"
    "Wallee AG", "City Kiosk Bern"
]

# Jaht
cur_year=2023
# Status
statuses = ["bezahlt", "offen", "überfällig"]

today=dt.today()

data = []

for month in range(1,13): # 12 monate
    for i in range(1, 110):  # 20 Rechnungen pro Monat   
       # zufälliges Datum in einem Monat vom 2025 
       days_in_month=cl.monthrange(cur_year,month)[1]
       random_day = random.randint(1, days_in_month)
       start_date=dd(cur_year,month,1)
       inv_date = start_date + tdl(days=random_day)
       order_date = inv_date - tdl(days=2)

       if inv_date <= today.date() and \
          inv_date.year == cur_year:
          customer = random.choice(customers)
          total_netto = round(random.uniform(100, 5000), 2)
          vat = round((total_netto * 1.081),2)
          end_total = round((total_netto + vat),2)
          status = random.choice(statuses)

          invoice_nr = f"INV-{cur_year}-{month}{i:04d}"

          data.append([
              invoice_nr,
              inv_date.strftime("%Y-%m-%d"),
              order_date.strftime("%Y-%m-%d"),
              customer,
              total_netto,
              vat,
              end_total,
              status
           ])

# DataFrame erstellen
df = pd.DataFrame(data, columns=[
    "Rechnung Nr", "Rechnung Datum", "Auftrag Datum", "Kunde", "Total ohne MwSt", 
    "MwSt 8.1%", "Endtotal", "Status"
])

# als CSV speichern
df.to_csv(f"D:/MyData/Python/invoices/data/rechnungen_{cur_year}.csv", index=False, sep=";",encoding="utf-8")
df = pd.read_csv(f"D:/MyData/Python/invoices/data/rechnungen_{cur_year}.csv", encoding="utf-8",sep=";")
print(df.columns)
df["Rechnung Datum"]=pd.to_datetime(df["Rechnung Datum"],format="%Y-%m-%d")
df["Auftrag Datum"]=pd.to_datetime(df["Auftrag Datum"],format="%Y-%m-%d")

print("Datei erstellt!")