import pytest
from app.admin.auth import (
    verify_superadmin_credentials,
    create_session_token,
    verify_session_token,
    get_password_hash,
    verify_password,
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing utilities."""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestSuperadminAuth:
    """Test superadmin authentication."""
    
    def test_verify_correct_credentials(self):
        """Test verification with correct env credentials."""
        result = verify_superadmin_credentials(
            settings.ADMIN_USERNAME,
            settings.ADMIN_PASSWORD
        )
        assert result is True
    
    def test_verify_incorrect_username(self):
        """Test verification with incorrect username."""
        result = verify_superadmin_credentials(
            "wrong_user",
            settings.ADMIN_PASSWORD
        )
        assert result is False
    
    def test_verify_incorrect_password(self):
        """Test verification with incorrect password."""
        result = verify_superadmin_credentials(
            settings.ADMIN_USERNAME,
            "wrong_password"
        )
        assert result is False


class TestSessionTokens:
    """Test session token creation and verification."""
    
    def test_create_and_verify_token(self):
        """Test creating and verifying a valid token."""
        username = "test_admin"
        role = "superadmin"
        
        token = create_session_token(username, role)
        assert token is not None
        assert isinstance(token, str)
        
        payload = verify_session_token(token)
        assert payload is not None
        assert payload["username"] == username
        assert payload["role"] == role
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.string"
        payload = verify_session_token(invalid_token)
        assert payload is None
    
    def test_verify_empty_token(self):
        """Test verifying an empty token."""
        payload = verify_session_token("")
        assert payload is None
