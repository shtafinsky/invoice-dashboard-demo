from pathlib import Path

# to make it platform independent
#base_path = Path("D:/MyData/Python/invoices")
# _file_ - folder of the script, resolve creats an absolut path
# base_path = Path(__file__).resolve().parent.parent
# data_folder = base_path / "data"

file_name_format = "rechnungen_YYYY.csv"

APP_NAME = "InvoiceDashboard"
DATA_CONFIG = "data_config.json"


required_cols = {
    "Rechnung Nr": None,
    "Rechnung Datum": "date",
    "Auftrag Datum": "date",
    "Kunde": None,
    "Total ohne MwSt": "numeric",
    "MwSt 8.1%": "numeric",
    "Endtotal": "numeric",
    "Status": "status"
                }
key = "Rechnung Nr"

invoice_status_dic = {
     "paid": "bezahlt",
     "open": "offen",
     "overdue": "überfällig"
                     }
invoice_status = list(invoice_status_dic.values())

validation_errors = {
    "date_invalid": "Ungültiges Datumformat",
    "non_numeric": "Betrag ist nicht nummerisch",
    "status_invalid": "Status ist ungültig",
    "missing_column": "Spalte '{column}' fehlt in der Datei",
    "missing_value": "Wert fehlt"
    }

# chart colors
PALETTES = {
    "monthly": {
        "current": "#1f77b4",
        "previous": "#a6cbe8"
    },
    "customer": {
        "default": "#ff7f0e"
    }
}
# month names
month_names={
    "de": ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],
    "en": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Okt","Nov","Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin","juil.", "août", "sept.","oct.", "nov.", "déc."],
    "it": ["gen", "feb", "mar", "apr", "mag", "giu","lug", "ago", "set", "ott", "nov", "dic"]
}

# attributes to be taken for calculation on dashboards

dashboard_attributes = {
    "amount": "Endtotal",
    "customer": "Kunde",
    "invoice_nr": "Rechnung Nr",
    "status": "Status",
    "date": "Rechnung Datum"
}

# Chart lables
chart_label = {
    "sales_for_month": "Umsatz pro Monat",
    "sales_for_customer": "Umsatz pro Kunde",
    "invoices_for_month": "Rechnungen pro Monat",
    "invoices_for_customer": "Rechnungen pro Kunde" 
}

# Axis labels
axis_lable = {
    "sales_for_month_axis": ("Monat","Umsatz"),
    "sales_for_customer_axis": ("Kunden","Umsatz"),
    "invoices_for_month_axis": ("Monat","Rechnungen"),
    "invoices_for_customer_axis": ("Kunden","Rechnungen")     
}

language = "de"