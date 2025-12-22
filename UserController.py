#!/usr/bin/env python3
"""
Example UserController.py
This controller uses the UserModel and UserView to handle user operations.
"""

from UserModel import UserModel
from UserView import UserView


class UserController:
    """Controller for managing user interactions between model and view."""

    def __init__(self):
        """Initialize the controller with model and view instances."""
        self.model = UserModel()
        self.view = UserView()

    def create_user(self, name: str, email: str) -> None:
        """
        Create a new user.
        
        Args:
            name (str): The user's name.
            email (str): The user's email.
        """
        try:
            user = self.model.add_user(name, email)
            self.view.display_user_created(user)
        except ValueError as e:
            self.view.display_error(str(e))

    def get_user(self, user_id: int) -> None:
        """
        Retrieve and display a user by ID.
        
        Args:
            user_id (int): The ID of the user to retrieve.
        """
        user = self.model.get_user(user_id)
        if user:
            self.view.display_user(user)
        else:
            self.view.display_error(f"User with ID {user_id} not found.")

    def list_users(self) -> None:
        """List all users."""
        users = self.model.get_all_users()
        self.view.display_users_list(users)

    def update_user(self, user_id: int, name: str = None, email: str = None) -> None:
        """
        Update a user's information.
        
        Args:
            user_id (int): The ID of the user to update.
            name (str, optional): New name for the user.
            email (str, optional): New email for the user.
        """
        try:
            updated_user = self.model.update_user(user_id, name, email)
            if updated_user:
                self.view.display_user_updated(updated_user)
            else:
                self.view.display_error(f"User with ID {user_id} not found.")
        except ValueError as e:
            self.view.display_error(str(e))

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user by ID.
        
        Args:
            user_id (int): The ID of the user to delete.
        """
        deleted = self.model.delete_user(user_id)
        if deleted:
            self.view.display_user_deleted(user_id)
        else:
            self.view.display_error(f"User with ID {user_id} not found.")


if __name__ == "__main__":
    # Example usage of the controller
    controller = UserController()
    
    # Create users
    controller.create_user("Alice", "alice@example.com")
    controller.create_user("Bob", "bob@example.com")
    
    # List all users
    controller.list_users()
    
    # Get a specific user
    controller.get_user(1)
    
    # Update a user
    controller.update_user(1, name="Alice Smith")
    
    # Delete a user
    controller.delete_user(2)
    
    # List users after deletion
    controller.list_users()
