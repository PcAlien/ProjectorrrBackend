class BookingSummary:
    restDays2PspEnd: int
    workloadHoursPerDay: int
    project: str
    restTurnover: float
    employeeId: int
    pspEndDate: str
    turnover2PspEnd: float
    finalBudgetEndDate: str
    hourlyRate: int
    psp: int

    def __init__(self, restDays2PspEnd: int, workloadHoursPerDay: int, project: str, restTurnover: float, employeeId: int, pspEndDate: str, turnover2PspEnd: float, finalBudgetEndDate: str, hourlyRate: int, psp: int) -> None:
        self.restDays2PspEnd = restDays2PspEnd
        self.workloadHoursPerDay = workloadHoursPerDay
        self.project = project
        self.restTurnover = restTurnover
        self.employeeId = employeeId
        self.pspEndDate = pspEndDate
        self.turnover2PspEnd = turnover2PspEnd
        self.finalBudgetEndDate = finalBudgetEndDate
        self.hourlyRate = hourlyRate
        self.psp = psp


class EmployeeSummaryElement:
    name: str
    bookingSummaries: [BookingSummary]
    workloadSum: int
    turnoverSum: float
    id: int

    def __init__(self, name: str, bookingSummaries: [BookingSummary], workloadSum: int, turnoverSum: float, id: int) -> None:
        self.name = name
        self.bookingSummaries = bookingSummaries
        self.workloadSum = workloadSum
        self.turnoverSum = turnoverSum
        self.id = id


class EmployeeSummary:
    employeeSummary: [EmployeeSummaryElement]

    def __init__(self, employeeSummary: [EmployeeSummaryElement]) -> None:
        self.employeeSummary = employeeSummary
