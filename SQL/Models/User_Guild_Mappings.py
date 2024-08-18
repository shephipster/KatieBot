from .Entity import Entity
import SQL.Connection

class User_Guild_Mappings(Entity):
    
    def __init__(self):
        super().__init__("User_Guild_Mappings")
        
    def createTable(self):
        connection = SQL.Connection.connection.cursor()
        table = \
        """
        CREATE TABLE IF NOT EXISTS
        User_Guild_Mappings(
            id integer PRIMARY KEY,
            user_id integer NOT NULL,
            guild_id integer NOT NULL,
            next_ping TIMESTAMP NOT NULL DEFAULT 0,
            ping_delay integer NOT NULL DEFAULT 120,
            FOREIGN KEY (user_id)
                REFERENCES Users (user_id)
                    ON DELETE CASCADE,
            FOREIGN KEY (guild_id)
                References Guilds (guild_id)
                    ON DELETE CASCADE                   
        );
        """
        try:
            connection.execute(table)
        except Exception as e:
            print(e)
            
    def fetchAvailableUsers(self, guild, current_time):
        connection = SQL.Connection.connection.cursor()
        query = f'SELECT * from User_Guild_Mappings where next_ping <= ? AND guild_id = ?'
        params = (
            current_time,
            guild
        )
        results = connection.execute(query, params)
        return results
    
    def updatePingedUsers(self, users:list, guild):
        from datetime import datetime as dt
        from datetime import timedelta
        next_time = dt.now() + timedelta(seconds=120)
        connection = SQL.Connection.connection.cursor()
        placeholders = ", ".join(["?"] * len(users))
        query = f'''
            UPDATE User_Guild_Mappings
            SET next_ping = ?
            WHERE user_id IN ({placeholders})
            AND guild_id = ?
        '''
        params = (
            next_time,
            *users,
            guild
        )
        connection.execute(query, params)    
        
    def convertFromRow(self, values: list):
        return super().convertFromRow(values)
    
    def addRow(self, **kwargs):
        connection = SQL.Connection.connection.cursor()

        if self.getByPKey(None, user_id = kwargs['user_id'], guild_id = kwargs['guild_id']):
            return
        else:
            query = \
            """
            INSERT INTO User_Guild_Mappings (user_id, guild_id, next_ping, ping_delay) VALUES (?,?,?,?)
            """
            params = (
                kwargs['user_id'],
                kwargs['guild_id'],
                0,
                120          
            )
            connection.execute(query, params)
            return super().addRow(**kwargs)
    
    def getByPKey(self, pkey, **kwargs):
        try:
            connection = SQL.Connection.connection.cursor()
            guid = kwargs['guild_id']
            uid = kwargs['user_id']
            query = f'SELECT * from User_Guild_Mappings where guild_id = ? AND user_id = ?'
            params = (guid, uid)
            fetched_data = connection.execute(query, params).fetchall()
            return fetched_data
        except:
            return None
    
    def search(self, **kwargs):
        pass

    def set(self, pkey, **kwargs):
        pass