class UserModel:
    """A simple example model class representing a user."""

    def __init__(self, user_id: int, username: str, email: str):
        """Initialize a new UserModel instance.
        
        Args:
            user_id (int): Unique identifier for the user.
            username (str): The user's username.
            email (str): The user's email address.
        """
        self.user_id = user_id
        self.username = username
        self.email = email

    def to_dict(self) -> dict:
        """Convert the user model to a dictionary.
        
        Returns:
            dict: A dictionary representation of the user.
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserModel':
        """Create a UserModel instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing user data.
        
        Returns:
            UserModel: A new UserModel instance.
        """
        return cls(
            user_id=data.get('user_id'),
            username=data.get('username'),
            email=data.get('email')
        )

    def __repr__(self) -> str:
        """Return a string representation of the UserModel."""
        return f"UserModel(user_id={self.user_id}, username='{self.username}', email='{self.email}')"
