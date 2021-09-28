def format_csv_entry(e):
    return str(e or "").replace(",", " ").replace("\n", " ").replace("\t", " ")
