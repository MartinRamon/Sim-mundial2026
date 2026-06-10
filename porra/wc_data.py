"""Datos reales de la Copa del Mundo de Futbol 2026 (Canada, Mexico y EE. UU.).

Grupos y cuadro de eliminatorias segun el sorteo final de la FIFA.
"""

# code -> (nombre en castellano, iso para bandera, emoji)
TEAMS = {
    # Grupo A
    "MEX": ("Mexico", "mx", "\U0001F1F2\U0001F1FD"),
    "RSA": ("Sudafrica", "za", "\U0001F1FF\U0001F1E6"),
    "KOR": ("Corea del Sur", "kr", "\U0001F1F0\U0001F1F7"),
    "CZE": ("Chequia", "cz", "\U0001F1E8\U0001F1FF"),
    # Grupo B
    "CAN": ("Canada", "ca", "\U0001F1E8\U0001F1E6"),
    "BIH": ("Bosnia y Herzeg.", "ba", "\U0001F1E7\U0001F1E6"),
    "QAT": ("Catar", "qa", "\U0001F1F6\U0001F1E6"),
    "SUI": ("Suiza", "ch", "\U0001F1E8\U0001F1ED"),
    # Grupo C
    "BRA": ("Brasil", "br", "\U0001F1E7\U0001F1F7"),
    "MAR": ("Marruecos", "ma", "\U0001F1F2\U0001F1E6"),
    "HAI": ("Haiti", "ht", "\U0001F1ED\U0001F1F9"),
    "SCO": ("Escocia", "gb-sct", "\U0001F3F4"),
    # Grupo D
    "USA": ("Estados Unidos", "us", "\U0001F1FA\U0001F1F8"),
    "PAR": ("Paraguay", "py", "\U0001F1F5\U0001F1FE"),
    "AUS": ("Australia", "au", "\U0001F1E6\U0001F1FA"),
    "TUR": ("Turquia", "tr", "\U0001F1F9\U0001F1F7"),
    # Grupo E
    "GER": ("Alemania", "de", "\U0001F1E9\U0001F1EA"),
    "CUW": ("Curazao", "cw", "\U0001F1E8\U0001F1FC"),
    "CIV": ("Costa de Marfil", "ci", "\U0001F1E8\U0001F1EE"),
    "ECU": ("Ecuador", "ec", "\U0001F1EA\U0001F1E8"),
    # Grupo F
    "NED": ("Paises Bajos", "nl", "\U0001F1F3\U0001F1F1"),
    "JPN": ("Japon", "jp", "\U0001F1EF\U0001F1F5"),
    "SWE": ("Suecia", "se", "\U0001F1F8\U0001F1EA"),
    "TUN": ("Tunez", "tn", "\U0001F1F9\U0001F1F3"),
    # Grupo G
    "BEL": ("Belgica", "be", "\U0001F1E7\U0001F1EA"),
    "EGY": ("Egipto", "eg", "\U0001F1EA\U0001F1EC"),
    "IRN": ("Iran", "ir", "\U0001F1EE\U0001F1F7"),
    "NZL": ("Nueva Zelanda", "nz", "\U0001F1F3\U0001F1FF"),
    # Grupo H
    "ESP": ("Espana", "es", "\U0001F1EA\U0001F1F8"),
    "CPV": ("Cabo Verde", "cv", "\U0001F1E8\U0001F1FB"),
    "KSA": ("Arabia Saudi", "sa", "\U0001F1F8\U0001F1E6"),
    "URU": ("Uruguay", "uy", "\U0001F1FA\U0001F1FE"),
    # Grupo I
    "FRA": ("Francia", "fr", "\U0001F1EB\U0001F1F7"),
    "SEN": ("Senegal", "sn", "\U0001F1F8\U0001F1F3"),
    "IRQ": ("Irak", "iq", "\U0001F1EE\U0001F1F6"),
    "NOR": ("Noruega", "no", "\U0001F1F3\U0001F1F4"),
    # Grupo J
    "ARG": ("Argentina", "ar", "\U0001F1E6\U0001F1F7"),
    "ALG": ("Argelia", "dz", "\U0001F1E9\U0001F1FF"),
    "AUT": ("Austria", "at", "\U0001F1E6\U0001F1F9"),
    "JOR": ("Jordania", "jo", "\U0001F1EF\U0001F1F4"),
    # Grupo K
    "POR": ("Portugal", "pt", "\U0001F1F5\U0001F1F9"),
    "COD": ("RD Congo", "cd", "\U0001F1E8\U0001F1E9"),
    "UZB": ("Uzbekistan", "uz", "\U0001F1FA\U0001F1FF"),
    "COL": ("Colombia", "co", "\U0001F1E8\U0001F1F4"),
    # Grupo L
    "ENG": ("Inglaterra", "gb-eng", "\U0001F3F4"),
    "CRO": ("Croacia", "hr", "\U0001F1ED\U0001F1F7"),
    "GHA": ("Ghana", "gh", "\U0001F1EC\U0001F1ED"),
    "PAN": ("Panama", "pa", "\U0001F1F5\U0001F1E6"),
}

# Seleccion "patriotica": penalizacion si se predice su eliminacion antes de tiempo.
HOME_TEAM = "ESP"

GROUPS = {
    "A": ["MEX", "RSA", "KOR", "CZE"],
    "B": ["CAN", "BIH", "QAT", "SUI"],
    "C": ["BRA", "MAR", "HAI", "SCO"],
    "D": ["USA", "PAR", "AUS", "TUR"],
    "E": ["GER", "CUW", "CIV", "ECU"],
    "F": ["NED", "JPN", "SWE", "TUN"],
    "G": ["BEL", "EGY", "IRN", "NZL"],
    "H": ["ESP", "CPV", "KSA", "URU"],
    "I": ["FRA", "SEN", "IRQ", "NOR"],
    "J": ["ARG", "ALG", "AUT", "JOR"],
    "K": ["POR", "COD", "UZB", "COL"],
    "L": ["ENG", "CRO", "GHA", "PAN"],
}

GROUP_LETTERS = list(GROUPS.keys())

# Grupo en el que esta Espana: es el unico que apuestan los participantes.
SPAIN_GROUP = next(l for l, ts in GROUPS.items() if HOME_TEAM in ts)


def team_name(code):
    t = TEAMS.get(code)
    return t[0] if t else "Por definir"


def _build_group_matches():
    """Genera los 6 partidos round-robin de cada grupo (72 en total)."""
    schedule = [
        [(0, 1), (2, 3)],  # Jornada 1
        [(0, 2), (3, 1)],  # Jornada 2
        [(3, 0), (1, 2)],  # Jornada 3
    ]
    matches = []
    for letter in GROUP_LETTERS:
        teams = GROUPS[letter]
        n = 1
        for d_idx, day in enumerate(schedule):
            for h, a in day:
                matches.append(
                    {
                        "id": "%s%d" % (letter, n),
                        "group": letter,
                        "matchday": d_idx + 1,
                        "home": teams[h],
                        "away": teams[a],
                    }
                )
                n += 1
    return matches


GROUP_MATCHES = _build_group_matches()
GROUP_MATCH_IDS = {m["id"] for m in GROUP_MATCHES}

# ----- Eliminatorias -----

ROUND_LABELS = {
    "R32": "Dieciseisavos",
    "R16": "Octavos",
    "QF": "Cuartos",
    "SF": "Semifinales",
    "TP": "Tercer puesto",
    "F": "Final",
}

# Indice de ronda para la clausula de Espana (cuanto mas alto, mas lejos llega).
# Grupos=0, R32=1, R16=2, QF=3, SF=4, perder Final=5, Campeon=6
ELIM_ROUND_INDEX = {"R32": 1, "R16": 2, "QF": 3, "SF": 4, "TP": 4, "F": 5}

ROUND_ORDER = ["R32", "R16", "QF", "SF", "TP", "F"]

# Las 8 posiciones que reciben un tercero (clave Annex C -> numero de partido R32)
THIRD_SLOT_TO_MATCH = {
    "1A": 79,
    "1B": 85,
    "1D": 81,
    "1E": 74,
    "1G": 82,
    "1I": 77,
    "1K": 87,
    "1L": 80,
}


def _g(group, rank):
    return {"type": "group", "group": group, "rank": rank}


def _third(slot):
    return {"type": "third", "slot": slot}


def _w(match):
    return {"type": "winner", "match": match}


def _l(match):
    return {"type": "loser", "match": match}


KNOCKOUT_MATCHES = [
    # Dieciseisavos (R32)
    {"match": 73, "round": "R32", "home": _g("A", 2), "away": _g("B", 2)},
    {"match": 74, "round": "R32", "home": _g("E", 1), "away": _third("1E")},
    {"match": 75, "round": "R32", "home": _g("F", 1), "away": _g("C", 2)},
    {"match": 76, "round": "R32", "home": _g("C", 1), "away": _g("F", 2)},
    {"match": 77, "round": "R32", "home": _g("I", 1), "away": _third("1I")},
    {"match": 78, "round": "R32", "home": _g("E", 2), "away": _g("I", 2)},
    {"match": 79, "round": "R32", "home": _g("A", 1), "away": _third("1A")},
    {"match": 80, "round": "R32", "home": _g("L", 1), "away": _third("1L")},
    {"match": 81, "round": "R32", "home": _g("D", 1), "away": _third("1D")},
    {"match": 82, "round": "R32", "home": _g("G", 1), "away": _third("1G")},
    {"match": 83, "round": "R32", "home": _g("K", 2), "away": _g("L", 2)},
    {"match": 84, "round": "R32", "home": _g("H", 1), "away": _g("J", 2)},
    {"match": 85, "round": "R32", "home": _g("B", 1), "away": _third("1B")},
    {"match": 86, "round": "R32", "home": _g("J", 1), "away": _g("H", 2)},
    {"match": 87, "round": "R32", "home": _g("K", 1), "away": _third("1K")},
    {"match": 88, "round": "R32", "home": _g("D", 2), "away": _g("G", 2)},
    # Octavos (R16)
    {"match": 89, "round": "R16", "home": _w(73), "away": _w(75)},
    {"match": 90, "round": "R16", "home": _w(74), "away": _w(77)},
    {"match": 91, "round": "R16", "home": _w(76), "away": _w(78)},
    {"match": 92, "round": "R16", "home": _w(79), "away": _w(80)},
    {"match": 93, "round": "R16", "home": _w(83), "away": _w(84)},
    {"match": 94, "round": "R16", "home": _w(81), "away": _w(82)},
    {"match": 95, "round": "R16", "home": _w(86), "away": _w(88)},
    {"match": 96, "round": "R16", "home": _w(85), "away": _w(87)},
    # Cuartos (QF)
    {"match": 97, "round": "QF", "home": _w(89), "away": _w(90)},
    {"match": 98, "round": "QF", "home": _w(93), "away": _w(94)},
    {"match": 99, "round": "QF", "home": _w(91), "away": _w(92)},
    {"match": 100, "round": "QF", "home": _w(95), "away": _w(96)},
    # Semifinales (SF)
    {"match": 101, "round": "SF", "home": _w(97), "away": _w(98)},
    {"match": 102, "round": "SF", "home": _w(99), "away": _w(100)},
    # Tercer puesto
    {"match": 103, "round": "TP", "home": _l(101), "away": _l(102)},
    # Final
    {"match": 104, "round": "F", "home": _w(101), "away": _w(102)},
]

KNOCKOUT_BY_MATCH = {m["match"]: m for m in KNOCKOUT_MATCHES}
KNOCKOUT_MATCH_IDS = {str(m["match"]) for m in KNOCKOUT_MATCHES}

FINAL_MATCH = 104
THIRD_PLACE_MATCH = 103

# ----- Premios individuales (Pichichi y MVP) -----
# Candidatos para el desplegable (agrupados por seleccion). El usuario tambien
# puede escribir "otro" jugador a mano (texto libre). El admin fija el Pichichi
# y el MVP reales al final del torneo.
STAR_PLAYERS = [
    ("Kai Havertz", "GER"), ("Antonio Rudiger", "GER"), ("Jamal Musiala", "GER"), ("Florian Wirtz", "GER"), ("Nick Woltemade", "GER"),
    ("Salem Al-Dawsari", "KSA"), ("Firas Al-Buraikan", "KSA"), ("Mohammed Kanno", "KSA"), ("Saud Abdulhamid", "KSA"), ("Nawaf Al-Aqidi", "KSA"),
    ("Riyad Mahrez", "ALG"), ("Amine Gouiri", "ALG"), ("Mohamed Amine Amoura", "ALG"), ("Ramy Bensebaini", "ALG"), ("Ismael Bennacer", "ALG"),
    ("Lionel Messi", "ARG"), ("Nico Paz", "ARG"), ("Alexis Mac Allister", "ARG"), ("Lautaro Martinez", "ARG"), ("Julian Alvarez", "ARG"),
    ("Mathew Ryan", "AUS"), ("Harry Souttar", "AUS"), ("Jackson Irvine", "AUS"), ("Craig Goodwin", "AUS"), ("Riley McGree", "AUS"),
    ("David Alaba", "AUT"), ("Marcel Sabitzer", "AUT"), ("Konrad Laimer", "AUT"), ("Christoph Baumgartner", "AUT"), ("Marko Arnautovic", "AUT"),
    ("Kevin De Bruyne", "BEL"), ("Jeremy Doku", "BEL"), ("Romelu Lukaku", "BEL"), ("Leandro Trossard", "BEL"), ("Amadou Onana", "BEL"),
    ("Edin Dzeko", "BIH"), ("Ermedin Demirovic", "BIH"), ("Amar Dedic", "BIH"), ("Rade Krunic", "BIH"), ("Anel Ahmedhodzic", "BIH"),
    ("Vinicius Junior", "BRA"), ("Rodrygo", "BRA"), ("Endrick", "BRA"), ("Marquinhos", "BRA"), ("Raphinha", "BRA"),
    ("Garry Rodrigues", "CPV"), ("Logan Costa", "CPV"), ("Jovane Cabral", "CPV"), ("Willy Semedo", "CPV"), ("Jamiro Monteiro", "CPV"),
    ("Alphonso Davies", "CAN"), ("Jonathan David", "CAN"), ("Stephen Eustaquio", "CAN"), ("Tajon Buchanan", "CAN"), ("Maxime Crepeau", "CAN"),
    ("Son Heung-min", "KOR"), ("Kim Min-jae", "KOR"), ("Lee Kang-in", "KOR"), ("Hwang Hee-chan", "KOR"), ("Hwang In-beom", "KOR"),
    ("Seko Fofana", "CIV"), ("Franck Kessie", "CIV"), ("Sebastien Haller", "CIV"), ("Simon Adingra", "CIV"), ("Odilon Kossounou", "CIV"),
    ("Leandro Bacuna", "CUW"), ("Juninho Bacuna", "CUW"), ("Jurien Gaari", "CUW"), ("Kenji Gorre", "CUW"), ("Eloy Room", "CUW"),
    ("Moises Caicedo", "ECU"), ("Piero Hincapie", "ECU"), ("Enner Valencia", "ECU"), ("Kendry Paez", "ECU"), ("Pervis Estupinan", "ECU"),
    ("Mohamed Salah", "EGY"), ("Omar Marmoush", "EGY"), ("Mostafa Mohamed", "EGY"), ("Mahmoud Trezeguet", "EGY"), ("Mohamed Elneny", "EGY"),
    ("Andrew Robertson", "SCO"), ("Scott McTominay", "SCO"), ("John McGinn", "SCO"), ("Kieran Tierney", "SCO"), ("Che Adams", "SCO"),
    ("Rodri Hernandez", "ESP"), ("Lamine Yamal", "ESP"), ("Nico Williams", "ESP"), ("Pedri", "ESP"), ("Ferran Torres", "ESP"),
    ("Christian Pulisic", "USA"), ("Weston McKennie", "USA"), ("Folarin Balogun", "USA"), ("Tyler Adams", "USA"), ("Antonee Robinson", "USA"),
    ("Kylian Mbappe", "FRA"), ("Olise", "FRA"), ("William Saliba", "FRA"), ("Ousmane Dembele", "FRA"), ("Desire Doue", "FRA"),
    ("Frantzdy Pierrot", "HAI"), ("Duckens Nazon", "HAI"), ("Derrick Etienne", "HAI"), ("Danley Jean Jacques", "HAI"), ("Johny Placide", "HAI"),
    ("Jude Bellingham", "ENG"), ("Harry Kane", "ENG"), ("Anthony Gordon", "ENG"), ("Bukayo Saka", "ENG"), ("Declan Rice", "ENG"),
    ("Mehdi Taremi", "IRN"), ("Sardar Azmoun", "IRN"), ("Alireza Jahanbakhsh", "IRN"), ("Saman Ghoddos", "IRN"), ("Ramin Rezaeian", "IRN"),
    ("Aymen Hussein", "IRQ"), ("Ali Jasim", "IRQ"), ("Amir Al-Ammari", "IRQ"), ("Zidane Iqbal", "IRQ"), ("Jalal Hassan", "IRQ"),
    ("Takefusa Kubo", "JPN"), ("Kaoru Mitoma", "JPN"), ("Wataru Endo", "JPN"), ("Takehiro Tomiyasu", "JPN"), ("Ritsu Doan", "JPN"),
    ("Musa Al-Taamari", "JOR"), ("Yazan Al-Naimat", "JOR"), ("Ali Olwan", "JOR"), ("Yazan Al-Arab", "JOR"), ("Noor Al-Rawabdeh", "JOR"),
    ("Achraf Hakimi", "MAR"), ("Brahim Diaz", "MAR"), ("Hakim Ziyech", "MAR"), ("Abde Ezzalzouli", "MAR"), ("Sofyan Amrabat", "MAR"),
    ("Santiago Gimenez", "MEX"), ("Edson Alvarez", "MEX"), ("Guillermo Ochoa", "MEX"), ("Johan Vasquez", "MEX"), ("Julian Quinones", "MEX"),
    ("Erling Haaland", "NOR"), ("Martin Odegaard", "NOR"), ("Alexander Sorloth", "NOR"), ("Sander Berge", "NOR"), ("Antonio Nusa", "NOR"),
    ("Chris Wood", "NZL"), ("Liberato Cacace", "NZL"), ("Marko Stamenic", "NZL"), ("Sarpreet Singh", "NZL"), ("Joe Bell", "NZL"),
    ("Virgil van Dijk", "NED"), ("Frenkie de Jong", "NED"), ("Cody Gakpo", "NED"), ("Xavi Simons", "NED"), ("Matthijs de Ligt", "NED"),
    ("Miguel Almiron", "PAR"), ("Julio Enciso", "PAR"), ("Ramon Sosa", "PAR"), ("Mathias Villasanti", "PAR"), ("Omar Alderete", "PAR"),
    ("Cristiano Ronaldo", "POR"), ("Bruno Fernandes", "POR"), ("Bernardo Silva", "POR"), ("Joao Neves", "POR"), ("Vitinha", "POR"),
    ("Akram Afif", "QAT"), ("Almoez Ali", "QAT"), ("Hassan Al-Haydos", "QAT"), ("Meshaal Barsham", "QAT"), ("Boualem Khoukhi", "QAT"),
    ("Patrik Schick", "CZE"), ("Tomas Soucek", "CZE"), ("Vladimir Coufal", "CZE"), ("Adam Hlozek", "CZE"), ("Ladislav Krejci", "CZE"),
    ("Sadio Mane", "SEN"), ("Kalidou Koulibaly", "SEN"), ("Pape Matar Sarr", "SEN"), ("Edouard Mendy", "SEN"), ("Ismaila Sarr", "SEN"),
    ("Ronwen Williams", "RSA"), ("Themba Zwane", "RSA"), ("Teboho Mokoena", "RSA"), ("Lyle Foster", "RSA"), ("Percy Tau", "RSA"),
    ("Alexander Isak", "SWE"), ("Viktor Gyokeres", "SWE"), ("Dejan Kulusevski", "SWE"), ("Anthony Elanga", "SWE"), ("Victor Lindelof", "SWE"),
    ("Granit Xhaka", "SUI"), ("Manuel Akanji", "SUI"), ("Yann Sommer", "SUI"), ("Xherdan Shaqiri", "SUI"), ("Breel Embolo", "SUI"),
    ("Ellyes Skhiri", "TUN"), ("Aissa Laidouni", "TUN"), ("Elias Achouri", "TUN"), ("Montassar Talbi", "TUN"), ("Youssef Msakni", "TUN"),
    ("Hakan Calhanoglu", "TUR"), ("Arda Guler", "TUR"), ("Orkun Kokcu", "TUR"), ("Kenan Yildiz", "TUR"), ("Ferdi Kadioglu", "TUR"),
    ("Federico Valverde", "URU"), ("Darwin Nunez", "URU"), ("Ronald Araujo", "URU"), ("Manuel Ugarte", "URU"), ("Jose Maria Gimenez", "URU"),
]

STAR_PLAYERS_BY_NAME = {name: team for name, team in STAR_PLAYERS}
