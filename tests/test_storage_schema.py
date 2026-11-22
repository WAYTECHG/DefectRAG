from backend.storage import SQLiteRepository


def test_schema_is_created_once_per_file(tmp_path, monkeypatch):
    calls = []
    original = SQLiteRepository._create_schema

    def counting(self):
        calls.append(self.path)
        original(self)

    monkeypatch.setattr(SQLiteRepository, "_create_schema", counting)
    path = tmp_path / "inspection.sqlite3"
    SQLiteRepository(path)
    repo = SQLiteRepository(path)
    assert len(calls) == 1
    assert repo.stats()["total"] == 0


def test_schema_is_recreated_when_the_file_was_removed(tmp_path):
    path = tmp_path / "inspection.sqlite3"
    SQLiteRepository(path)
    for leftover in tmp_path.iterdir():
        leftover.unlink()
    assert SQLiteRepository(path).stats()["total"] == 0
