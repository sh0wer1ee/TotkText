self.onmessage = async (event) => {
  const query = event.data.query.toLocaleLowerCase();
  const shards = event.data.shards;
  const limit = event.data.limit || 300;
  let count = 0;

  try {
    for (let i = 0; i < shards; i += 1) {
      const name = String(i).padStart(4, "0");
      const res = await fetch(`./data/search/search-${name}.json`);
      if (!res.ok) throw new Error(`${res.status} search-${name}.json`);
      const data = await res.json();
      const batch = [];

      for (const item of data) {
        if (count >= limit) break;
        if (item.text.toLocaleLowerCase().includes(query)) {
          batch.push(item);
          count += 1;
        }
      }

      self.postMessage({
        type: "progress",
        done: i + 1,
        total: shards,
        count,
        results: batch,
      });

      if (count >= limit) break;
    }

    self.postMessage({ type: "done", count });
  } catch (error) {
    self.postMessage({ type: "error", message: error.message });
  }
};
