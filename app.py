# ... (Keep your imports and UI setup as is)

if uploaded_file and st.button("Generate Schedule"):
    # 1. Read the data
    df = pd.read_excel(uploaded_file)
    
    # Check if 'Equipment' column exists
    if 'Equipment' not in df.columns:
        st.error("Please ensure your Excel file has a column named 'Equipment'")
    else:
        # 2. THE SECRET: Sort by Equipment
        # This keeps the team focused on one equipment at a time
        df = df.sort_values(by=['Equipment', 'MH']) 
        
        hourly_cap = daily_cap / 8.0
        usage_tracker = {}
        
        # ... (Your usage_tracker function remains the same)
        
        # 3. Process the tasks
        # (Your loop stays mostly the same, but now it processes the sorted df)
        # ...
        
        # Output the results
        st.success("Smoothing complete! Tasks grouped by Equipment.")
        # ... (Download code remains same)
