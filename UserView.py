class UserView:
    """
    Example view class for displaying user information.
    """

    def __init__(self, user_data):
        """
        Initialize the view with user data.
        
        Args:
            user_data (dict): A dictionary containing user information.
        """
        self.user_data = user_data

    def display(self):
        """
        Display the user information in a formatted way.
        """
        if not self.user_data:
            print("No user data available.")
            return

        print("User Information:")
        print("-" * 20)
        for key, value in self.user_data.items():
            print(f"{key.capitalize()}: {value}")
        print("-" * 20)


# Example usage
if __name__ == "__main__":
    # Sample user data
    sample_user = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "city": "New York"
    }
    
    # Create view instance and display
    view = UserView(sample_user)
    view.display()