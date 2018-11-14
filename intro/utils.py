def get_subscription_key(filename):
    with open(filename, 'r') as file:
        key = file.read()
        return key
