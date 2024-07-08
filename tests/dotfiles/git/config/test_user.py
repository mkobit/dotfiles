import src.dotfiles.git.config as c


email = 'test@example.com'
user_name = 'testuser'
signing_key = 'testkey'


def test_user_init():
    """Test user initialization"""
    use_config_only = True
    user = c.User(email=email, user_name=user_name, signing_key=signing_key, use_config_only=use_config_only)

    assert user.email == email
    assert user.user_name == user_name
    assert user.signing_key == signing_key
    assert user.use_config_only == use_config_only


def test_dumps_user():
    """Test user dumps with different parameters"""
    use_config_only = True
    user = c.User(email=email, user_name=user_name, signing_key=signing_key, use_config_only=use_config_only)

    assert user.header() == '[user]'
    file_options = user.file_options()
    assert file_options.get('email') == email
    assert file_options.get('name') == user_name
    assert file_options.get('signingKey') == signing_key
    assert file_options.get('useConfigOnly') == use_config_only
