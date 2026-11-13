import json
from pathlib import Path

import pytest

from rag.ingest import discover_files, load_file, normalize_blocks, source_ids_for

ROOT = Path(__file__).resolve().parent.parent

CSV = (
    "﻿Wydział,Kierunek,Ostateczny_prog_punktowy\n"
    "Wydział Elektryczny,Informatyka stosowana,170\n"
    'Wydział X,"Kierunek, z przecinkiem",Nikt nie został zakwalifikowany\n'
    ",,\n"
)


def _write(tmp_path, content, name="Tabela_test.csv"):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_load_csv_one_block_per_row_with_key_from_all_but_last_column(tmp_path):
    blocks = load_file(_write(tmp_path, CSV))
    assert len(blocks) == 2  # pusty wiersz pominięty, BOM nie psuje nagłówka
    assert source_ids_for(blocks[0].metadata) == ["Tabela_test.csv#Wydział Elektryczny,Informatyka stosowana"]
    assert "Kierunek: Informatyka stosowana" in blocks[0].text
    assert "Ostateczny prog punktowy: 170" in blocks[0].text  # „_” w nagłówku zamieniony na spację
    assert "Nikt nie został zakwalifikowany" in blocks[1].text
    assert source_ids_for(blocks[1].metadata) == ["Tabela_test.csv#Wydział X,Kierunek, z przecinkiem"]


def test_load_csv_does_not_depend_on_column_names(tmp_path):
    blocks = load_file(_write(tmp_path, "Imię,Miasto,Wiek\nAnna,Płock,30\nJan,Warszawa,41\n"))
    assert [source_ids_for(b.metadata)[0] for b in blocks] == ["Tabela_test.csv#Anna,Płock", "Tabela_test.csv#Jan,Warszawa"]
    assert "Imię: Anna. Miasto: Płock. Wiek: 30." in blocks[0].text


@pytest.mark.parametrize("content, key", [("Nazwa;Liczba\nA;1\n", "A"), ("Nazwa\tLiczba\nA\t1\n", "A"), ("Nazwa,Liczba\nA,1\n", "A")])
def test_load_csv_detects_delimiter_and_two_columns_give_single_key(tmp_path, content, key):
    (block,) = load_file(_write(tmp_path, content))
    assert source_ids_for(block.metadata) == [f"Tabela_test.csv#{key}"]
    assert "Liczba: 1" in block.text


def test_load_csv_single_column_uses_its_value_as_key(tmp_path):
    (block,) = load_file(_write(tmp_path, "Fakt\nWisła płynie przez Warszawę\n"))
    assert source_ids_for(block.metadata) == ["Tabela_test.csv#Wisła płynie przez Warszawę"]


def test_csv_text_survives_normalization(tmp_path):
    blocks = load_file(_write(tmp_path, CSV))
    assert [b.text for b in normalize_blocks(blocks)] == [b.text for b in blocks]


def test_csv_is_discovered_in_directory(tmp_path):
    _write(tmp_path, CSV, "a.csv")
    assert [p.name for p in discover_files([tmp_path])] == ["a.csv"]


@pytest.mark.parametrize(
    "content, message",
    [
        ("", "brak nagłówka"),
        ("A,B,C\n1,2\n", "kolumn zamiast"),
        ("A,B,C\nx,y,1\nx,y,2\n", "powtórzony identyfikator"),
    ],
)
def test_csv_errors_say_what_is_wrong(tmp_path, content, message):
    with pytest.raises(ValueError, match=message):
        load_file(_write(tmp_path, content))


def test_every_csv_source_id_from_golden_sets_matches_a_row():
    """Regresja: identyfikatory `plik.csv#...` w eval/*.jsonl muszą wskazywać istniejące wiersze."""
    csv_files = list((ROOT / "data" / "raw").glob("*.csv"))
    available = {sid for f in csv_files for b in load_file(f) for sid in source_ids_for(b.metadata)}
    wanted = {
        sid
        for golden in (ROOT / "eval").glob("golden_*.jsonl")
        for line in golden.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for sid in json.loads(line)["source_ids"]
        if ".csv" in sid
    }
    assert wanted - available == set()
