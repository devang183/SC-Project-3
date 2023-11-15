# rbac.py
#-----Sambit----------------
# Dummy user data
users = {
    'admin': {
        'password': 'admin_password',
        'roles': ['admin']
    },
    'user': {
        'password': 'user_password',
        'roles': ['user']
    }
}

def is_admin(username):
    # Check if the user has the 'admin' role
    return 'admin' in users.get(username, {}).get('roles', [])
