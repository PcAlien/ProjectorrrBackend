from src.projector_backend.dto.booking_dto import BookingDTO


class EditedItem:

    employee_name: str
    psp_element: str

    text_changed: bool
    stunden_changed: bool
    datum_changed: bool
    berechnungsmotiv_changed: bool
    bugdet_diff: float

    old_text: str
    new_text: str
    old_datum: str
    new_datum: str
    old_stunden: float
    new_stunden: float
    new_bm: float
    old_bm: float

    def __init__(self, employee_name, psp_element, text_changed, stunden_changed, datum_changed, berechnungsmotiv_changed, bugdet_diff, old_text, new_text,
                 old_datum, new_datum, old_stunden, new_stunden,old_bm, new_bm) -> None:

        self.employee_name = employee_name
        self.psp_element = psp_element

        self.text_changed = text_changed
        self.stunden_changed = stunden_changed
        self.datum_changed = datum_changed
        self.berechnungsmotiv_changed = berechnungsmotiv_changed
        self.bugdet_diff = bugdet_diff

        self.old_text = old_text
        self.new_text = new_text
        self.old_datum = old_datum
        self.new_datum = new_datum
        self.old_stunden = old_stunden
        self.new_stunden = new_stunden
        self.old_bm = old_bm
        self.new_bm = new_bm


class HistResult:
    datum: str
    deleted_items : [BookingDTO] = []
    edited_items : [EditedItem] = []
    new_items : [BookingDTO] = []

    umsatz_deleted: float
    umsatz_edited:float
    umsatz_new:float

    def __init__(self, datum, deleted_items, edited_items, new_items) -> None:
        self.datum = datum
        self.deleted_items = deleted_items
        self.edited_items = edited_items
        self.new_items = new_items
        self.umsatz_edited = 0
        self.umsatz_new = 0
        self.umsatz_deleted =0
        self.umsatz_change = 0

        item:BookingDTO
        for item in self.deleted_items:
            self.umsatz_deleted -= item.umsatz

        for item in self.new_items:
            self.umsatz_new += item.umsatz

        eitem: EditedItem
        for eitem in edited_items:
            self.umsatz_edited += eitem.bugdet_diff

        self.umsatz_change = self.umsatz_deleted + self.umsatz_edited + self.umsatz_new

