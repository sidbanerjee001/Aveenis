import './App.css';
import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const PROJECT_URL = process.env.REACT_APP_PROJECT_URL;
const ANON_KEY = process.env.REACT_APP_ANON_KEY;

const supabase = createClient(PROJECT_URL, ANON_KEY);

function App() {

  const [posts, setPosts] = useState([]);
  
  useEffect(() => {
    getPosts();
  }, []);

  async function getPosts() {
    const { data } = await supabase.from("posts").select();
    setPosts(data);
  }

  return (
    <div className="App">
      <header className="App-header">
        <p>
          Welcome. To the Aveenis.
        </p>
        <ul>
        {posts.map((post) => (
          <li key={post.id}>{post.title}</li>
        ))}
      </ul>
      </header>
    </div>
  );
}

export default App;
