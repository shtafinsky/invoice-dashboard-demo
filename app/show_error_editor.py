def edit_error(df,year):

    import streamlit as st
    from datetime import datetime as dtt
    import pandas as pd
    # application imports    
    import app_config
    from pathlib import Path

    errors = st.session_state.messages["error"]

    error_rows={e["row"] for e in errors}

    row_msg_map = {}

    for e in errors:
        row = e["row"]
        msg = f'{e["field"]}: {e["message"]}'

        if row not in row_msg_map:
            row_msg_map[row] = [msg]
        else:
            row_msg_map[row].append(msg)

    df_errors = df.loc[df.index.isin(error_rows)].copy()

    df_errors = df_errors.replace("nan","")

    df_errors["error"] = df_errors.index.map(
        lambda i: " / ".join(row_msg_map[i]))

    st.markdown("### ❌ Fehlerhafte Daten")

    edited_df = st.data_editor(df_errors,hide_index=True)

    if st.button("Korrektur übernehmen"):
        df_merged = df.copy()

        edited_df = edited_df.drop(columns=["error"], errors="ignore")
        #del edited_df["error"]

        df_merged.update(edited_df)        

        cur_tmestamp=dtt.now().strftime("%Y-%m-%d_%H.%M.%S")

        # backup of the original csv

        file_path_base = st.session_state.data_folder
        file_path_bak = (
            f"{file_path_base}/"
            f"{app_config.file_name_format.replace('YYYY', f'{year}_bak_{cur_tmestamp}')}"
            )

        df.to_csv(f"{file_path_bak}", index=False, sep=";",encoding="utf-8")

        # save corrected file
        #file_path = f"{file_path_base}/{app_config.file_name_format.replace("YYYY",f'{year}')}"
        file_name = app_config.file_name_format.replace("YYYY",f'{year}')

        file_path = Path(file_path_base)/file_name
     
        df_merged.to_csv(f"{file_path}", index=False, sep=";",encoding="utf-8")

        st.success("Datei wurde aktualisiert")