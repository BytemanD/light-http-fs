
class AuthManager(object):

    def __init__(self, password):
        self.admin_password = password

    def is_valid(self, username, password):
        return username == 'admin' and password == self.admin_password
