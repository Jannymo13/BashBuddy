import React, { useState, useEffect } from "react";

interface UserData {
  users: string[];
}

function App() {
  const [data, setData] = useState<UserData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/users")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("Fetched data:", data);
        setData(data);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setError(err.message);
      });
  }, []); // Empty dependency array - only run once on mount

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data) {
    return <div>Loading...</div>;
  }

  return <div>{JSON.stringify(data)}</div>;
}

export default App;
