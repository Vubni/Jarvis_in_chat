
def get_month_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} месяц"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return f"{count} месяца"
    else:
        return f"{count} месяцев"