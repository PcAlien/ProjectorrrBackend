def sortme(madto):
    month, year = madto.monat.split(".")
    return (int(year), int(month))