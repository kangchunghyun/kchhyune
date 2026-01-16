from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ARRAY
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from contextlib import contextmanager
from sqlalchemy import Column, String, DateTime, func
import csv
import ast
import json
import re

class Database:
    def __init__(self, host, user, password, db_name="postgres", port=54321):
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        self.engine = create_engine(self.connection_string, echo=False, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """필요할 때마다 새 세션을 생성하여 반환"""
        return self.Session()
    
    @contextmanager
    def session_scope(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def test_connection(self):
        """연결 테스트용 간단한 쿼리 실행"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            print(f"[DB ERROR] 연결 실패: {e}")
            return False
        
    def flatten(self, value):
        if isinstance(value, list):
            return [item for sublist in value for item in (sublist if isinstance(sublist, list) else [sublist])]
        return value
    
    def normalize_2d_array(self, arr):
        if not isinstance(arr, list):
            return []
        try:
            max_len = max(len(inner) for inner in arr if isinstance(inner, list))
            return [inner + [''] * (max_len - len(inner)) for inner in arr]
        except Exception:
            return []

    def parse_pg_array(self, text):
        """
        PostgreSQL 형식 배열 문자열 (ex: {{A},{B}}) → [['A'], ['B']]
        """
        if not isinstance(text, str) or not text.startswith('{{'):
            return []
        try:
            inner = text.strip('{}')
            matches = re.findall(r'\{(.*?)\}', inner)
            return [[item.strip()] for item in matches if item.strip()]
        except Exception as e:
            print(f"[parse_pg_array 오류] {text} → {e}")
            return []


    def upsert_unified_data(self, srcdata, batch_size=1000):
        array_fields = {
            'cdrcategory', 'cdraction', 'cdrcontent', 'cdrmode',
            'events', 'severity', 'slename', 'sleversion',
            'shortmsgko', 'shortmsgen', 'longmsgko', 'longmsgen'
        }

        json_fields = {'cdrpolicy', 'cdrpolicydetail'}
        int_fields = {'filesize', 'cdrtime', 'set0time', 'set1time'}

        data = []

        with open(srcdata, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            if reader.fieldnames:
                reader.fieldnames = [name.lstrip('\ufeff') for name in reader.fieldnames]
                print(f"[DEBUG] fieldnames → {reader.fieldnames}")

            for row in reader:
                # JSON 필드 처리
                for key in json_fields:
                    val = row.get(key)
                    if not val or val.strip() == "":
                        row[key] = None
                    else:
                        try:
                            row[key] = json.dumps(json.loads(val), ensure_ascii=False)
                        except Exception as e:
                            print(f"[JSON 변환 실패] {key} → {val} ({e})")
                            row[key] = None

                # 정수형 필드 처리
                for key in int_fields:
                    if key in row:
                        try:
                            row[key] = int(row[key]) if row[key].strip() != "" else None
                        except Exception as e:
                            print(f"[INT 변환 실패] {key} → {row[key]} ({e})")
                            row[key] = None

                # 배열 필드 처리 (반드시 독립 루프에서!)
                for key in array_fields:
                    if key in row and row[key]:
                        row[key] = self.parse_pg_array(row[key])
                        print(f"[DEBUG] {key} 변환 결과 → {row[key]}")

                data.append(row)

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            stmt = insert(UnifiedTable).values(batch)
            update_stmt = stmt.on_conflict_do_update(
                index_elements=["sha256"],
                set_={
                    c.name: getattr(stmt.excluded, c.name)
                    for c in UnifiedTable.__table__.columns
                    if c.name not in ("sha256", "createdtime", "lastmodifytime")
                }
            )

            try:
                with self.session_scope() as session:
                    session.execute(update_stmt)
                    print(f"[UPSERT] {len(batch)}건 upsert 완료.")
            except SQLAlchemyError as e:
                print(f"[DB ERROR] UPSERT 실패: {e}")
                raise

Base = declarative_base()

class UnifiedTable(Base):
    __tablename__ = 'unified_table'
    
    sha256 = Column(String, primary_key=True)
    cdrversion = Column(String)
    slepversion = Column(String)
    originalfilename = Column(String)
    filename = Column(String)
    path = Column(String)
    filesize = Column(Integer)
    mimetype = Column(String)
    extension = Column(String)
    tag = Column(ARRAY(String))
    createdtime = Column(DateTime, server_default=func.now(), nullable=False)
    lastmodifytime = Column(DateTime, server_default=func.now())
    cdrtime = Column(Integer)
    cdrdetectedfiletype = Column(String)
    cdrresult = Column(String)
    cdrstatus = Column(String)
    cdrdetailmessage = Column(Text)
    cdrpolicy = Column(String)
    cdrpolicydetail = Column(String)
    #cdr_createdtime = Column(TIMESTAMP)
    cdrcategory = Column(ARRAY(String))
    cdraction = Column(ARRAY(String))
    cdrcontent = Column(ARRAY(String))
    cdrmode = Column(ARRAY(String))
    summaryresult = Column(String)
    summaryexploitname = Column(String)
    set0time = Column(Integer)
    set1time = Column(Integer)
    #analysis_createdtime = Column(TIMESTAMP)
    events = Column(ARRAY(String))
    severity = Column(ARRAY(String))
    slename = Column(ARRAY(String))
    sleversion = Column(ARRAY(String))
    shortmsgko = Column(ARRAY(String))
    shortmsgen = Column(ARRAY(String))
    longmsgko = Column(ARRAY(String))
    longmsgen = Column(ARRAY(String))