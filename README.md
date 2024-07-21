## Software Security - Secure Coding Practices for Session Management

1. The application doesn't provide any way to reset the list or end the session.
   You could implement this by removing the session key from the sessions table and any likes from the likes table. Implement an option "Forget Me" as a `POST` request to the `URL /forget` and include a button in your page template to trigger this.
2. Extend the example above to support authenticated sessions by requiring a username and password to be submitted before generating the session.
3. Implement the logout functionality that removes a session from the session table.   
