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
  1. Clone this repository to your local machine.
    ```
    git clone https://github.com/OmarSwailam/social-media-neo4j-flask.git
    ```
  2. Navigate to the project directory.
  3. Run the application
     ```
      docker-compose up --build
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

## Configuration

Before running the application, you should configure the Neo4j database connection and other settings.

## Usage

To run the Flask application, execute the following command:
  ```
  python run.py
  ```

Your application will be accessible at `http://localhost:5000`.

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
