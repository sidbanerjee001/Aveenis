## FRONTEND

1. Enter "aveenis" within Frontend & install NPM packages (if you're using pnpm, replace `npm` with `pnpm` in all the commands below):

  ```bash
  npm i
  ```

2. You can now run the Next.js local development server:

  ```bash
  npm start
  ```

## BACKEND

1. Enter backend and install python packages. BEST TO CREATE VIRTUAL ENVIRONMENT FIRST!

  ```bash
  pip install -r requirements.txt
  ```

2. Run Flask app with debug mode (best for development) or build mode (best for deployment testing)

  ```bash
  flask --app app.py --debug run
  ```

OR

  ```bash
  flask --app app.py run
  ```
