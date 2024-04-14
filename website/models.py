from . import db
import json

class User:
    __user_id = None
    __username: str
    __email: str
    __phone_number: str
    __password: str
    __address: dict
    __user_type: str

    def __init__(self, username: str, email: str, phone_number: str, user_type: str):
        self.__username = username
        self.__email = email
        self.__phone_number = phone_number
        self.__user_type = user_type

    def get_username(self) -> str:
        return self.__username
    
    def set_username(self, username: str):
        self.__username = username

    def get_email(self) -> str:
        return self.__email
    
    def set_email(self, email: str):
        self.__email = email

    def get_phone_number(self) -> str:
        return self.__phone_number
    
    def set_phone_number(self, phone_number: str):
        self.__phone_number = phone_number

    def check_password(self, password: str) -> bool:
        return self.__password == db.make_password(password)
    
    def set_password(self, password: str):
        self.__password = db.make_password(password)

    def get_address(self) -> dict:
        return self.__address
    
    def set_address(self, country: str, city: str, area: str):
        self.__address = {'country': country, 'city': city, 'area': area}

    def get_user_type(self) -> str:
        return self.__user_type
    
    def set_user_type(self, user_type: str):
        self.__user_type = user_type

    def get_id(self) -> int:
        return self.__user_id
    
    def __set_id(self, id: int):
        self.__user_id = id

    @staticmethod
    def get_user_by_email(email: str) -> "User":
        my_db = db.get_db()
        cursor = my_db.cursor()
        
        cursor.execute(f"""
            SELECT * FROM user WHERE email = "{email}"
        """)

        result = cursor.fetchone()

        user = None

        if result:
            user = User(result[1], result[2], result[3], result[6])
            user.__password = result[4]
            user.__user_id = result[0]
            user.__address = result[5]

        cursor.close()
        return user
    
    def to_json(self) -> dict:
        return {
            'user_id': self.__user_id,
            'username': self.__username,
            'user_type': self.__user_type
        }
    
    def __str__(self):
        return f"User: {self.__username}"
    
    def save(self):
        mydb = db.get_db()
        cursor = mydb.cursor()
        if self.__user_id is not None:  # update
            cursor.execute(f"SELECT COUNT(user_id) FROM user WHERE email='{self.__email}'")
            if cursor.fetchone()[0] > 0:
                raise User.EmailAlreadyExists(f"{self.__email} already exists in the database")
            cursor.execute(f"SELECT COUNT(user_id) FROM user WHERE phone_number='{self.__phone_number}'")
            if cursor.fetchone()[0] > 0:
                raise User.PhoneNumberAlreadyExists(f"{self.__phone_number} already exists in the database")
            
            cursor.execute(f"""
                UPDATE user SET
                username = "{self.__username}",
                email = "{self.__email}",
                phone_number = "{self.__phone_number}",
                password = "{self.__password}",
                address = '{json.dumps(self.__address)}',
                user_type = "{self.__user_type}"
                WHERE user_id = {self.__user_id}
            """)
        else:
            
            cursor.execute(f"SELECT COUNT(user_id) FROM user WHERE email='{self.__email}'")
            if cursor.fetchone()[0] > 0:
                raise User.EmailAlreadyExists(f"{self.__email} already exists in the database")
            cursor.execute(f"SELECT COUNT(user_id) FROM user WHERE phone_number='{self.__phone_number}'")
            if cursor.fetchone()[0] > 0:
                raise User.PhoneNumberAlreadyExists(f"{self.__phone_number} already exists in the database")
            cursor.execute(f"""
                INSERT INTO user (user_id, username, email, phone_number, address, password, user_type)
                VALUES (NULL, "{self.__username}", "{self.__email}", "{self.__phone_number}", '{json.dumps(self.__address)}', "{self.__password}", "{self.__user_type}");
            """)

            cursor.execute(f"SELECT user_id FROM user WHERE email='{self.__email}' OR phone_number='{self.__phone_number}'")
            self.__user_id = cursor.fetchone()[0]

        mydb.commit()
        cursor.close()
    
    class EmailAlreadyExists(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class PhoneNumberAlreadyExists(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
