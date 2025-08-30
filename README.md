# C-PARP System

C-PARP (Community Pharmacy ARV Refill Program) is a web-based system to
manage facilities, pharmacies, and clients.\
This README explains how to run the system, database setup, and login
credentials. 

Note: This is just a sample and much appreciate feedbacks and inputs. 
As they say in my facorite tv's Arigato Gozaimasu

------------------------------------------------------------------------

## 1. Requirements

Make sure you have installed:

-   Python 3.10+
-   pip (Python package manager)
-   Virtual environment (recommended)

------------------------------------------------------------------------

## 2. Setup Instructions

1.  Open a terminal (or Command Prompt) in the `cparp` folder.

2.  Create a virtual environment (recommended):

    ``` bash
    python -m venv venv
    source venv/bin/activate   # For Linux/Mac
    venv\Scripts\activate    # For Windows
    ```

3.  Install dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

4.   Initialize the database (only once):

    ``` bash
    python init_db.py
    ```

    > If you run it again, you may need to delete the old `cparp.db`
    > file first to avoid duplicate entries.

5.   Start the server:

    ``` bash
    python app.py
    ```

6.   Open your browser and go to:

    <http://127.0.0.1:5000>

------------------------------------------------------------------------

## 3. Logins

There are three roles in the system: **Admin**, **Facility**, and
**Pharmacy**.

### Admin Login

-   Username: `admin`
-   Password: `admin123`

Admin can: - Manage facilities, pharmacies, and users - View all reports
and clients

### Facility Login (example)

-   Username: `akph`
-   Password: `password`

Facility users can: - View only their clients - See linked pharmacies

### Pharmacy Login (example)

-   Username: `pharm1`
-   Password: `password`

Pharmacy users can: - View only their own assigned clients - Manage
refills

> You can update usernames/passwords inside `init_db.py` if needed.

------------------------------------------------------------------------

## 4. Notes

-   **Database file:** `cparp.db` (SQLite).\
-   **First-time setup:** Always run `init_db.py` once before starting
    the app.\
-   **Reset database:** Delete `cparp.db` and re-run `init_db.py`.\
-   **Styling:** Static files (CSS, JS) are in the `static/` folder.

------------------------------------------------------------------------

## 5. Troubleshooting

-   If login fails → Check if you ran `init_db.py`.\
-   If you get duplicate errors → Delete `cparp.db` and reinitialize.\
-   If port 5000 is busy → Run with `python app.py --port 5001`.

------------------------------------------------------------------------

