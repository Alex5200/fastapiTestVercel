from User import Users


def test_user_model():
    user = Users(username="john_doe", email="")
    assert user.username == "john_doe"
    assert user.email == "alex"
    assert user.role == "user"
