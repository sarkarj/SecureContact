# ContactClient Flask App

The **ContactClient Flask App** is a secure web application built with Flask, designed for managing user data including name, email, phone, preferred time to connect, and admin-level features such as OTP verification and note addition. This application uses encryption, CAPTCHA validation, and phone verification to ensure security.

## Features

- **User Management:** Allows users to submit their details including name, email, phone, and preferred time to connect.
- **Admin Authentication:** Admin users are required to complete OTP verification before accessing and managing user data.
- **Data Encryption:** Sensitive information such as name, email, and phone numbers are encrypted using the Fernet encryption scheme.
- **Phone Validation:** Users' phone numbers are validated via the NumVerify API to ensure correctness.
- **CAPTCHA Protection:** A CAPTCHA is generated to prevent automated submissions.
- **Rate Limiting:** Limits the number of requests to prevent abuse and ensure smooth user experience.

## Installation

### Dockerized Installation

To set up this application in a Docker container, follow these steps:

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/contact-client-flask.git
    cd contact-client-flask
    ```

2. **Set Up Environment Variables:**

   - Create a `.env` file at the root of the repository with the following variables:

    ```plaintext
    SECRET_KEY=your_secret_key
    FLASK_ENV=production
    FERNET_KEY=your_fernet_key
    NUMVERIFY_API_KEY=your_numverify_api_key
    DB_NAME=your_db_name.db
    TOTP_SECRET=your_totp_secret
    RATELIMIT_STORAGE_URL=your_ratelimit_storage_url
    ```

3. **Build and Run the Docker Container:**

    Make sure Docker and Docker Compose are installed. Then, run the following command:

    ```bash
    docker-compose up --build
    ```

    This will build the Docker image and start the application in a container. The application will be available at `http://localhost:8080`.

### Manual Installation

1. **Install Dependencies:**

    Make sure you have Python 3.7+ and pip installed. Then, install the required Python packages by running:

    ```bash
    pip install -r requirements.txt
    ```

2. **Run the Flask Application:**

    Start the Flask app with:

    ```bash
    python app.py
    ```

    The application will run locally on `http://localhost:8080`.

## Admin OTP Verification

Admin users must authenticate via OTP before accessing the records. This feature ensures that only authorized personnel can view or add notes to the user data. The OTP is verified using a time-based one-time password (TOTP) algorithm, which is configured with a secret key.

## Usage

- **Homepage:** The homepage allows users to submit their details through a form, including name, email, phone number, and preferred time to connect.
- **Admin Panel:** Admin users can access and update records after successful OTP verification.
- **Database:** The user data is stored securely in a SQLite database, with encrypted fields for sensitive information.

## Security Features

- **CSRF Protection:** Prevents cross-site request forgery attacks.
- **Encryption:** All sensitive data (e.g., name, email, phone) is encrypted using the Fernet encryption system.
- **CAPTCHA Validation:** Protects the forms from bot submissions.
- **Phone Number Validation:** Ensures the validity of the phone number entered by the user using the NumVerify API.
- **Rate Limiting:** Limits the number of requests to prevent abuse.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions to this project. Please fork the repository, make your changes, and submit a pull request. Be sure to follow the coding standards and provide tests where applicable.

## Acknowledgments

- Flask for building the web framework.
- Flask-WTF for form handling.
- Cryptography library for secure encryption and decryption.
- NumVerify for phone number validation.
- PyOTP for OTP generation and verification.
