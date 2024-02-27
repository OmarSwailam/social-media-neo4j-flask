# social-media-neo4j-flask
## Project Overview

This Flask application with Neo4j and `neomodel` serves as a foundation for building social media web applications. It includes user registration and login, user following/unfollowing, post creation, editing, and deletion, all backed by the power of the Neo4j graph database and the ease of `neomodel` ORM.
The application provides swagger docs for easy testing.
## Features

- User registration and login with JWT (JSON Web Tokens) for authentication.
- User following and unfollowing functionality.
- Post creation, editing, and deletion.
- Retrieving a list of all users and posts.
- Retrieving specific user and post details.

## Installation
## Using Docker
  make sure you have docker and docker compose installed on your machine
  1. Clone this repository to your local machine.
    ```
    git clone https://github.com/OmarSwailam/social-media-neo4j-flask.git
    ```
  2. Navigate to the project directory.
  3. Build and Run the application
     ```
      docker-compose up --build
     ```
  4. Testing the application
    ```
      Navigate to http://localhost:5000
      Register a new user and copy the <access token></access>
      in the top right above the available endpoints click the authorize button and type
      Bearer <access token>
    ```
## Normal installation
  1. Clone this repository to your local machine.
    ```
    git clone https://github.com/OmarSwailam/social-media-neo4j-flask.git
    ```
  2. Navigate to the project directory.
  3. Create a virtual environment (optional but recommended).
    ```
    python -m venv venv
    ```
  4. Activate the virtual environment
    ```
    venv/scripts/activate  # On Windows
    ```

  5. Install the required dependencies.
    ```
    pip install -r requirements.txt
    ```

  6. Run neo4j container using doker, or install it and run it locally
    [neo4j download and install docs](https://neo4j.com/docs/desktop-manual/current/installation/download-installation/)
    [neo4j docker image](https://hub.docker.com/_/neo4j)

  7. Run the python application
    ```
    python run.py
    ```
  8. Testing the application
    ```
      Navigate to http://localhost:5000
      Register a new user and copy the <access token></access>
      in the top right above the available endpoints click the authorize button and type
      Bearer <access token>
    ```
## Configuration

Feel free to edit the config.py file.

## Endpoints
The application provides swagger docs for easy testing.
The application provides the following endpoints:

- **User Registration**: `/users/register` (POST)
- **User Login**: `/users/login` (POST)
- **Get a List of All Users**: `/users/` (GET)
- **Get Specific User Details**: `/users/<user_id>` (GET)
- **Follow a User**: `/users/<user_id>/follow` (POST)
- **Unfollow a User**: `/users/<user_id>/follow` (DELETE)
- **Get Followers or Following of a User**: `/users/<user_id>/<action>` (GET)
- **Get a List of All Posts**: `/posts/` (GET)
- **Create a New Post**: `/posts/` (POST)
- **Get a Specific Post**: `/posts/<post_uuid>` (GET)
- **Edit a Specific Post**: `/posts/<post_uuid>` (PUT)
- **Delete a Specific Post**: `/posts/<post_uuid>` (DELETE)

## Contributing

Contributions are welcome! You can contribute to the project by:

- Reporting issues or suggesting improvements.
- Forking the repository and submitting pull requests.
