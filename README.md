# thewhitehat.club

This is a [Flask](https://flask.palletsprojects.com/en/stable/) app to run [https://cpsecurity.club](https://cpsecurity.club)

----

## Running the App (Development)

1. Create a new virtualenv in the root of the git repository and activate it with :

```bash
python -m venv venv
source venv/bin/activate
```

3. Install the required pip packages with

```bash
pip3 install -r requirements.txt
```

4. Create the empty directory `static/css`

```bash
mkdir static/css
```
5. Add API_PASS to ENV

6. And finally, run the app with

```bash
flask run --debug
```

7. Visit [127.0.0.1:3000](127.0.0.1:3000) to view the site running locally.
