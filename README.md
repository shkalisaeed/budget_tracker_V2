**Usage Instructions**

1. Open a terminal and cd into where you've saved the repository on your machine

2. Use the following command to automatically install all dependent libraries 

`pip install -r requirements.txt`

If the above doesn't work, Use

`python -m pip install -r requirements.txt`

3. Run `main.py` from your IDE or terminal. It should say something along the lines of "Serving Flask app 'main'" on the output.
It will also say "Running on (IP Address)" underneath which is your local host, click on it or copy it into your browser.

**Potential Issues**

1. If you've pip installed the libraries but they aren't registering (squiggly error lines under the import lines at the top of main.py), change your IDE's Python interpretor to the correct Python version which you've installed the libaries. This can happen if you have multiple versions of Python installed.

2. Sometimes the instance/budget_database.db gets nuked while testing so each time it gets pushed it might be different. Since it's a local db anyway it shouldn't be an issue, if you try to log in with old credentials that it no longer has just make a new account.




