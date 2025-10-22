# vulnerable_app.py - CodeQL 테스트를 위한 취약한 코드
    import sqlite3

    def get_user_data(username):
        db = sqlite3.connect('example.db')
        cursor = db.cursor()
        # **취약점:** 입력(username)을 직접 SQL 쿼리에 삽입
        query = "SELECT * FROM users WHERE username = '" + username + "'"
        cursor.execute(query)
        data = cursor.fetchall()
        db.close()
        return data

    # 공격자가 ' OR 1=1 --' 같은 값을 입력할 수 있습니다.
    get_user_data("test_user") 
