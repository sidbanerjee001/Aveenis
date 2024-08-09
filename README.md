## FRONTEND

1. Enter `web-ui` & install NPM packages (if you're using pnpm, replace `npm` with `pnpm` in all the commands below):

  ```bash
  npm i
  ```

2. Create a `.env` file in the "aveenis" directory, i.e. the root folder. This is necessary to securely request data from the Supabase backend.

  ```bash
  REACT_APP_PROJECT_URL=<input url>
  REACT_APP_ANON_KEY=<your ANON key>
  ```

3. You can now run the Next.js local development server:

  ```bash
  npm run dev
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
