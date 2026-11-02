from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class SqlAlchemyDatabaseHealthChecker:
    def __init__(self, session: Session) -> None:
        self._session = session

    def is_available(self) -> bool:
        try:
            self._session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
