/* Local stand-in for the artifact runtime (window.claude): an in-memory `db` and a `user`.
   Seed it with window.__SSK_FIXTURE = {collection: [docs with id]} before the page script runs.
   window.__SSK_WRITES records every write for the tests. window.__SSK_READONLY makes canEdit() false. */
(function () {
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const store = {};
  const listeners = [];
  window.__SSK_WRITES = [];
  for (const [col, docs] of Object.entries(window.__SSK_FIXTURE || {})) for (const d of docs) store[col + "/" + d.id] = clone(d);
  const colOf = (path) => path.split("/")[0];
  const docSnap = (path) => ({ id: path.split("/").pop(), exists: path in store, data: () => (path in store ? clone(store[path]) : undefined), metadata: { fromCache: false, hasPendingWrites: false } });
  const colSnap = (col) => {
    const docs = Object.keys(store).filter((k) => k.startsWith(col + "/") && k.split("/").length === 2).sort().map(docSnap);
    return { docs, size: docs.length, empty: !docs.length, metadata: { fromCache: false, hasPendingWrites: false }, docChanges: () => [] };
  };
  const notify = (col) => listeners.filter((l) => l.col === col).forEach((l) => setTimeout(() => l.next(colSnap(col)), 0));
  function docRef(path) {
    return {
      id: path.split("/").pop(), path,
      get: async () => docSnap(path),
      set: async (data) => { store[path] = clone(data); window.__SSK_WRITES.push({ op: "set", path, data: clone(data) }); notify(colOf(path)); },
      update: async (data) => { if (!(path in store)) throw { code: "invalid_argument", message: "missing" }; Object.assign(store[path], clone(data)); window.__SSK_WRITES.push({ op: "update", path, data: clone(data) }); notify(colOf(path)); },
      delete: async () => { delete store[path]; window.__SSK_WRITES.push({ op: "delete", path }); notify(colOf(path)); },
      onSnapshot: (next) => { setTimeout(() => next(docSnap(path)), 0); return () => {}; },
    };
  }
  const db = {
    doc: (path) => docRef(path),
    collection: (col) => ({
      path: col,
      doc: (id) => docRef(col + "/" + (id || "auto" + Math.random().toString(36).slice(2, 8))),
      get: async () => colSnap(col),
      onSnapshot: (next) => { const l = { col, next }; listeners.push(l); setTimeout(() => next(colSnap(col)), 0); return () => listeners.splice(listeners.indexOf(l), 1); },
    }),
  };
  const user = { id: async () => "u-owner", me: async () => ({ id: "u-owner" }), canEdit: () => !window.__SSK_READONLY, isOwner: () => !window.__SSK_READONLY, can: () => !window.__SSK_READONLY };
  window.claude = { use: async (name) => ({ db, user }[name] || null) };
  window.__SSK_STORE = store;
})();
