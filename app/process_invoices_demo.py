import pandas as pd
import streamlit as st
from datetime import datetime as dtt
import os, calendar, locale
import numpy as np
import re
import plotly.express as px
import plotly.io as pio
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
import io
# application owns
from show_error_editor import edit_error
from process_input_data import validate
import app_config  
from path import load_config,  save_config 

import logging
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).resolve().parents[1] / "debug.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True
)

def debug(msg):
    logging.info(msg)

# dashboard view
view_sales = "sale"
view_invoices = "invoice"
view_dev = "development"
view_errors = "errors"
view_show = "show"

monthly_chart = "monthly"
customer_chart = "customer"

#--------------------------------------
    
# reset/initialization of session processing statuses
def init_state():
    # App control
    st.session_state.setdefault("initialized", False)
    st.session_state.setdefault("view", None)

    # data
    st.session_state.setdefault("year", None)
    st.session_state.setdefault("year_err", None)       # related to the DF with errors
    st.session_state.setdefault("df", None)
    st.session_state.setdefault("df_err", None)         # DF with errors

    if "data_folder" not in st.session_state:   
        st.session_state["data_folder"] = Path(config["data_folder"])
        #st.session_state["data_folder"] = get_data_folder()  

    # export
    st.session_state.setdefault("pdf_buffer", None)
    st.session_state.setdefault("figs",None)

    # error levels
    st.session_state.setdefault("messages", {
        "error": [],
        "warning": [],
        "info": []
        })
    
# claening of messages
def clear_messages():
    st.session_state.messages = {"error": [], "warning": [], "info": []}

# End app
def shutdown_app():
    st.session_state.clear()
    os._exit(0)

# Data loading - data will be cached
@st.cache_data
def load_data(path):

    # 1. File check
    if not Path(path).exists():
        st.error("CSV-Datei nicht gefunden")
        return None

    # 2. Encoding fallback    
    for enc in ["utf-8", "cp1252", "latin1"]:
        try:
            return pd.read_csv(path, encoding=enc, sep=";")
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            st.error("CSV Struktur fehlerhaft (Trennzeichen oder Format)")
            return None

    st.error("CSV Encoding konnte nicht erkannt werden")
    return None

# dataframe cache cleaning
def clear_cache_df():
    if "df" in st.session_state:
        del st.session_state["df"]     
    if "df_err" in st.session_state:
        del st.session_state["df_err"]     

# clear session data
def clear_session_data():
    st.session_state.figs=None
    st.session_state.year=None
    st.session_state.pdf_buffer=None
    st.session_state.initialized = False
    st.session_state.view = None    

# setting of aktiv view
def set_view(view):
    st.session_state.view = view
    st.session_state.pdf_buffer = None
    clear_messages()
    st.rerun()

# displaying of dashboards
def show_dashboard():

    figs = None  # initialization

    if st.session_state.view == view_sales:
        figs=display_sales(st.session_state.df)

    elif st.session_state.view == view_invoices:
        figs=display_invoices(st.session_state.df)

    elif st.session_state.view == view_dev:
        status, df_prev = read_csv_prev()

        if status == "ok":
            figs=display_development(st.session_state.df, df_prev)

        elif status == "error":
            st.session_state.view = view_errors
            st.session_state.df_err = df_prev
            st.session_state.year_err = st.session_state.year-1
            st.rerun()
        elif status == "missing":
            st.session_state.view = None            
        else:      
            set_view(view_sales)                      # no errors but just warnings
            #st.rerun()    
    elif st.session_state.view == view_errors:
        if st.session_state.messages["error"]:
            # modul show_error_editor for error correction
            edit_error(st.session_state.df_err,  
                            st.session_state.year_err)       
            #clear_cache_df()        
    else:
        set_view(view_sales)

    if figs:
        if any(f is None for f in figs):
            st.error("Fehler beim Erstellen der Diagramme")
            return None

    st.session_state.figs = figs   # save diagrams for export 

# show csv files
def show_csv_file():
    print("show_csv_file")
    st.dataframe(st.session_state.df)

# creating pdf from image
def create_pdf(figures, filename="report.pdf", title="Dashboard Report"):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    # Titel
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 20))

    # Charts
    for i,fig in enumerate(figures):
        img_bytes = fig_to_image(fig)
        img_buffer = io.BytesIO(img_bytes)

        # doc has predefined width and hight
        img = Image(img_buffer)

        # size of the image rended by plotly
        orig_w = img.drawWidth    
        orig_h = img.drawHeight
        
        # adjusted size of the image
        img.drawWidth = doc.width
        img.drawHeight = orig_h * (doc.width / orig_w)

        elements.append(img)

        # Spacer nur wenn NICHT letztes Element
        if i < len(figures) - 1:
            elements.append(Spacer(1, 20))

    doc.build(elements)

    buffer.seek(0)
    return buffer

# converting figure to image
def fig_to_image(fig):
    return pio.to_image(fig, format="png", scale=2)

# check for availabilty of csv files
def load_and_validate_csv(year):

    file_name=app_config.file_name_format.replace('YYYY',f'{year}')

    file_path_base = st.session_state.data_folder    #get_data_folder()

    file_path = Path(file_path_base)/file_name
    #file_path = f'{file_path_base}/{file_name}'

    try:
        df = load_data(file_path)
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return False, None

    debug(f"st.session_state.view = {st.session_state.view}")

    if st.session_state.view == view_show:
        ok = True
    else:
        ok, df = validate(df)

    if not ok:
        return False, df

    return True, df        

# displays dasboard
def display_sidebar():
    with st.sidebar:

        st.markdown("## 📊 Dashboard")
        st.markdown("---")

        is_disabled = not st.session_state.get("initialized",False)

        st.markdown("### Navigation")

        if st.button("📊 Umsätze", 
                     key="nav_sales",
                     use_container_width=True,
                     disabled=is_disabled,
                    type="primary" if st.session_state.view == view_sales else "secondary"):
            set_view(view_sales)

        if st.button("📄 Rechnungen", 
                     key="nav_invoices",
                     use_container_width=True,
                     disabled=is_disabled,
                    type="primary" if st.session_state.view == view_invoices else "secondary"):
            set_view(view_invoices)

        if st.button("📈 Entwicklung",
                     key="nav_development",
                     use_container_width=True,
                     disabled=is_disabled,
                    type="primary" if st.session_state.view == view_dev else "secondary"):
            set_view(view_dev)    

        st.markdown("---")
        st.markdown("### Aktionen")

        if st.button("📄 PDF erstellen",
                     key="pdf_creation",
                     use_container_width=True,
                     disabled=is_disabled,
                     ):
            if st.session_state.figs is None:
                return

            figs=st.session_state.get("figs")

            if figs:
                with st.spinner("PDF wird erstellt..."):
                    st.session_state.pdf_buffer = create_pdf(figs)

        if st.session_state.get("pdf_buffer"):
            st.download_button(
                "⬇️ PDF herunterladen",
                data=st.session_state.pdf_buffer,
                file_name="report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        if st.button("🔙 Neues Jahr wählen", 
                     key="new_year_selection",
                     use_container_width=True):
                     #disabled=is_disabled):
            load_data.clear()  # clear of the load data cache
            #clear_messages()
            #clear_cache_df()
            clear_session_data()
            st.rerun() 

        if st.sidebar.button("⏻ Beenden", 
                             type="primary",
                             use_container_width=True):
            shutdown_app()

        with st.sidebar.expander("Debug-Log anzeigen"):
            if LOG_FILE.exists():
                st.text(LOG_FILE.read_text(encoding="utf-8")[-5000:])
            else:
                st.write("Noch kein Log vorhanden.")            

# formating of amounts in hover
def format_chf(value):
    return f"CHF {value:,.2f}".replace(",", "'")

# formating of amounts in percentage
def format_percentage(value):
    return f"{value:,.2%}"

# formating of amounts on the bars
def format_short(value):
    if isinstance(value, (int, np.integer)):
        return(str(f"{value:,}".replace(",", "'")))
    else:
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.0f}k"
        elif abs(value) > 0:
            return(str(int(value)))
        else:
            return ""

# selecting of bar colors based on number of series (cur-year and prev-yrear)
def get_color_sequence(chart_type, n_series):
    palette = app_config.PALETTES.get(chart_type, {})

    if chart_type == "monthly":
        if n_series == 1:
            return [palette["current"]]
        elif n_series == 2:
            return [palette["current"], palette["previous"]]

    elif chart_type == "customer":
        return [palette["default"]]

    return ["#cccccc"] * n_series  # fallback 

# aggregation over months
@st.cache_data
def monthly_aggregation(df, col, op):
# grouping by month and aggregation by <col> and calculating as <op>
    date = app_config.dashboard_attributes.get("date",None)
    df = df.copy()
    df["month"]=df[date].dt.month

    monthly = (
        df.groupby("month")
        .agg({col: op})
        .reindex(range(1,13), fill_value=0)    # in case if there were no value in a month
    )

    return monthly

# building of dictionary series out of dataframes, lists,...
def build_series(name, labels, values):
    return {
        "name": name,
        "labels": list(labels),
        "values": list(values)
        }

# reading of previous year file
def read_csv_prev():

    # statuses: "ok" - no errors, "missing" - no file available, "error" - wrong data in the file

    file_name=app_config.file_name_format.replace('YYYY',f'{st.session_state.year-1}')

    file_path_base = st.session_state.data_folder    #get_data_folder()
    file_path = Path(file_path_base)/file_name
    #file_path = f'{file_path_base}/{file_name}'    
    
    if not os.path.exists(file_path):
        st.warning(f"Keine Daten für {st.session_state.year-1} vorhanden")
        return "missing", None
    else:        
        df_prev = load_data(file_path)
        ok, df_prev = validate(df_prev)     # Validation of input data        
        
        if not ok:
            return "error", df_prev
        else:        
            return "ok", df_prev

# plotting of a bar chart using plotly express
def plot_bar_chart_px(data_series,            # data_series: one or multiple series of presented data
                      crt_title,              # titel: chart titel
                      crt_labels,             # axis labels (x,y)
                      format_bar,             # format for amounts on the bars
                      format_hover,           # format for amount in hover 
                      chart_type="monthly"):  # monthly or customer chart, default - monthly                      

    if not data_series:
       st.warning("Keine Daten vorhanden")
       return

    rows=[]                               # list of all data series

    for serie in data_series:
        for i,value in enumerate(serie["values"]):
            rows.append({
                "label": serie["labels"][i],
                "value": value,
                "serie": serie["name"]
                })

    df_plot = pd.DataFrame(rows)

    df_plot["Text"]=df_plot["value"].apply(format_bar)

    df_plot["Hover"]=df_plot["value"].apply(format_hover)


    
    n_series = df_plot["serie"].nunique()

    # generate colors for series based on the based color 
    color_sequence = get_color_sequence(chart_type, n_series)

    x_lable = crt_labels[0]
    y_lable = crt_labels[1]

    fig = px.bar(
        df_plot,
        x= "label",
        y="value",
        color="serie",
        text="Text",
        custom_data=["Hover"],
        barmode="group",
        title=crt_title,
        color_discrete_sequence=color_sequence,
        labels={
            "label": x_lable,
            "value": y_lable,
            "serie": "Jahr"
        }
    )

    fig.update_traces(
        texttemplate="<b>%{text}</b>",        
        textfont=dict(color="black",),
        textposition="outside",
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True,
            gridcolor="#d0d0d0",
            gridwidth=1.5
            ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#d0d0d0",
            gridwidth=1.5
            ),
        xaxis_tickangle=-30,
        showlegend=(len(data_series) > 1),
        legend_title_text=""
    )    

    st.plotly_chart(fig, width="stretch")

    return fig

# input-form for year selection 
def show_year_selector(years):

    st.title("📊 Rechnungs-Dashboard")
    st.caption("Analyse von Umsätzen und Rechnungen")

    col1, col2, col3 = st.columns([2,1,1])
    with col1:

        with st.form("year-input",clear_on_submit=True):
            report_year=st.selectbox("Jahr auswählen",
                                    years,
                                    help="Wählen Sie das Jahr für die Analyse")
            submitted_dashboard=st.form_submit_button("Dashboard laden 🚀",
                                            use_container_width=True)
            submitted_show_files=st.form_submit_button("Datei anzeigen 📄",
                                            use_container_width=True)

    if submitted_dashboard or submitted_show_files:
        clear_messages()
        clear_cache_df()
        #clear_session_data()
        #load_data.clear()

        st.session_state.initialized=True

        success, df = load_and_validate_csv(report_year)

        st.session_state.df=df

        if not success:
            st.session_state.view = view_errors
            st.session_state.df_err = st.session_state.df
            st.session_state.year_err = report_year
        else:
            st.session_state.year=report_year  
            if submitted_dashboard:
                set_view(view_sales)
            if submitted_show_files:
                set_view(view_show)
        st.rerun()

# Dashboard for sales
def display_sales(df):

    data = calculate_sales(df,st.session_state.year)    

    st.title(f"Umsätze {st.session_state.year}")
    st.caption("Analyse von Umsatz und Rechnungen")
    
    # KPI's
    cols = st.columns(2)

    cols[0].metric(
        label="Total Umsatz",
        value=data['total_sales']
        )
    cols[1].metric(
        label="Durchschnittlicher Rechnungsbetrag",
        value=data['avg_sales']
        )
    
    # charts
    fig_sales_monthly = plot_bar_chart_px(data["monthly_series"],
                                        app_config.chart_label["sales_for_month"],
                                        app_config.axis_lable["sales_for_month_axis"],                                         
                                        format_short,
                                        format_chf,
                                        monthly_chart)                                        
    

    fig_customer_sales = plot_bar_chart_px(data["customer_series"],
                                        app_config.chart_label["sales_for_customer"],
                                        app_config.axis_lable["sales_for_customer_axis"],                                         
                                        format_short,
                                        format_chf,
                                        customer_chart)                                               
    
    return(fig_sales_monthly,fig_customer_sales)

# sales will be calculated
def calculate_sales(df,year):
    amount = app_config.dashboard_attributes.get("amount",None)
    customer = app_config.dashboard_attributes.get("customer",None)

    total_sales=df[amount].sum()
    total_sales_formatted=format_chf(total_sales)
    avg_sales=df[amount].mean()
    avg_sales_formatted=format_chf(avg_sales)


    # Gruppieren auf neue Spalte "month" und summe monatlicher Umsätze sowie anzahl der rechnungen

    monthly_sales=monthly_aggregation(df, amount, "sum")

    # normalized serie for processing by the plot_bar_chat
    monthly_series = [
                    build_series(
                                str(year),
                                app_config.month_names[app_config.language],
                                list(monthly_sales[amount]))
                    ]    

    customer_sales=(
        df.groupby(customer)
        .agg({amount: "sum"})
        .sort_values(by=amount, ascending=False)
        .head(10)
    )
    customers = customer_sales.index # Kunden holen

    # normalized serie for processing by the plot_bar_chat
    customer_series = [
                    build_series(
                                str(year),
                                customers,
                                list(customer_sales[amount]))
                    ]

    return{"total_sales": total_sales_formatted,
           "avg_sales": avg_sales_formatted,
           "monthly_series": monthly_series,
           "customer_series": customer_series
            }

# Dashboard for invoices
def display_invoices(df):
    data = calculate_invoices(df,st.session_state.year)

    st.title(f"Rechnungen {st.session_state.year}")
    st.caption("Analyse von Umsatz und Rechnungen")
    
    # KPI's
    cols = st.columns(4)

    cols[0].metric(
        label="Total Rechnungen",
        value=data['total_invoices']
        )
    cols[1].metric(
        label="Total bezahlter Rechnungen",
        value=data['invoices_paid']
        )    
    cols[2].metric(
        label="Total offener Rechnungen",
        value=data['invoices_open']
        )  
    cols[3].metric(
        label="Total überfälliger Rechnungen",
        value=data['invoices_overdue']
        )         

    # charts
    
    fig_monthly_invoices = plot_bar_chart_px(data["monthly_series"],
                                            app_config.chart_label["invoices_for_month"],
                                            app_config.axis_lable["invoices_for_month_axis"],
                                            format_short,
                                            format_short,
                                            monthly_chart)                                           
    
    fig_customer_invoices = plot_bar_chart_px(data["customer_series"],
                                            app_config.chart_label["invoices_for_customer"],
                                            app_config.axis_lable["invoices_for_customer_axis"],
                                            format_short,
                                            format_short,
                                            customer_chart)                                             

    return(fig_monthly_invoices,fig_customer_invoices)   

# calculate of invoices data
def calculate_invoices(df,year):
    invoice = app_config.dashboard_attributes.get("invoice_nr",None)
    status  = app_config.dashboard_attributes.get("status",None)
    customer = app_config.dashboard_attributes.get("customer",None)

    total_invoices=df[invoice].count()

    status_series = df[status]

    # invoice_status defines the statuses and their sequenz on the dashboard's KPI
    status_count = df[status].value_counts().to_dict()

    statuses = app_config.invoice_status_dic

    invoices_paid = status_count.get(statuses["paid"], 0)
    invoices_open = status_count.get(statuses["open"], 0)
    invoices_overdue = status_count.get(statuses["overdue"], 0)    

    # Gruppieren auf neue Spalte "month" und summe monatlicher Umsätze sowie anzahl der rechnungen

    monthly_invoices=monthly_aggregation(df, invoice, "count")

    # normalized serie for processing by the plot_bar_chat
    monthly_series = [
                    build_series(
                                str(year),
                                app_config.month_names[app_config.language],
                                list(monthly_invoices[invoice]))
                    ]

    customer_invoices=(
        df.groupby(customer)
        .agg({invoice: "count"})
        .sort_values(by=invoice, ascending=False)
        .head(10)
    )

    customers = customer_invoices.index # Kunden holen

    # normalized serie for processing by the plot_bar_chat
    customer_series = [
                    build_series(
                                str(year),
                                customers,
                                list(customer_invoices[invoice]))
                    ]
    return{"total_invoices": total_invoices,
           "invoices_paid": invoices_paid,
           "invoices_open": invoices_open,
           "invoices_overdue": invoices_overdue,
           "monthly_series": monthly_series,
           "customer_series": customer_series
            }

# Dashboard for Development compared to previous year
def display_development(df,df_prev):    
    data = calculate_development(df,df_prev,st.session_state.year,st.session_state.year-1)

    st.title(f"Entwicklung {st.session_state.year} / {st.session_state.year-1}")
    st.caption("Analyse von Umsatz und Rechnungen")
    
    # KPI's
    cols = st.columns(2)

    cols[0].metric(
        label="Umsatzsteigerung",
        value=data['sales_increase']
        )  
    cols[1].metric(
        label="Anstieg der Bestellungen",
        value=data['invoices_increase']
        )      

    # charts
    fig_dev_sales = plot_bar_chart_px(data["monthly_sales_series"],
                                    app_config.chart_label["sales_for_month"],
                                    app_config.axis_lable["sales_for_month_axis"],                                    
                                    format_short,
                                    format_chf,
                                    monthly_chart)                                     
    
    fig_dev_invoices = plot_bar_chart_px(data["monthly_invoices_series"],
                                    app_config.chart_label["invoices_for_month"],
                                    app_config.axis_lable["invoices_for_month_axis"],                                          
                                    format_short,
                                    format_short,
                                    monthly_chart)                                        
    
    return(fig_dev_sales,fig_dev_invoices)

# calculate data for development chart
def calculate_development(df,df_prev,cur_year,prev_year):
    amount = app_config.dashboard_attributes.get("amount",None)
    customer = app_config.dashboard_attributes.get("customer",None)
    invoice = app_config.dashboard_attributes.get("invoice_nr",None)

    total_sales_cur=df[amount].sum()  # total sales in current year
    total_sales_prev=df_prev[amount].sum()  # total sales in previous year
    if total_sales_prev == 0:
        sales_increase = 0
    else:
        sales_increase=(total_sales_cur - total_sales_prev) / total_sales_prev # increase
    sales_increase_formatted=format_percentage(sales_increase)

    total_invoices_cur=df[invoice].count()  # total invoices in current year
    total_invoices_prev=df_prev[invoice].count()  # total invoices in previous year
    if total_invoices_prev == 0:
       invoices_increase = 0
    else: 
        invoices_increase = (total_invoices_cur - total_invoices_prev) / total_invoices_prev
    invoices_increase_formatted=format_percentage(invoices_increase)

    # Gruppieren auf neue Spalte "month" und summe monatlicher Umsätze sowie anzahl der rechnungen
    # get sales data for the current year
    monthly_sales_cur = monthly_aggregation(df, amount, "sum") 
    monthly_sales_prev=monthly_aggregation(df_prev, amount, "sum") 

    # normalized serie for processing by the plot_bar_chat
    monthly_sales_series = [
                    build_series(
                                str(cur_year),
                                app_config.month_names[app_config.language],
                                list(monthly_sales_cur[amount])
                    ),
                    build_series(
                                str(prev_year),
                                app_config.month_names[app_config.language],
                                list(monthly_sales_prev[amount])
                    ),                    
                    ]
    
    # Gruppieren auf neue Spalte "month" und summe monatlicher Umsätze sowie anzahl der rechnungen
    # get invoices data for the current year
    monthly_invoices_cur = monthly_aggregation(df, invoice, "count")
    monthly_invoices_prev=monthly_aggregation(df_prev, invoice, "count") 

    # normalized serie for processing by the plot_bar_chat
    monthly_invoices_series = [
                    build_series(
                                str(cur_year),
                                app_config.month_names[app_config.language],
                                list(monthly_invoices_cur[invoice])),
                     build_series(
                                str(prev_year),
                                app_config.month_names[app_config.language],
                                list(monthly_invoices_prev[invoice]))                                                 
                    ]
    
    return{"sales_increase": sales_increase_formatted,
           "invoices_increase": invoices_increase_formatted,
           "monthly_sales_series": monthly_sales_series,
           "monthly_invoices_series": monthly_invoices_series
            }

# ------------------------ Main routine ----------------------------------
# Existierende Jahren aus den Rechnungsdateien ermitteln
# ----------------------------------------------------------------------- 
if app_config.DEMO_MODE:
    demo_folder = Path(__file__).resolve().parents[1] / "demo_data"

    config = {
        "data_folder": str(demo_folder)
    }
else:
    config = load_config()

    if not config:
        st.title("Setup")

        folder = st.text_input("Bitte geben Sie den Datenordner an")

        submitted=st.button("Speichern")

        if not folder:
            st.stop()

        save_config(folder)
        st.rerun()

if config not in st.session_state:
    st.session_state["config"] = config  

# initialization
init_state()

if st.session_state.view == view_errors:
    st.session_state.initialized=False

# data_folder = get_data_folder()

# if "data_folder" not in st.session_state or st.session_state.data_folder == None:
#     st.session_state["data_folder"] = data_folder

files=os.listdir(st.session_state.data_folder)

years=set()  # ein set verhindert duplikate - falls dateien aus verschieden ordnern gelesene werden
match_mask=re.escape(app_config.file_name_format).replace('YYYY',r'(\d{4})')  # escape makes escapes: '.' to '\.'

for f in files: # geht alle dateien mit rechnungen durch und ermittelt jeweiliges jahr
    match = re.match(f"^{match_mask}$", f)
    if match:
        years.add(int(match.group(1)))
years=sorted(years,reverse=True)

if len(years)==0: # prüfet, ob die dateien mit rechnungen existieren
    st.write(f"Keine Dateien im Format {app_config.file_name_format}")
    st.stop()
# -------------------------------------------------------------------------

display_sidebar()

if not st.session_state.get("initialized", False) and st.session_state.get("view") != view_errors:
    show_year_selector(years)
elif st.session_state.get("view") == view_show:
    show_csv_file()
else:
    show_dashboard()         

# end main routine                