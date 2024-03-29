from .Entity import Entity
import SQL.Connection

class User_Likes(Entity):
    
    def __init__(self):
        super().__init__("User_Likes")
        
    def createTable(self):
        connection = SQL.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        User_Likes(
            id integer PRIMARY KEY AUTOINCREMENT,
            user_id integer NOT NULL,
            guild_id integer NOT NULL,
            tag text NOT NULL,
            count integer NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES Users (user_id)  
                    ON DELETE CASCADE,
            FOREIGN KEY (guild_id)
                REFERENCES Guilds (guild_id)
                    ON DELETE CASCADE   
        );
        """
        try:
            connection.execute(table)
        except Exception as e:
            print(e)
    
        
    def convertFromRow(self, values: list):
        return super().convertFromRow(values)
    
    def addRow(self, **kwargs):
        connection = SQL.Connection.connection.cursor()

        if self.getByPKey(None, tag = kwargs['tag'], user_id = kwargs['user_id'], guild_id = kwargs['guild_id']):
            return
        else:
            query = \
            """
            INSERT INTO User_Likes (user_id, guild_id, tag, count) VALUES (?,?,?,?)
            """
            params = (
                kwargs['user_id'],
                kwargs['guild_id'],
                kwargs['tag'],
                0         
            )

        connection.execute(query, params)
        
    def deleteRow(self, **kwargs):
        try:
            connection = SQL.Connection.connection.cursor()
            guid = kwargs['guild_id']
            uid = kwargs['user_id']
            tag = kwargs['tag']
            query = f'DELETE from User_Likes where guild_id = ? AND user_id = ? AND tag = ?'
            params = (guid, uid, tag)
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return None
        
    def search(self, **kwargs):
        try:
            connection = SQL.Connection.connection.cursor()
            params = ()
            query = f'SELECT * from User_Likes where '
            if 'user_id' in kwargs:
                query = query + "user_id = ?"
                params = params + (kwargs['user_id'],)
            if 'guild_id' in kwargs:
                if len(params) != 0:
                    query = query + " AND "
                query = query + "guild_id = ?"
                params = params + (kwargs['guild_id'],)
            if 'tag' in kwargs:
                if len(params) != 0:
                    query = query + " AND "
                query = query + "tag= ?"
                params = params + (kwargs['tag'],)
                
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return                 
    
    def getByPKey(self, pkey, **kwargs):
        try:
            connection = SQL.Connection.connection.cursor()
            guid = kwargs['guild_id']
            uid = kwargs['user_id']
            tag = kwargs['tag']
            query = f'SELECT * from User_Likes where guild_id = ? AND user_id = ? AND tag = ?'
            params = (guid, uid, tag)
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return None

    def set(self, pkey, **kwargs):
        pass