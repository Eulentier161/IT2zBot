from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from util.util import Utils


class Database:
    def __init__(self) -> None:
        self.engine = create_engine(
            f"sqlite+pysqlite:///{Path(Utils.get_project_root(), 'sqlite.db').resolve()}",
            echo=True,
        )
        meta = MetaData(self.engine)
        self.tasks_table = Table(
            "tasks",
            meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("msg_id", String, unique=True, nullable=True),
            Column("title", String),
            Column("details", String),
        )
        meta.create_all()

    def create_tasks_entry(self, msg_id: int, title: str, details: str):
        with self.engine.connect() as conn:
            conn.execute(self.tasks_table.insert().values(msg_id=msg_id, title=title, details=details))

    def mark_task_deleted(self, msg_id: str):
        with self.engine.connect() as conn:
            conn.execute(self.tasks_table.update().where(self.tasks_table.c.msg_id == msg_id).values(msg_id=None))

    def get_active_task(self, msg_id: str) -> dict:
        with self.engine.connect() as conn:
            res = conn.execute(self.tasks_table.select().where(self.tasks_table.c.msg_id == msg_id))
            return res.first()._mapping

    def update_task(self, msg_id: str, title: str = None, details: str = None):
        values = {}
        if title:
            values["title"] = title
        if details:
            values["details"] = details
        if not values:
            return

        with self.engine.connect() as conn:
            conn.execute(self.tasks_table.update().where(self.tasks_table.c.msg_id == msg_id).values(**values))
