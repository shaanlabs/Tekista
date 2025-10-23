from models import db, User


def test_register_login_logout_flow(client, app):
    # Register
    resp = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'Newpass123!',
        'confirm': 'Newpass123!'
    }, follow_redirects=True)
    assert resp.status_code == 200

    # Login failure
    resp = client.post('/login', data={'username': 'newuser', 'password': 'wrong'}, follow_redirects=False)
    assert resp.status_code == 200  # stays on login page due to flash

    # Login success
    resp = client.post('/login', data={'username': 'newuser', 'password': 'Newpass123!'}, follow_redirects=False)
    assert resp.status_code in (302, 303)

    # Logout
    resp = client.get('/logout', follow_redirects=False)
    assert resp.status_code in (302, 303)
