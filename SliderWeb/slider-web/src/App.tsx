import React, { useEffect, useState } from 'react';
import PageComponent from './PageComponent';
import './App.css';


function App() {

  const [pages, setPages] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL}/pages.json`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to fetch pages: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setPages(data))
      .catch((error) => console.error('Error fetching pages:', error));
  }, []);

  return (
    <div className="App">
      {[...pages].map((page, index) => (
        <PageComponent key={page.id} page={page} index={ index } pages={pages} />
      ))}
    </div>
  );
} 

export default App;
