import streamlit as st
import pandas as pd
import app_config 

def validate(df):
    #overall_ok=True

    # all columns are available?
    overall_ok,df = check_col(df)

    if overall_ok:
        # iteration over all fields and validate them if necessary
        for field,check_type in app_config.required_cols.items():
            if check_type == "date":
                check_ok,df = check_date(df,field)
                overall_ok = overall_ok and check_ok
            elif check_type == "numeric":
                check_ok,df = check_numeric(df,field)
                overall_ok = overall_ok and check_ok
            elif check_type == "status":
                check_ok,df = check_status(df,field)
                overall_ok = overall_ok and check_ok
            else:
                pass

    if overall_ok:
        for field,check_type in app_config.required_cols.items():
            if check_type == "date":
                df[field] = pd.to_datetime(df[field])        
    
    return overall_ok, df

# New message will be added
def add_error_message(
                    level,               # error/warning/info
                    error_type,
                    field,
                    message=None,
                    value=None,
                    row=None):
    
    if error_type not in app_config.validation_errors:
        raise ValueError(f"Unbekannter error_type: {error_type}"
                        f"Erlaubt: {list(app_config.validation_errors.keys())}")
    
    if level not in st.session_state.messages:
        raise ValueError(f"Unbekannter level: {level}")

    if message is None:
        message = app_config.validation_errors[error_type]

    st.session_state.messages[level].append(
        {
        "error_type": error_type,
        "field": field,
        "message": message,
        "value": value,
        "row": row
        })  

# ----------------------Vorhandensein der Spalten prüfen --------------------------
def check_col(df):
    missing_cols = []

    for col in app_config.required_cols.keys():
        if col not in df.columns:
            missing_cols.append(col)    

    if missing_cols:
        error_type="missing_column"
        for i,row in enumerate(df.itertuples()):

            for col in missing_cols:
                add_error_message(
                    "error",                                          # message level
                    error_type,                                       # error type
                    col,                                              # field/column
                    app_config.validation_errors[error_type].format(column=col), 
                    None,                                             # value
                    i                                                 # row
                )            
        return False,df
    else:
        return True,df

# ----------------------Datum prüfen ----------------------------------------------
def check_date(df,field):
    # copy of original column date
    date_original = df[field].copy()

    # normalization: replace "-" with "."
    df[field]=df[field].astype(str).str.replace(".", "-") 

    # are the dates with day first?
    mask_day_first = df[field].astype(str).str.match("^.{2}[-]")

    if mask_day_first.any():
        df.loc[mask_day_first, field] = (
            pd.to_datetime(
                df.loc[mask_day_first, field], 
                format="%d-%m-%Y", 
                errors="coerce")
            .dt.strftime("%Y-%m-%d")
        )
    
    # final parsing
    df["date_parsed"]=pd.to_datetime(df[field],errors="coerce")

    # invalid values
    invalid_dates=df["date_parsed"].isna()

    del df["date_parsed"] 
    
    # error saving
    if invalid_dates.any():
        # in case of invalid date its value will be displayed
        # in case of missing date blank will be displayed
        df_invalid_date = df.loc[invalid_dates].copy()
        #df_invalid_date
        df_invalid_date[field] = date_original[invalid_dates]      

        #error_type="date_invalid"

        for idx,row in df_invalid_date.iterrows():

            if pd.isna(row[field]):
                error_type = "missing_value"
            else:
                error_type="date_invalid"            

            add_error_message(
                "error",                                    # error level
                error_type,                                 # error type
                field,                                      # field
                None,                                       # message
                row[field],                                 # value
                idx                                         # row number
            )         
        ok=False
    else:
        ok=True
        #df[field] = pd.to_datetime(df[field])         

    return ok,df

# ------------------------check for numeric values ----------------------
def check_numeric(df,field):
    numeric_ok = pd.to_numeric(df[field], errors="coerce").notna()

    if not numeric_ok.all():

        for idx,row in df[~numeric_ok].iterrows():        

            if pd.isna(row[field]):
                error_type = "missing_value"
            else:
                error_type="non_numeric"

            add_error_message(
                "error",                                    # error level
                error_type,                                 # error type
                field,                                      # field
                None,                                       # message will be from definition
                row[field],                                 # value
                idx                                         # row number
                )         
        ok=False
    else:
        ok=True
        df[field]=pd.to_numeric(df[field])

    return ok,df

# ------------------------ check status --------------------------------
def check_status(df,field):
    df[field] = df[field].astype(str).str.lower().str.strip()

    # invalid_status contains entries with missing and also invalid statuses
    invalid_status = ~df[field].isin(app_config.invoice_status)

    df_errors = df.loc[invalid_status].copy()

    # in case of invalid status its value will be displayed
    # in case of missing status blank will be displayed
    df_errors[field] = df_errors[field].replace("nan","")
    # df_errors[field] = df_errors[field].where(
    #     df_errors[field].notna(), ""
    # )

    # error saving
    if invalid_status.any():

        for idx,row in df_errors.iterrows():     
            if row[field] == "":
                error_type = "missing_value"
            else:
                error_type="status_invalid"

            add_error_message(
                "error",                                    # error level
                error_type,                                 # error type
                field,                                      # field
                None,                                       # message
                row[field],                              # value
                idx                                         # row number
                )                  
        ok=False
    else:
        ok=True

    return ok,df