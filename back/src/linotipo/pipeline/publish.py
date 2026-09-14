"""Etapa 6: valida la edición guardada y la hace pública a través del `Publisher`."""

from __future__ import annotations

from linotipo.domain.models import Edition
from linotipo.domain.ports import EditionRepository, Publisher
from linotipo.pipeline.workdir import WorkDir


def run_publish(work: WorkDir, repo: EditionRepository, publisher: Publisher) -> Edition:
    rendered = work.read("render", Edition)
    path = repo.save(rendered)
    # Relee desde disco: lo que se publica es exactamente lo que leerá el front.
    edition = repo.load(rendered.date)
    publisher.publish(edition, path)
    return edition
