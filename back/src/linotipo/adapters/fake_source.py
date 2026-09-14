"""Fuente de noticias determinista, sin red. Para desarrollo, tests y la edición de ejemplo."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from linotipo.domain.models import Source, source_id_from_url

# (outlet, título, path). Los títulos comparten palabras a propósito para que
# la etapa `cluster` agrupe algunos.
_FIXTURES: list[tuple[str, str, str]] = [
    (
        "El País",
        "El Gobierno aprueba la reforma de la ley de vivienda",
        "politica/reforma-vivienda",
    ),
    (
        "RTVE",
        "El Consejo de Ministros aprueba la reforma de la ley de vivienda",
        "noticias/reforma-vivienda-consejo",
    ),
    (
        "elDiario.es",
        "Claves de la reforma de la ley de vivienda aprobada por el Gobierno",
        "politica/claves-vivienda",
    ),
    (
        "El Mundo",
        "El Banco de España mejora la previsión de crecimiento al 2,4%",
        "economia/banco-espana-prevision",
    ),
    (
        "Expansión",
        "El Banco de España eleva su previsión de crecimiento para este año",
        "economia/prevision-crecimiento",
    ),
    (
        "El País",
        "La Comisión Europea propone un nuevo paquete de sanciones",
        "internacional/comision-sanciones",
    ),
    ("RTVE", "Bruselas plantea un nuevo paquete de sanciones", "noticias/bruselas-sanciones"),
    (
        "20minutos",
        "La ola de calor deja temperaturas récord en el valle del Guadalquivir",
        "sociedad/ola-calor-guadalquivir",
    ),
    (
        "El País",
        "Récord de temperaturas por la ola de calor en Andalucía",
        "clima/record-ola-calor",
    ),
    (
        "El Mundo",
        "El Real Madrid gana en el último minuto y lidera la clasificación",
        "deportes/real-madrid-lider",
    ),
    ("Marca", "El Real Madrid gana en el descuento y se pone líder", "futbol/madrid-lider"),
    ("elDiario.es", "El Prado inaugura una gran retrospectiva de Sorolla", "cultura/prado-sorolla"),
    (
        "RTVE",
        "El Museo del Prado abre la retrospectiva de Sorolla",
        "noticias/prado-retrospectiva-sorolla",
    ),
    (
        "El País",
        "El CSIC descubre una nueva especie de anfibio en los Pirineos",
        "ciencia/csic-anfibio-pirineos",
    ),
    (
        "20minutos",
        "Investigadores del CSIC hallan una nueva especie de anfibio",
        "ciencia/csic-nueva-especie",
    ),
    (
        "Expansión",
        "El Ibex 35 cierra en máximos anuales impulsado por la banca",
        "mercados/ibex-maximos",
    ),
    (
        "El Mundo",
        "La huelga de transporte afecta a los principales puertos",
        "espana/huelga-transporte-puertos",
    ),
    (
        "elDiario.es",
        "Sanidad amplía el calendario de vacunación infantil",
        "sociedad/calendario-vacunacion",
    ),
]


class FakeNewsSource:
    def __init__(self, edition_date: date | None = None) -> None:
        self.edition_date = edition_date or datetime.now(tz=UTC).date()

    def fetch(self) -> list[Source]:
        base = datetime.combine(self.edition_date, time(6, 0), tzinfo=UTC)
        sources: list[Source] = []
        for index, (outlet, title, path) in enumerate(_FIXTURES):
            url = f"https://example.org/{outlet.lower().replace(' ', '-').replace('.', '')}/{path}"
            sources.append(
                Source(
                    id=source_id_from_url(url),
                    outlet=outlet,
                    title=title,
                    url=url,  # type: ignore[arg-type]
                    published_at=base - timedelta(minutes=17 * index),
                )
            )
        return sources
