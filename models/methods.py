def rrule_reocurring():
    freq = input('''Enter frequency:
                    1. DAILY 
                    2. WEEKLY 
                    3. MONTHLY
                    4. YEARLY
                 ''')
    interval = input('Enter interval (e.g., every 2 weeks would be 2): ')
    if freq == '1':
        untill = input('Enter end date (YYYYMMDD): ')
        return f"FREQ=DAILY;INTERVAL={interval};UNTIL={untill}"
    if freq == '2':
        untill = input('Enter end date (YYYYMMDD): ')
        byDay = input('Enter days of the week (e.g., MO,TU,WE): ')
        return f"FREQ=WEEKLY;INTERVAL={interval};BYDAY={byDay};UNTIL={untill}"
    if freq == '3' or freq == '4':
        byDate_or_byDay = input('''Enter either BYMONTHDAY (e.g., 15) or BYDAY (e.g., 3FR for 3rd Friday): ''')
        if byDate_or_byDay.isdigit():
            untill = input('Enter end date (YYYYMMDD): ')
            return f"FREQ={'MONTHLY' if freq == '3' else 'YEARLY'};INTERVAL={interval};BYMONTHDAY={byDate_or_byDay};UNTIL={untill}"
        else:
            untill = input('Enter end date (YYYYMMDD): ')
            return f"FREQ={'MONTHLY' if freq == '3' else 'YEARLY'};INTERVAL={interval};BYDAY={byDate_or_byDay};UNTIL={untill}"

        
    '''
    Placeholder function for generating RRULE strings for recurring events.
    In a full implementation, this would take parameters via CLI input like frequency,
    interval, and end date to construct a valid RRULE string.
    '''
    # This is a simplified version - in a real implementation, these values would be passed as arguments
    # "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO"  # Example: every Monday
