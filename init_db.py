import sqlite3

def setup_database():
    # 데이터베이스 파일명 (app.py와 동일하게 맞춰주세요)
    conn = sqlite3.connect('drive.db')
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 설문조사 (
        사고유형 TEXT,
        총점 INTEGER,
        점수비중 FLOAT
    )
    ''')

    # 데이터 삽입 (이미 있다면 중복 삽입 방지)
    cursor.execute("SELECT COUNT(*) FROM 설문조사")
    if cursor.fetchone()[0] == 0:
        data = [
            ('낙상사고', 399, 26.6), ('범죄사고', 383, 25.5), ('교통사고', 213, 14.2),
            ('실종사고', 172, 11.5), ('식품 및 위생사고', 124, 8.3), ('재난사고', 112, 7.5), ('약물·중독사고', 97, 6.5)
        ]
        cursor.executemany("INSERT INTO 설문조사 VALUES (?,?,?)", data)
        conn.commit()
        print("데이터베이스 초기화 완료!")
    else:
        print("이미 데이터가 존재합니다.")

    conn.close()

if __name__ == "__main__":
    setup_database()
