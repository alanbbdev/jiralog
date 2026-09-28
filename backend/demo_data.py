from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


PEOPLE = [
    ("Marina Costa", "MC"),
    ("Rafael Lima", "RL"),
    ("Ana Souza", "AS"),
    ("Bruno Melo", "BM"),
]
ISSUES = [
    ("PLAT-142", "Aprimorar fluxo de checkout", "Plataforma", "#2563eb"),
    ("MKT-88", "Landing page da campanha", "Marketing", "#f97316"),
    ("OPS-317", "Automatizar alertas de estoque", "Operacoes", "#14b8a6"),
    ("PLAT-156", "Revisar permissoes de acesso", "Plataforma", "#2563eb"),
    ("DATA-61", "Painel de conversao semanal", "Dados", "#eab308"),
]


def dashboard_data(start_date: date, end_date: date) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    current = start_date
    index = 0
    while current <= end_date:
        if current.weekday() < 5:
            for offset in range(3):
                issue = ISSUES[(index + offset) % len(ISSUES)]
                person = PEOPLE[(index + offset * 2) % len(PEOPLE)]
                hours = [1.5, 2.25, 3.0, 1.25, 2.75][(index + offset) % 5]
                entries.append(
                    {
                        "id": f"demo-{index}-{offset}",
                        "issueKey": issue[0],
                        "summary": issue[1],
                        "project": issue[2],
                        "projectColor": issue[3],
                        "author": person[0],
                        "initials": person[1],
                        "date": current.isoformat(),
                        "seconds": int(hours * 3600),
                        "hours": hours,
                        "comment": ["Implementacao", "Revisao e testes", "Alinhamento tecnico"][offset],
                    }
                )
            index += 1
        current += timedelta(days=1)
    return {"entries": entries, "generatedAt": datetime.now().isoformat()}