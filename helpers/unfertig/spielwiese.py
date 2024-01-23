import json

from dto.abwesenheiten import AbwesenheitDTO, AbwesenheitDetailsDTO
from helpers import data_helper

abds: [AbwesenheitDetailsDTO] = []
abds.append(AbwesenheitDetailsDTO("31.12.2023", "u"))
abds.append(AbwesenheitDetailsDTO("31.12.2023", "a"))
abds.append(AbwesenheitDetailsDTO("31.12.2023", "x"))

abw: AbwesenheitDTO = AbwesenheitDTO("meinName", "123", "Tester", abds)

jsonstting = json.dumps(abw,default=data_helper.serialize)
print(jsonstting)