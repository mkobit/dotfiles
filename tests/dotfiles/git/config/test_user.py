from src.dotfiles.git.config.user import User


def test_user_init():
    """Test user initialization with different parameters"""
    email = 'test@example.com'
    user_name = 'testuser'
    signing_key = 'testkey'
    use_config_only = True
    user = User(email=email, user_name=user_name, signing_key=signing_key, use_config_only=use_config_only)
    
    assert user.email == email
    assert user.user_name == user_name
    assert user.signing_key == signing_key
    assert user.use_config_only == use_config_only
