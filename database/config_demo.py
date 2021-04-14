def sqlite(path='database.sqlite'):
    '''
    Argument:
        - path: str, in-memory is ':memory:'
    '''
    return f'sqlite:///{path}'

def postgresql(username, password, hostport, database):
    return f'postgresql://{username}:{password}@{hostport}/{database}'


database_url = sqlite()
